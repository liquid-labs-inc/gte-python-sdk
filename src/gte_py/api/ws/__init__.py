"""WebSocket client for GTE."""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypedDict, cast

import aiohttp

logger = logging.getLogger(__name__)


class OrderBookLevel(TypedDict):
    """Order book level data structure."""
    px: str  # Price
    sz: str  # Size
    n: int   # Number of orders at this price level


class OrderBookData(TypedDict):
    """Order book data structure."""
    a: List[OrderBookLevel]  # Asks sorted from lowest to highest price
    b: List[OrderBookLevel]  # Bids sorted from highest to lowest price
    t: int                   # Timestamp in milliseconds
    m: str                   # Market address


class TradeData(TypedDict):
    """Trade data structure."""
    sd: str  # Side ('buy' or 'sell')
    m: str   # Market address
    px: str  # Price
    sz: str  # Size
    h: str   # Transaction hash
    id: int  # Trade ID
    t: int   # Timestamp in milliseconds


class CandleData(TypedDict):
    """Candle data structure."""
    m: str   # Market address
    t: int   # Timestamp in milliseconds
    i: str   # Interval
    o: str   # Open price
    h: str   # High price
    l: str   # Low price
    c: str   # Close price
    v: str   # Volume
    n: int   # Number of trades


class WebSocketMessage(TypedDict):
    """WebSocket message structure."""
    s: str   # Stream type
    d: Union[OrderBookData, TradeData, CandleData]  # Data


class ParsedOrderBookData(TypedDict):
    """Parsed order book data."""
    market: str
    timestamp: datetime
    asks: List[Dict[str, float]]
    bids: List[Dict[str, float]]


class ParsedTradeData(TypedDict):
    """Parsed trade data."""
    market: str
    side: str
    price: float
    size: float
    timestamp: datetime
    trade_id: int
    tx_hash: str


class ParsedCandleData(TypedDict):
    """Parsed candle data."""
    market: str
    interval: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int


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
        self.request_id = 0

    def _next_request_id(self) -> int:
        """Generate a new request ID."""
        self.request_id += 1
        return self.request_id

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
            
            # Parse data based on stream type
            parsed_data = self._parse_stream_data(data)
            
            if stream_type in self.callbacks:
                for callback in self.callbacks.get(stream_type, []):
                    try:
                        # Pass both raw and parsed data to callback
                        await callback(data, parsed_data)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
        elif "id" in data:  # Response to a subscription request
            logger.debug(f"Received response: {data}")
            if "error" in data:
                logger.error(f"WebSocket subscription error: {data['error']}")
                
    def _parse_stream_data(self, data: dict) -> dict:
        """Parse stream data based on its type.
        
        Args:
            data: Raw stream data
            
        Returns:
            Parsed data in a more usable format
        """
        stream_type = data["s"]
        stream_data = data["d"]
        
        if stream_type == "book":
            # Parse orderbook data
            return {
                "market": stream_data["m"],
                "timestamp": datetime.fromtimestamp(stream_data["t"] / 1000),
                "asks": [{"price": float(level["px"]), 
                         "size": float(level["sz"]), 
                         "count": level["n"]} 
                        for level in stream_data["a"]],
                "bids": [{"price": float(level["px"]), 
                         "size": float(level["sz"]), 
                         "count": level["n"]}
                        for level in stream_data["b"]]
            }
            
        elif stream_type == "trades":
            # Parse trade data
            return {
                "market": stream_data["m"],
                "side": stream_data["sd"],
                "price": float(stream_data["px"]),
                "size": float(stream_data["sz"]),
                "timestamp": datetime.fromtimestamp(stream_data["t"] / 1000),
                "trade_id": stream_data["id"],
                "tx_hash": stream_data["h"]
            }
            
        elif stream_type == "candle":
            # Parse candle data
            return {
                "market": stream_data["m"],
                "interval": stream_data["i"],
                "timestamp": datetime.fromtimestamp(stream_data["t"] / 1000),
                "open": float(stream_data["o"]),
                "high": float(stream_data["h"]),
                "low": float(stream_data["l"]),
                "close": float(stream_data["c"]),
                "volume": float(stream_data["v"]),
                "trade_count": stream_data["n"]
            }
            
        # For unknown stream types, return the raw data
        return stream_data

    async def subscribe(self, method: str, params: dict, callback: Callable[[dict, dict], Any]):
        """Subscribe to a topic.

        Args:
            method: Topic to subscribe to (e.g., "trades.subscribe")
            params: Parameters for the subscription
            callback: Function to call when a message is received with (raw_data, parsed_data)
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
        request_id = self._next_request_id()
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
    async def subscribe_trades(self, market: str, callback: Callable[[dict, dict], Any]):
        """Subscribe to trades for a market.

        Args:
            market: Market address
            callback: Function to call when a trade is received with (raw_data, parsed_data)
        """
        await self.subscribe("trades.subscribe", {"market": market}, callback)

    async def unsubscribe_trades(self, market: str):
        """Unsubscribe from trades for a market.

        Args:
            market: Market address
        """
        await self.unsubscribe("trades.unsubscribe", {"market": market})

    async def subscribe_candles(self, market: str, interval: str, callback: Callable[[dict, dict], Any]):
        """Subscribe to candles for a market.

        Args:
            market: Market address
            interval: Candle interval (1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
            callback: Function to call when a candle is received with (raw_data, parsed_data)
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
        self, market: str, limit: int = 10, callback: Callable[[dict, dict], Any] | None = None
    ):
        """Subscribe to orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels to include (defaults to 10)
            callback: Function to call when an orderbook update is received with (raw_data, parsed_data)
        """
        # Register with book stream type
        stream_type = "book"
        if callback is not None:
            if stream_type not in self.callbacks:
                self.callbacks[stream_type] = []
            self.callbacks[stream_type].append(callback)

        # Send subscription request using new format
        request_id = self._next_request_id()
        request = {
            "id": request_id,
            "method": "book.subscribe",
            "params": {"market": market, "limit": limit},
        }
        print(request)

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
