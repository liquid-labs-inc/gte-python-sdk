"""Order execution functionality for the GTE client."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from eth_typing import AnyAddress, ChecksumAddress
from web3 import Web3
from web3.exceptions import LogTopicError
from web3.providers import WebSocketProvider
from web3.types import EventData

from .contracts.iclob import ICLOB
from .contracts.router import Router
from .contracts.structs import Side
from .contracts.utils import get_current_timestamp
from .info import MarketService
from .models import Market, Order, OrderStatus, Trade

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manages event subscriptions for streaming data."""

    def __init__(self, web3: Web3):
        """
        Initialize the subscription manager.

        Args:
            web3: Web3 instance with WebsocketProvider
        """
        self._web3 = web3
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

        # Check if websocket provider
        if not isinstance(web3.provider, WebSocketProvider):
            logger.warning(
                "Web3 provider is not a WebsocketProvider. Streaming functionality will be limited."
            )

    async def subscribe(
        self,
        subscription_id: str,
        contract: ICLOB,
        event_name: str,
        callback: Callable[[EventData], None],
        argument_filters: dict[str, Any] = None,
        polling_interval: float = 2.0,
    ) -> str:
        """
        Subscribe to contract events.

        Args:
            subscription_id: Unique identifier for this subscription
            contract: Contract to subscribe to
            event_name: Name of the event to subscribe to
            callback: Function to call with each event
            argument_filters: Filters to apply to events
            polling_interval: Polling interval for non-websocket providers

        Returns:
            Subscription ID
        """
        if subscription_id in self._subscriptions:
            # Unsubscribe existing subscription with this ID
            await self.unsubscribe(subscription_id)

        self._subscriptions[subscription_id] = {
            "contract": contract,
            "event_name": event_name,
            "callback": callback,
            "argument_filters": argument_filters or {},
            "polling_interval": polling_interval,
            "last_block": self._web3.eth.block_number,
        }

        # Start event listener
        if isinstance(self._web3.provider, WebSocketProvider):
            task = asyncio.create_task(self._ws_listen_for_events(subscription_id))
        else:
            task = asyncio.create_task(self._poll_for_events(subscription_id))

        self._running_tasks[subscription_id] = task
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from events.

        Args:
            subscription_id: ID of the subscription to cancel
        """
        if subscription_id in self._running_tasks:
            task = self._running_tasks[subscription_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._running_tasks[subscription_id]

        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]

    async def _ws_listen_for_events(self, subscription_id: str) -> None:
        """
        Listen for events using websocket subscription.

        Args:
            subscription_id: ID of the subscription
        """
        if subscription_id not in self._subscriptions:
            return

        sub_info = self._subscriptions[subscription_id]
        contract = sub_info["contract"]
        event_name = sub_info["event_name"]
        callback = sub_info["callback"]
        filters = sub_info["argument_filters"]

        event = getattr(contract.contract.events, event_name)
        event_filter = None
        try:
            event_filter = await event.create_filter(fromBlock="latest", argument_filters=filters)

            while True:
                try:
                    for event in event_filter.get_new_entries():
                        asyncio.create_task(callback(event))
                except LogTopicError as e:
                    logger.error(f"Error processing events: {e}")

                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            # Clean up the filter when cancelled
            await event_filter.uninstall()
            raise

    async def _poll_for_events(self, subscription_id: str) -> None:
        """
        Poll for events using eth_getLogs for non-websocket providers.

        Args:
            subscription_id: ID of the subscription
        """
        if subscription_id not in self._subscriptions:
            return

        sub_info = self._subscriptions[subscription_id]
        contract = sub_info["contract"]
        event_name = sub_info["event_name"]
        callback = sub_info["callback"]
        filters = sub_info["argument_filters"]
        interval = sub_info["polling_interval"]

        event = getattr(contract.contract.events, event_name)

        try:
            while True:
                current_block = self._web3.eth.block_number
                from_block = sub_info["last_block"] + 1

                if current_block >= from_block:
                    events = event.get_logs(
                        fromBlock=from_block, toBlock=current_block, argument_filters=filters
                    )

                    for event_data in events:
                        asyncio.create_task(callback(event_data))

                    # Update last processed block
                    sub_info["last_block"] = current_block

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise


class ExecutionClient:
    """Client for executing orders on the GTE exchange."""

    # Event signature constants
    EVENT_ORDER_POSTED = "OrderPosted"
    EVENT_ORDER_FILLED = "OrderFilled"
    EVENT_ORDER_CANCELLED = "OrderCancelled"
    EVENT_ORDER_AMENDED = "OrderAmended"

    def __init__(self, web3: Web3, sender_address: AnyAddress, router_address: str | None = None):
        """
        Initialize the execution client.

        Args:
            web3: Web3 instance for on-chain interactions
            router_address: Address of the GTE Router contract
            sender_address: Address to send transactions from
        """
        self._web3 = web3
        self._clob_clients: dict[str, ICLOB] = {}
        self._router: Router | None = None
        self._market_info: MarketService | None = None
        self._sender_address: ChecksumAddress = self._web3.to_checksum_address(sender_address)
        self._subscription_manager: SubscriptionManager | None = None

        if web3 and router_address:
            self.setup_contracts(web3, router_address)

    def setup_contracts(self, web3: Web3, router_address: str) -> None:
        """
        Set up the contracts.

        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        router_address = web3.to_checksum_address(router_address)

        # Create router and market info service
        self._router = Router(web3=web3, contract_address=router_address)
        self._market_info = MarketService(web3=web3, router_address=router_address)

    def _get_clob(self, contract_address: str) -> ICLOB:
        """
        Get or create an ICLOB contract instance.

        Args:
            contract_address: CLOB contract address

        Returns:
            ICLOB contract instance

        Raises:
            ValueError: If Web3 is not configured
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot interact with contracts.")

        contract_address = self._web3.to_checksum_address(contract_address)

        if contract_address not in self._clob_clients:
            self._clob_clients[contract_address] = ICLOB(
                web3=self._web3, contract_address=contract_address
            )
        return self._clob_clients[contract_address]

    async def stream_user_orders(
        self,
        user_address: str,
        market_address: str | None = None,
        callback: Callable[[Order, str], None] | None = None,
    ) -> str:
        """
        Stream order updates for a specific user.

        Args:
            user_address: Address of the user
            market_address: Optional market address to filter by
            callback: Function to call with each order update and event type

        Returns:
            Subscription ID that can be used to unsubscribe
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot stream blockchain events.")

        if not self._subscription_manager:
            raise ValueError("Subscription manager not initialized.")

        user_address = self._web3.to_checksum_address(user_address)
        subscription_id = f"user_orders_{user_address}_{market_address or 'all'}"

        # Keep track of orders to update them as events come in
        orders_by_id: dict[int, Order] = {}

        # Get market CLOB contract
        clob = None
        if market_address:
            clob = self._get_clob(market_address)
            contracts_to_subscribe = [clob]
        else:
            # If we don't have a market address, we need to get all markets
            # For now, use existing CLOB clients, but in a real implementation
            # we would need to discover all markets
            contracts_to_subscribe = list(self._clob_clients.values())
            if not contracts_to_subscribe:
                raise ValueError(
                    "No CLOB contracts available. Subscribe to specific markets first."
                )

        async def handle_post_event(event: EventData) -> None:
            if event.args.get("account") != user_address:
                return

            contract_address = event.address
            order = self._convert_post_event_to_order(event, contract_address)
            orders_by_id[order.id] = order
            callback(order, "posted")

        async def handle_fill_event(event: EventData) -> None:
            args = event['args']
            if args.get("maker") != user_address and args.get("taker") != user_address:
                return

            contract_address = event['address']
            order_id = args.get("orderId")

            # If this is a maker order and we have it cached
            if args.get("maker") == user_address and order_id in orders_by_id:
                order = orders_by_id[order_id]
                self._update_order_from_fill_event(order, event)
                callback(order, "filled")
            else:
                # We don't have the order, try to fetch it
                try:
                    # Find the contract that emitted this event
                    contract = None
                    for c in contracts_to_subscribe:
                        if c.address.lower() == contract_address.lower():
                            contract = c
                            break

                    if contract:
                        order_data = contract.get_order(order_id)
                        order = self._convert_contract_order_to_model(order_data, contract_address)
                        orders_by_id[order_id] = order
                        self._update_order_from_fill_event(order, event)
                        callback(order, "filled")
                except Exception as e:
                    logger.warning(f"Failed to fetch order {order_id}: {e}")

        async def handle_cancel_event(event: EventData) -> None:
            args = event['args']
            if args.get("account") != user_address:
                return

            order_id = args.get("orderId")
            if order_id in orders_by_id:
                order = orders_by_id[order_id]
                order.status = OrderStatus.CANCELLED
                callback(order, "cancelled")

        async def handle_amend_event(event: EventData) -> None:
            args = event['args']
            if args.get("account") != user_address:
                return

            order_id = args.get("orderId")
            if order_id in orders_by_id:
                order = orders_by_id[order_id]
                self._update_order_from_amend_event(order, event)
                callback(order, "amended")

        # Start with existing orders
        existing_orders = await self.get_user_orders_from_events(
            user_address=user_address,
            market_address=market_address,
            from_block=self._web3.eth.block_number - 10000,  # Last ~10000 blocks
            to_block="latest",
        )

        # Initialize the cache with existing orders
        for order in existing_orders:
            orders_by_id[int(order.id)] = order
            callback(order, "initial")

        # Set up subscriptions for each event type
        tasks = []
        for contract in contracts_to_subscribe:
            # Subscribe to post events
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_post_{contract.address}",
                    contract,
                    self.EVENT_ORDER_POSTED,
                    handle_post_event,
                    {"account": user_address},
                )
            )

            # Subscribe to fill events (as maker)
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_fill_maker_{contract.address}",
                    contract,
                    self.EVENT_ORDER_FILLED,
                    handle_fill_event,
                    {"maker": user_address},
                )
            )

            # Subscribe to fill events (as taker)
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_fill_taker_{contract.address}",
                    contract,
                    self.EVENT_ORDER_FILLED,
                    handle_fill_event,
                    {"taker": user_address},
                )
            )

            # Subscribe to cancel events
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_cancel_{contract.address}",
                    contract,
                    self.EVENT_ORDER_CANCELLED,
                    handle_cancel_event,
                    {"account": user_address},
                )
            )

            # Subscribe to amend events
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_amend_{contract.address}",
                    contract,
                    self.EVENT_ORDER_AMENDED,
                    handle_amend_event,
                    {"account": user_address},
                )
            )

        await asyncio.gather(*tasks)
        return subscription_id

    async def stream_market_trades(
        self,
        market_address: str,
        callback: Callable[[Trade], None],
    ) -> str:
        """
        Stream trades for a specific market.

        Args:
            market_address: Market address to filter by
            callback: Function to call with each trade

        Returns:
            Subscription ID that can be used to unsubscribe
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot stream blockchain events.")

        if not self._subscription_manager:
            raise ValueError("Subscription manager not initialized.")

        market_address = self._web3.to_checksum_address(market_address)
        subscription_id = f"market_trades_{market_address}"

        clob = self._get_clob(market_address)

        async def handle_fill_event(event: EventData) -> None:
            trade = self._convert_fill_event_to_trade(event, market_address)
            callback(trade)

        # Start with recent trades
        recent_trades = await self.get_market_trades_from_events(
            market_address=market_address,
            from_block=self._web3.eth.block_number - 1000,  # Last ~1000 blocks
            to_block="latest",
            limit=50,
        )

        # Send existing trades to callback
        for trade in recent_trades:
            callback(trade)

        # Subscribe to new trades
        await self._subscription_manager.subscribe(
            subscription_id, clob, self.EVENT_ORDER_FILLED, handle_fill_event
        )

        return subscription_id

    async def stream_user_trades(
        self,
        user_address: str,
        market_address: str | None = None,
        callback: Callable[[Trade], None] | None = None,
    ) -> str:
        """
        Stream trades for a specific user.

        Args:
            user_address: Address of the user
            market_address: Optional market address to filter by
            callback: Function to call with each trade

        Returns:
            Subscription ID that can be used to unsubscribe
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot stream blockchain events.")

        if not self._subscription_manager:
            raise ValueError("Subscription manager not initialized.")

        user_address = self._web3.to_checksum_address(user_address)
        subscription_id = f"user_trades_{user_address}_{market_address or 'all'}"

        # Get market CLOB contract
        clob = None
        if market_address:
            clob = self._get_clob(market_address)
            contracts_to_subscribe = [clob]
        else:
            # If we don't have a market address, we need to get all markets
            contracts_to_subscribe = list(self._clob_clients.values())
            if not contracts_to_subscribe:
                raise ValueError(
                    "No CLOB contracts available. Subscribe to specific markets first."
                )

        async def handle_maker_fill_event(event: EventData) -> None:
            if event.args.get("maker") != user_address:
                return

            contract_address = event.address
            trade = self._convert_fill_event_to_trade(event, contract_address, is_maker=True)
            callback(trade)

        async def handle_taker_fill_event(event: EventData) -> None:
            if event.args.get("taker") != user_address:
                return

            contract_address = event.address
            trade = self._convert_fill_event_to_trade(event, contract_address, is_maker=False)
            callback(trade)

        # Start with existing trades
        existing_trades = await self.get_user_trades_from_events(
            user_address=user_address,
            market_address=market_address,
            from_block=self._web3.eth.block_number - 10000,  # Last ~10000 blocks
            to_block="latest",
        )

        # Send existing trades to callback
        for trade in existing_trades:
            callback(trade)

        # Set up subscriptions for each contract
        tasks = []
        for contract in contracts_to_subscribe:
            # Subscribe to fill events (as maker)
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_maker_{contract.address}",
                    contract,
                    self.EVENT_ORDER_FILLED,
                    handle_maker_fill_event,
                    {"maker": user_address},
                )
            )

            # Subscribe to fill events (as taker)
            tasks.append(
                self._subscription_manager.subscribe(
                    f"{subscription_id}_taker_{contract.address}",
                    contract,
                    self.EVENT_ORDER_FILLED,
                    handle_taker_fill_event,
                    {"taker": user_address},
                )
            )

        await asyncio.gather(*tasks)
        return subscription_id

    async def get_user_trades(
        self,
        user_address: str,
        market_address: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Trade]:
        """
        Fetch historical trades for a specific user.

        Args:
            user_address: Address of the user
            market_address: Optional market address to filter by
            limit: Maximum number of trades to return
            offset: Offset for pagination

        Returns:
            List of user trades
        """
        raise NotImplementedError

    async def get_order_book_snapshot(self, market: Market, depth: int = 10) -> dict[str, Any]:
        """
        Get current order book snapshot from the chain.

        Args:
            market: Market object with details
            depth: Number of price levels to fetch on each side

        Returns:
            Dictionary with bids and asks arrays

        Raises:
            ValueError: If Web3 is not configured
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot fetch on-chain order book.")

        contract_address = market.address

        clob = self._get_clob(contract_address)

        # Get top of book to start traversal
        highest_bid, lowest_ask = clob.get_tob()

        # Collect bids
        bids = []
        current_bid = highest_bid
        for _ in range(depth):
            if current_bid <= 0:
                break

            limit = clob.get_limit(current_bid, Side.BUY)
            bids.append(
                {
                    "price": current_bid,
                    "size": limit.get("size", 0),
                    "orderCount": limit.get("orderCount", 0),
                }
            )

            # Move to next price level
            current_bid = clob.get_next_smallest_ticks(current_bid, Side.BUY)

        # Collect asks
        asks = []
        current_ask = lowest_ask
        for _ in range(depth):
            if current_ask <= 0:
                break

            limit = clob.get_limit(current_ask, Side.SELL)
            asks.append(
                {
                    "price": current_ask,
                    "size": limit.get("size", 0),
                    "orderCount": limit.get("orderCount", 0),
                }
            )

            # Move to next price level
            current_ask = clob.get_next_biggest_ticks(current_ask, Side.SELL)

        return {"bids": bids, "asks": asks, "timestamp": get_current_timestamp()}

    async def stream_order_book(
        self,
        market_address: str,
        callback: Callable[[dict], None],
        depth: int = 10,
        update_interval: float = 1.0,
    ) -> str:
        """
        Stream order book updates for a specific market.

        Args:
            market_address: Market address to filter by
            callback: Function to call with each order book update
            depth: Number of price levels to fetch on each side
            update_interval: Interval between order book refreshes

        Returns:
            Subscription ID that can be used to unsubscribe
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot stream blockchain events.")

        market_address = self._web3.to_checksum_address(market_address)
        subscription_id = f"orderbook_{market_address}"

        # Create a task to poll the order book
        task = asyncio.create_task(
            self._poll_order_book(market_address, callback, depth, update_interval)
        )

        # Store the task so we can cancel it later
        if self._subscription_manager:
            self._subscription_manager._running_tasks[subscription_id] = task

        return subscription_id

    async def _poll_order_book(
        self,
        market: Market,
        callback: Callable[[dict], None],
        depth: int,
        update_interval: float,
    ) -> None:
        """
        Poll the order book at regular intervals.

        Args:
            market_address: Market address
            callback: Function to call with each update
            depth: Depth of the order book
            update_interval: Interval between updates
        """

        try:
            while True:
                try:
                    # Get the current order book
                    order_book = await self.get_order_book_snapshot(market, depth)

                    # Call the callback
                    callback(order_book)

                except Exception as e:
                    logger.error(f"Error polling order book: {e}")

                # Wait for next update
                await asyncio.sleep(update_interval)
        except asyncio.CancelledError:
            # Clean up when cancelled
            raise

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from a streaming subscription.

        Args:
            subscription_id: ID of the subscription to cancel
        """
        if not self._subscription_manager:
            raise ValueError("Subscription manager not initialized.")

        await self._subscription_manager.unsubscribe(subscription_id)

    # ...existing code...
