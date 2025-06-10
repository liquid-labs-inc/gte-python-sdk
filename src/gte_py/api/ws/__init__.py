"""WebSocket client for GTE."""

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Union, TypedDict, Tuple, cast

import aiohttp
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)


class OrderBookLevel(TypedDict):
    """Order book level data structure."""
    px: str  # Price
    sz: str  # Size
    n: int  # Number of orders at this price level


class OrderBookData(TypedDict):
    """Order book data structure."""
    a: List[OrderBookLevel]  # Asks sorted from lowest to highest price
    b: List[OrderBookLevel]  # Bids sorted from highest to lowest price
    t: int  # Timestamp in milliseconds
    m: str  # Market address


class TradeData(TypedDict):
    """Trade data structure."""
    sd: str  # Side ('buy' or 'sell')
    m: str  # Market address
    px: str  # Price
    sz: str  # Size
    h: str  # Transaction hash
    id: int  # Trade ID
    t: int  # Timestamp in milliseconds


class CandleData(TypedDict):
    """Candle data structure."""
    m: str  # Market address
    t: int  # Timestamp in milliseconds
    i: str  # Interval
    o: str  # Open price
    h: str  # High price
    l: str  # Low price
    c: str  # Close price
    v: str  # Volume
    n: int  # Number of trades


class WebSocketMessage(TypedDict):
    """WebSocket message structure."""
    s: str  # Stream type
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
        self.callbacks: Dict[Tuple[str, ChecksumAddress], Callable] = {}
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
        if self.ws is None:
            raise RuntimeError("WebSocket connection is not established")
    
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
            inner = data['d']
            market = to_checksum_address(inner['m'])

            if stream_type in self.callbacks:
                for callback in self.callbacks.get((stream_type, market), []):
                    try:
                        # Pass both raw and parsed data to callback
                        await callback(inner)
                    except Exception as e:
                        logger.error(f"Error in callback", exc_info=e)
        elif "id" in data:  # Response to a subscription request
            logger.debug(f"Received response: {data}")
            if "error" in data:
                logger.error(f"WebSocket subscription error: {data['error']}")

    async def subscribe(self, method: str, params: dict, market: ChecksumAddress, callback: Callable[[TypedDict], Any]):
        """Subscribe to a topic.

        Args:
            method: Topic to subscribe to (e.g., "trades.subscribe")
            params: Parameters for the subscription
            market: Market address to subscribe to
            callback: Function to call when a message is received with (raw_data)
        """
        if not self.running or not self.ws:
            await self.connect()
        
        self.ws = cast(aiohttp.client.ClientWebSocketResponse, self.ws)

        # Extract the stream type from the method
        stream_type = method.split(".")[0]

        self.callbacks[(stream_type, market)] = callback

        # Send subscription request
        request_id = self._next_request_id()
        request = {"id": request_id, "method": method, "params": params}
        await self.ws.send_json(request)
        logger.debug(f"Sent subscription request: {request}")

    async def unsubscribe(self, method: str, params: dict, market: ChecksumAddress):
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
        if (stream_type, market) in self.callbacks:
            self.callbacks.pop((stream_type, market))

        logger.debug(f"Sent unsubscription request: {request}")

    # WebSocket API methods
    async def subscribe_trades(self, market: ChecksumAddress, callback: Callable[[TradeData], Any]):
        """Subscribe to trades for a market.

        Args:
            market: Market address
            callback: Function to call when a trade is received with (raw_data)
        """
        await self.subscribe("trades.subscribe", {"market": market}, market, callback)

    async def unsubscribe_trades(self, market: ChecksumAddress):
        """Unsubscribe from trades for a market.

        Args:
            market: Market address
        """
        await self.unsubscribe("trades.unsubscribe", {"market": market}, market)

    async def subscribe_candles(self, market: ChecksumAddress, interval: str, callback: Callable[[CandleData], Any]):
        """Subscribe to candles for a market.

        Args:
            market: Market address
            interval: Candle interval (1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
            callback: Function to call when a candle is received with (raw_data)
        """
        await self.subscribe(
            "candles.subscribe", {"market": market, "interval": interval}, market, callback
        )

    async def unsubscribe_candles(self, market: str, interval: str):
        """Unsubscribe from candles for a market.

        Args:
            market: Market address
            interval: Candle interval
        """
        await self.unsubscribe("candles.unsubscribe", {"market": market, "interval": interval}, market)

    async def subscribe_orderbook(
            self, market: ChecksumAddress, limit: int = 10, callback: Callable[[OrderBookData], Any] | None = None
    ):
        """Subscribe to orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels to include (defaults to 10)
            callback: Function to call when an orderbook update is received with (raw_data)
        """
        await self.subscribe('book.subscribe', {"market": market, "limit": limit}, market, callback)

    async def unsubscribe_orderbook(self, market: ChecksumAddress, limit: int = 10):
        """Unsubscribe from orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels that was used for subscription
        """
        await self.unsubscribe('book.unsubscribe', {"market": market, "limit": limit}, market)
