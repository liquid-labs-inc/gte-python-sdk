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
from gte_py.models import Candle, OrderbookUpdate, PriceLevel, OrderBookSnapshot, Market

logger = logging.getLogger(__name__)


class OrderbookClient:
    """WebSocket-based client for real-time market data."""

    def __init__(self, config: NetworkConfig,
                 rest: RestApi,
                 info: InfoClient):
        """Initialize the client.

        Args:
            config: Network configuration
            info: InfoClient instance for market information
        """
        self._ws_client = WebSocketApi(ws_url=config.ws_url)
        self._rest = rest
        self._info_client = info
        self._trade_callbacks = []
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

            self._orderbook_state[market.address] = update

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
        async with self._rest as client:
            return await client.get_order_book_snapshot(market.address, limit=depth)
