"""WebSocket client for GTE."""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class WebSocketApi:
    """WebSocket client for GTE."""

    def __init__(self, ws_url: str = "wss://ws.gte.io/v1"):
        """Initialize the client.

        Args:
            ws_url: WebSocket URL
        """
        self.ws_url = ws_url
        self.ws: aiohttp.client.ClientWebSocketResponse | None = None
        self.callbacks = {}
        self.running = False
        self.task = None

    async def connect(self):
        """Connect to the WebSocket."""
        session = aiohttp.ClientSession()
        self.ws = await session.ws_connect(self.ws_url)
        self.running = True
        self.task = asyncio.create_task(self._listen())
        logger.info("Connected to GTE WebSocket")

    async def close(self):
        """Close the WebSocket connection."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("Disconnected from GTE WebSocket")

    async def _listen(self):
        """Listen for messages from the WebSocket."""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self._handle_message(data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg.data}")
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.running = False

    async def _handle_message(self, data: dict):
        """Handle a message from the WebSocket.

        Args:
            data: Message data
        """
        if "s" in data:  # Stream data
            stream_type = data["s"]
            if stream_type in self.callbacks:
                for callback in self.callbacks.get(stream_type, []):
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
        elif "id" in data:  # Response to a subscription request
            logger.debug(f"Received response: {data}")

    async def subscribe(self, method: str, params: dict, callback: Callable[[dict], Any]):
        """Subscribe to a topic.

        Args:
            method: Topic to subscribe to (e.g., "trades.subscribe")
            params: Parameters for the subscription
            callback: Function to call when a message is received
        """
        if not self.running or not self.ws:
            await self.connect()

        # Extract the stream type from the method
        stream_type = method.split(".")[0]

        # Register callback
        if stream_type not in self.callbacks:
            self.callbacks[stream_type] = []
        self.callbacks[stream_type].append(callback)

        # Send subscription request
        request_id = str(uuid.uuid4())
        request = {"id": request_id, "method": method, "params": params}
        await self.ws.send_json(request)
        logger.debug(f"Sent subscription request: {request}")

    async def unsubscribe(self, method: str, params: dict):
        """Unsubscribe from a topic.

        Args:
            method: Topic to unsubscribe from (e.g., "trades.unsubscribe")
            params: Parameters for the unsubscription
        """
        if not self.running or not self.ws:
            return

        # Send unsubscription request
        request = {"method": method, "params": params}
        await self.ws.send_json(request)

        # Clean up callbacks for this stream type
        stream_type = method.split(".")[0]
        if stream_type in self.callbacks:
            del self.callbacks[stream_type]

        logger.debug(f"Sent unsubscription request: {request}")

    # WebSocket API methods
    async def subscribe_trades(self, markets: list[str], callback: Callable[[dict], Any]):
        """Subscribe to trades for specified markets.

        Args:
            markets: List of market addresses
            callback: Function to call when a trade is received
        """
        await self.subscribe("trades.subscribe", {"markets": markets}, callback)

    async def unsubscribe_trades(self, markets: list[str]):
        """Unsubscribe from trades for specified markets.

        Args:
            markets: List of market addresses
        """
        await self.unsubscribe("trades.unsubscribe", {"markets": markets})

    async def subscribe_candles(self, market: str, interval: str, callback: Callable[[dict], Any]):
        """Subscribe to candles for a market.

        Args:
            market: Market address
            interval: Candle interval (1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
            callback: Function to call when a candle is received
        """
        await self.subscribe(
            "candles.subscribe", {"market": market, "interval": interval}, callback
        )

    async def unsubscribe_candles(self, market: str, interval: str):
        """Unsubscribe from candles for a market.

        Args:
            market: Market address
            interval: Candle interval
        """
        await self.unsubscribe("candles.unsubscribe", {"market": market, "interval": interval})

    async def subscribe_orderbook(
        self, market: str, limit: int = 10, callback: Callable[[dict], Any] | None = None
    ):
        """Subscribe to orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels to include (defaults to 10)
            callback: Function to call when an orderbook update is received
        """
        # Register with book stream type
        stream_type = "book"
        if callback is not None:
            if stream_type not in self.callbacks:
                self.callbacks[stream_type] = []
            self.callbacks[stream_type].append(callback)

        # Send subscription request using new format
        request_id = str(uuid.uuid4())
        request = {
            "id": request_id,
            "method": "book.subscribe",
            "params": {"market": market, "limit": limit},
        }

        if self.ws:
            await self.ws.send_json(request)
            logger.debug(f"Sent orderbook subscription request: {request}")
        else:
            logger.error("WebSocket not connected")

    async def unsubscribe_orderbook(self, market: str, limit: int = 10):
        """Unsubscribe from orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels that was used for subscription
        """
        # Send unsubscription request using new format
        request = {"method": "book.unsubscribe", "params": {"market": market, "limit": limit}}

        if self.ws:
            await self.ws.send_json(request)

            # Clean up callbacks for this stream type
            if "book" in self.callbacks:
                del self.callbacks["book"]

            logger.debug(f"Sent orderbook unsubscription request: {request}")
        else:
            logger.error("WebSocket not connected")
