"""Real-time market data client."""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from eth_typing import ChecksumAddress

from gte_py.api.rest import RestApi
from gte_py.api.ws import WebSocketApi
from gte_py.clients import InfoClient
from gte_py.configs import NetworkConfig
from gte_py.models import Candle, OrderbookUpdate, PriceLevel, Trade, OrderBookSnapshot, Market

logger = logging.getLogger(__name__)


class OrderbookClient:
    """WebSocket-based client for real-time market data."""

    def __init__(self, config: NetworkConfig, info: InfoClient):
        """Initialize the client.

        Args:
            config: Network configuration
            info: InfoClient instance for market information
        """
        self._ws_client = WebSocketApi(ws_url=config.ws_url)
        self._rest_client = RestApi(base_url=config.api_url)
        self._info_client = info
        self._trade_callbacks = []
        self._candle_callbacks = {}  # Keyed by interval
        self._orderbook_callbacks = []
        self._last_trade = None
        self._last_candle = {}  # Keyed by interval
        self._orderbook_state: dict[ChecksumAddress, OrderbookUpdate] = {}

    async def connect(self):
        """Connect to the WebSocket."""
        await self._ws_client.connect()
        # TODO: handle subscriptions

    async def close(self):
        """Close the WebSocket connection."""
        await self._ws_client.close()

    # Trade methods
    async def subscribe_trades(self, market: Market, callback: Callable[[Trade], Any] | None = None):
        """Subscribe to real-time trades.

        Args:
            callback: Function to call when a trade is received
        """
        if callback:
            self._trade_callbacks.append(callback)

        if not self._trade_callbacks:
            # If no callbacks, add a dummy one to store the last trade
            self._trade_callbacks.append(lambda trade: setattr(self, "_last_trade", trade))

        # Define handler for raw trade messages
        async def handle_trade_message(data):
            if data.get("s") != "trades":
                return

            trade_data = data.get("d", {})
            trade = Trade(
                market_address=trade_data.get("m"),
                side=trade_data.get("sd"),
                price=float(trade_data.get("px")),
                size=float(trade_data.get("sz")),
                timestamp=trade_data.get("t"),
                tx_hash=trade_data.get("h"),
                trade_id=trade_data.get("id"),
            )

            self._last_trade = trade

            for cb in self._trade_callbacks:
                try:
                    await cb(trade) if asyncio.iscoroutinefunction(cb) else cb(trade)
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")

        await self._ws_client.subscribe_trades([market.address], handle_trade_message)

    async def unsubscribe_trades(self, market: Market):
        """Unsubscribe from real-time trades."""
        await self._ws_client.unsubscribe_trades([market.address])
        self._trade_callbacks = []

    @property
    def last_trade(self) -> Trade | None:
        """Get the most recent trade."""
        return self._last_trade

    def get_last_candle(self, interval: str = "1m") -> Candle | None:
        """Get the most recent candle for the specified interval."""
        return self._last_candle.get(interval)

    # Orderbook methods
    async def subscribe_orderbook(
            self,
            market: Market,
            callback: Callable[[OrderbookUpdate], Any] | None = None, limit: int = 10
    ):
        """Subscribe to real-time orderbook updates.

        Args:
            callback: Function to call when an orderbook update is received
            limit: Depth limit for the orderbook
        """
        if callback:
            self._orderbook_callbacks.append(callback)

        if not self._orderbook_callbacks:
            # If no callbacks, add a dummy one to update the orderbook state
            self._orderbook_callbacks.append(
                lambda update: setattr(self, "_orderbook_state", update)
            )

        # Define handler for raw orderbook messages
        async def handle_orderbook_message(data):
            if data.get("s") != "book":
                return

            ob_data = data.get("d", {})

            # Convert bid and ask arrays to PriceLevel objects
            bids = [
                PriceLevel(
                    price=bid.get("px", 0),
                    size=bid.get("sz", 0),
                    count=bid.get("n", 0),
                )
                for bid in ob_data.get("b", [])
            ]

            asks = [
                PriceLevel(
                    price=ask.get("px", 0),
                    size=ask.get("sz", 0),
                    count=ask.get("n", 0),
                )
                for ask in ob_data.get("a", [])
            ]

            update = OrderbookUpdate(
                market_address=ob_data.get("m", market.address),
                timestamp=ob_data.get("t", int(time.time() * 1000)),
                bids=bids,
                asks=asks,
            )

            self._orderbook_state = update

            for cb in self._orderbook_callbacks:
                try:
                    await cb(update) if asyncio.iscoroutinefunction(cb) else cb(update)
                except Exception as e:
                    logger.error(f"Error in orderbook callback: {e}")

        # Subscribe to orderbook using the updated API
        await self._ws_client.subscribe_orderbook(
            market=market.address, limit=limit, callback=handle_orderbook_message
        )

    async def unsubscribe_orderbook(self,
                                    market: Market,
                                    limit: int = 10):
        """Unsubscribe from real-time orderbook updates.

        Args:
            limit: Depth limit that was used for subscription
        """
        await self._ws_client.unsubscribe_orderbook(market=market.address, limit=limit)
        self._orderbook_callbacks = []
        self._orderbook_state = None

    def orderbook(self, market: Market) -> OrderbookUpdate | None:
        """Get the current orderbook state."""
        return self._orderbook_state[market.address]

    async def get_order_book_snapshot(self,
                                      market: Market,
                                      depth: int = 5) -> OrderBookSnapshot:
        """
        Get a snapshot of the current order book from the API.

        Args:
            depth: Number of price levels to include on each side

        Returns:
            OrderBookSnapshot containing bids and asks with prices and sizes
        """
        async with self._rest_client as client:
            return await client.get_order_book_snapshot(market.address, limit=depth)
