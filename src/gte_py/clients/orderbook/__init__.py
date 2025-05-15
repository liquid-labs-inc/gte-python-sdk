"""Real-time market data client."""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any, Tuple, List

from eth_typing import ChecksumAddress

from gte_py.api.rest import RestApi
from gte_py.api.ws import WebSocketApi
from gte_py.clients.info import InfoClient
from gte_py.clients.clob import CLOBClient
from gte_py.configs import NetworkConfig
from gte_py.models import Candle, OrderbookUpdate, PriceLevel, OrderBookSnapshot, Market, Side, Order

logger = logging.getLogger(__name__)


class OrderbookClient:
    """WebSocket-based client for real-time market data."""

    def __init__(self, config: NetworkConfig, rest: RestApi, info: InfoClient, clob: CLOBClient):
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
        self._clob = clob

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
            callback: Callable[[OrderbookUpdate], Any] | None = None,
            limit: int = 10,
    ):
        """Subscribe to real-time orderbook updates.

        Args:
            callback: Function to call when an orderbook update is received
            limit: Depth limit for the orderbook
        """
        if callback:
            self._orderbook_callbacks.append(callback)

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

    async def unsubscribe_orderbook(self, market: Market, limit: int = 10):
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

    async def get_order_book_snapshot(self, market: Market, depth: int = 5) -> OrderBookSnapshot:
        """
        Get a snapshot of the current order book from the API.

        Args:
            depth: Number of price levels to include on each side

        Returns:
            OrderBookSnapshot containing bids and asks with prices and sizes
        """
        async with self._rest as client:
            return await client.get_order_book_snapshot(market.address, limit=depth)

    async def get_tob(self, market: Market) -> Tuple[int, int]:
        """
        Get the best bid and offer (BBO) for a market.

        Args:
            market: Market object

        Returns:
            OrderBookSnapshot containing the best bid and offer
        """
        clob = self._clob.get_clob(market.address)
        bbo = await clob.get_tob()
        return bbo

    async def get_open_orders(
            self, market: Market, level: int | None = None
    ) -> List[Order]:
        """
        Get all orders for a specific market and address from the chain directly.
        This is a fallback method when the REST API is not available.

        Args:
            market: Market to get orders from
            address: Address to filter orders by (None for all)

        Returns:
            List of Order objects
            :param level:
        """
        clob = self._clob.get_clob(market.address)
        best_bid, best_ask = await clob.get_tob()
        orders = []
        # Get all orders for the bid and ask price levels
        price_level = best_bid
        tasks = []
        i = 0
        while price_level > 0:
            tasks.append(
                asyncio.create_task(
                    self.get_orders_for_price_level(
                        market=market, price=price_level, side=Side.BUY
                    )
                )
            )
            i += 1
            if level and i >= level:
                break
            price_level = await clob.get_next_smallest_price(price_level, Side.BUY)
        i = 0
        price_level = best_ask
        while price_level > 0:
            tasks.append(
                asyncio.create_task(
                    self.get_orders_for_price_level(
                        market=market, price=price_level, side=Side.SELL
                    )
                )
            )
            i += 1
            if level and i >= level:
                break
            price_level = await clob.get_next_biggest_price(price_level, Side.SELL)

        for task in tasks:
            try:
                pl_orders = await task
                for order in pl_orders:
                    orders.append(order)
            except Exception as e:
                logger.error(f"Error getting orders: {e}")
        return orders

    async def get_orders_for_price_level(
            self, market: Market, price: int, side: Side
    ) -> List[Order]:
        """
        Get all orders for a specific price level.

        Args:
            market: Market to get orders from
            price: Price level to filter orders by
            side: Side of the order (BUY or SELL)

        Returns:
            List of Order objects
        """
        clob = self._clob.get_clob(market.address)
        orders = []
        (num, head, tail) = await clob.get_limit(price, side)
        logger.debug(f"get_orders_for_price_level price={price} side={side} num={num}, head={head}, tail={tail}")
        order_id = head
        for i in range(num):
            order = await clob.get_order(order_id)
            orders.append(Order.from_clob_order(order, market))
            order_id = order.nextOrderId
        return orders

    async def get_order(self, market: Market, order_id: int) -> Order:
        clob = self._clob.get_clob(market.address)
        order = await clob.get_order(order_id)
        return Order.from_clob_order(order, market)
