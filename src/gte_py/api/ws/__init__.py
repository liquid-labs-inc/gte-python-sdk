import asyncio
import json
import logging
import random
from collections.abc import Callable, Awaitable
from typing import Any
from enum import Enum

import aiohttp
from eth_utils.address import to_checksum_address

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class WebSocketApi:
    def __init__(
        self,
        ws_url: str = "wss://dev-api.gte.xyz/ws",
        heartbeat_interval: float = 30.0,
        reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
        enable_logging: bool = True
    ):
        self.ws_url = ws_url
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.enable_logging = enable_logging

        self.state = ConnectionState.DISCONNECTED
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self.session: aiohttp.ClientSession | None = None

        # Map subscription_id -> callback
        self.callbacks: dict[int, Callable[[dict[str, Any]], Any] | Callable[[dict[str, Any]], Awaitable[Any]]] = {}
        # Map (topic, market) -> subscription_id for tracking
        self.subscriptions: dict[tuple[str, str], int] = {}

        self.listen_task: asyncio.Task[Any] | None = None
        self.reconnect_task: asyncio.Task[Any] | None = None

        self.request_id = 0
        self.reconnect_count = 0
        self._shutting_down = False

    async def connect(self):
        if self.state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            return
        await self._connect_internal()

    async def _connect_internal(self):
        try:
            if self.ws:
                await self.ws.close()
                self.ws = None
            if self.session and not self.session.closed:
                await self.session.close()

            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
            self.ws = await self.session.ws_connect(self.ws_url, heartbeat=self.heartbeat_interval)

            self.state = ConnectionState.CONNECTED
            self.reconnect_count = 0

            self.listen_task = asyncio.create_task(self._listen())
            if self.enable_logging:
                logger.info(f"Connected to GTE WebSocket at {self.ws_url}")
        except Exception as e:
            self.state = ConnectionState.DISCONNECTED
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise


    async def disconnect(self):
        self._shutting_down = True
        self.state = ConnectionState.DISCONNECTED

        for task in [self.listen_task, self.reconnect_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.listen_task = None
        self.reconnect_task = None

        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            self.ws = None

        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            self.session = None

        if self.enable_logging:
            logger.info("Disconnected from GTE WebSocket")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def _listen(self):
        if not self.ws:
            raise RuntimeError("WebSocket connection is not established")

        try:
            async for msg in self.ws:
                if self.state != ConnectionState.CONNECTED or self._shutting_down:
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message: {msg.data[:200]}...")
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    logger.warning("Received binary message (not supported)")
                elif msg.type == aiohttp.WSMsgType.PONG:
                    if self.enable_logging:
                        logger.debug("Received pong")
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                    break
        except asyncio.CancelledError:
            logger.debug("Listen task cancelled")
        except Exception as e:
            logger.error(f"WebSocket listen error: {e}")
        finally:
            if not self._shutting_down:
                await self._handle_disconnection()

    async def _handle_disconnection(self):
        if self.reconnect_task and not self.reconnect_task.done():
            return

        self.state = ConnectionState.DISCONNECTED
        if self.reconnect_count < self.reconnect_attempts:
            self.state = ConnectionState.RECONNECTING
            self.reconnect_task = asyncio.create_task(self._reconnect())
        else:
            self.listen_task = None
            logger.error(f"Max reconnection attempts ({self.reconnect_attempts}) reached")

    async def _reconnect(self):
        self.state = ConnectionState.RECONNECTING

        while self.reconnect_count < self.reconnect_attempts:
            self.reconnect_count += 1
            base_delay = self.reconnect_delay * (2 ** (self.reconnect_count - 1))
            delay = min(base_delay * random.uniform(0.8, 1.2), self.max_reconnect_delay)

            logger.info(f"Reconnecting in {delay:.1f}s (attempt {self.reconnect_count}/{self.reconnect_attempts})")
            await asyncio.sleep(delay)

            try:
                await self._connect_internal()
                logger.info("Reconnection successful")
                return
            except Exception as e:
                logger.error(f"Reconnection attempt {self.reconnect_count} failed: {e}")

        self.state = ConnectionState.DISCONNECTED
        self.listen_task = None
        logger.error("Failed to reconnect after all attempts")

    async def _handle_message(self, data: dict[str, Any]):
        # Handle subscription acknowledgment (just {"id": int64})
        if "id" in data and "d" not in data:
            if self.enable_logging:
                logger.debug(f"Subscription acknowledged: {data}")
            return
        
        # Handle data messages {"id": int64, "d": {...}}
        if "id" in data and "d" in data:
            subscription_id = data["id"]
            payload = data["d"]
            
            callback = self.callbacks.get(subscription_id)  
            if not callback:
                if self.enable_logging:
                    logger.warning(f"No callback for subscription ID {subscription_id}")
                return

            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(payload)
                else:
                    callback(payload)
            except Exception:
                logger.error(f"Error in callback for subscription {subscription_id}", exc_info=True)
        else:
            if self.enable_logging:
                logger.warning(f"Unknown message format: {data}")

    async def subscribe(self, topic: str, params: dict[str, Any], callback: Callable[[dict[str, Any]], Any] | Callable[[dict[str, Any]], Awaitable[Any]]):
        try:
            market = params["marketId"]
        except KeyError:
            raise ValueError("params must include 'marketId' key")
        except ValueError as e:
            raise ValueError(f"Invalid market address: {e}")

        if not self.ws or self.ws.closed:
            await self.connect()

        subscription_id = self._next_request_id()
        self.callbacks[subscription_id] = callback
        self.subscriptions[(topic, market)] = subscription_id
        
        request = {"id": subscription_id, "method": "subscribe", "topic": topic, "params": params}

        try:
            if self.ws is None:
                raise RuntimeError("WebSocket connection is not established")
            await self.ws.send_json(request)
            if self.enable_logging:
                logger.debug(f"Subscribed to {topic} for market {market} with ID {subscription_id}")
        except Exception:
            self.callbacks.pop(subscription_id, None)
            self.subscriptions.pop((topic, market), None)
            raise

    async def unsubscribe(self, topic: str, params: dict[str, Any]):
        if self.state != ConnectionState.CONNECTED:
            return

        try:
            market = params["marketId"]
        except KeyError:
            raise ValueError("params must include 'marketId' key")
        except ValueError as e:
            raise ValueError(f"Invalid market address: {e}")

        # Get the subscription ID
        subscription_id = self.subscriptions.get((topic, market))
        if subscription_id is None:
            logger.warning(f"No active subscription for {topic} and market {market}")
            return

        request = {"id": subscription_id, "method": "unsubscribe", "topic": topic, "params": params}

        try:
            if self.ws is None:
                logger.warning("WebSocket connection is not established")
                return
            await self.ws.send_json(request)
        except Exception as e:
            logger.warning(f"Failed to send unsubscribe request: {e}")

        self.callbacks.pop(subscription_id, None)
        self.subscriptions.pop((topic, market), None)

        if self.enable_logging:
            logger.debug(f"Unsubscribed from {topic} for market {market}")

    def _next_request_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def get_subscriptions(self) -> list[dict[str, Any]]:
        return [
            {"topic": topic, "market": market, "subscription_id": sub_id}
            for (topic, market), sub_id in self.subscriptions.items()
        ]

    def is_connected(self) -> bool:
        return self.state == ConnectionState.CONNECTED and self.ws is not None and not self.ws.closed

    def get_connection_state(self) -> ConnectionState:
        return self.state
