"""Order execution functionality for the GTE client."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Optional, List, Dict, Tuple, Union

from eth_typing import AnyAddress, ChecksumAddress
from web3 import Web3
from web3.exceptions import LogTopicError
from web3.providers import WebSocketProvider
from web3.types import EventData

from .contracts.iclob import ICLOB
from .contracts.factory import CLOBFactory
from .contracts.erc20 import ERC20
from .contracts.router import Router
from .contracts.structs import (
    Side, 
    Settlement, 
    LimitOrderType, 
    FillOrderType,
    ICLOBPostLimitOrderArgs,
    ICLOBPostFillOrderArgs,
    ICLOBAmendArgs,
    ICLOBCancelArgs
)
from .contracts.utils import get_current_timestamp, TypedContractFunction
from .info import MarketService
from .models import Market, Order, OrderStatus, OrderSide, OrderType, TimeInForce, Trade

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
    EVENT_LIMIT_ORDER_SUBMITTED = "LimitOrderSubmitted"
    EVENT_LIMIT_ORDER_PROCESSED = "LimitOrderProcessed"
    EVENT_FILL_ORDER_SUBMITTED = "FillOrderSubmitted"
    EVENT_FILL_ORDER_PROCESSED = "FillOrderProcessed"
    EVENT_ORDER_AMENDED = "OrderAmended"
    EVENT_ORDER_CANCELED = "OrderCanceled"
    EVENT_ORDER_MATCHED = "OrderMatched"

    def __init__(self, web3: Web3, sender_address: ChecksumAddress, factory_address: ChecksumAddress):
        """
        Initialize the execution client.

        Args:
            web3: Web3 instance for on-chain interactions
            sender_address: Address to send transactions from
            factory_address: Address of the GTE Factory contract
        """
        self._web3 = web3
        self._clob_clients: Dict[ChecksumAddress, ICLOB] = {}
        self._token_clients: Dict[ChecksumAddress, ERC20] = {}
        self._factory: Optional[CLOBFactory] = None
        self._sender_address = sender_address
        self._subscription_manager: Optional[SubscriptionManager] = None

        # Create factory client
        self._factory = CLOBFactory(web3=web3, contract_address=factory_address)
        
        # Initialize subscription manager if using websocket provider
        if isinstance(web3.provider, WebSocketProvider):
            self._subscription_manager = SubscriptionManager(web3)

    def _get_clob(self, contract_address: ChecksumAddress) -> ICLOB:
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

        if contract_address not in self._clob_clients:
            self._clob_clients[contract_address] = ICLOB(
                web3=self._web3, contract_address=contract_address
            )
        return self._clob_clients[contract_address]
    
    def _get_token(self, token_address: ChecksumAddress) -> ERC20:
        """
        Get or create an ERC20 token contract instance.
        
        Args:
            token_address: Token contract address
            
        Returns:
            ERC20 contract instance
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot interact with contracts.")
            
        if token_address not in self._token_clients:
            self._token_clients[token_address] = ERC20(
                web3=self._web3, contract_address=token_address
            )
        return self._token_clients[token_address]

    async def place_limit_order(
        self, 
        market: Market,
        side: OrderSide,
        amount: float,
        price: float,
        time_in_force: TimeInForce = TimeInForce.GTC,
        client_order_id: int = 0,
        **kwargs
    ) -> TypedContractFunction:
        """
        Place a limit order on the CLOB.
        
        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in base tokens
            price: Order price
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Optional client order ID for tracking
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._get_clob(market.address)
        
        # Convert model types to contract types
        contract_side = Side.BUY if side == OrderSide.BUY else Side.SELL
        
        # Convert time in force to limit order type
        if time_in_force == TimeInForce.GTC:
            limit_order_type = LimitOrderType.GOOD_TILL_CANCELLED
        elif time_in_force == TimeInForce.IOC:
            limit_order_type = LimitOrderType.IMMEDIATE_OR_CANCEL
        elif time_in_force == TimeInForce.FOK:
            limit_order_type = LimitOrderType.FILL_OR_KILL
        else:
            raise ValueError(f"Unsupported time in force: {time_in_force}")
        
        # Convert amount to base token atoms
        base_token = self._get_token(market.base_token_address)
        amount_in_base = base_token.format_amount(amount)
        
        # Convert price to ticks
        tick_size = market.tick_size
        price_in_ticks = int(price / tick_size)
        
        # Create post limit order args
        args = clob.create_post_limit_order_args(
            amount_in_base=amount_in_base,
            price=price_in_ticks,
            side=contract_side,
            cancel_timestamp=0,  # No expiration
            client_order_id=client_order_id,
            limit_order_type=limit_order_type,
            settlement=Settlement.INSTANT
        )
        
        # Return the transaction
        return clob.post_limit_order(
            account=self._sender_address,
            args=args,
            sender_address=self._sender_address,
            **kwargs
        )

    async def place_market_order(
        self, 
        market: Market,
        side: OrderSide,
        amount: float,
        amount_is_base: bool = True,
        **kwargs
    ) -> TypedContractFunction:
        """
        Place a market order on the CLOB.
        
        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in base tokens if amount_is_base is True, otherwise in quote tokens
            amount_is_base: Whether the amount is in base tokens
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._get_clob(market.address)
        
        # Convert model types to contract types
        contract_side = Side.BUY if side == OrderSide.BUY else Side.SELL
        
        # Convert amount to atoms
        if amount_is_base:
            base_token = self._get_token(market.base_token_address)
            amount_in_atoms = base_token.format_amount(amount)
        else:
            quote_token = self._get_token(market.quote_token_address)
            amount_in_atoms = quote_token.format_amount(amount)
        
        # For market orders, use a very aggressive price limit to ensure execution
        # For buy orders: high price, for sell orders: low price
        highest_bid, lowest_ask = clob.get_tob()
        if contract_side == Side.BUY:
            price_limit = lowest_ask * 2 if lowest_ask > 0 else 2**128  # Very high price for buy
        else:
            price_limit = highest_bid // 2 if highest_bid > 0 else 1  # Very low price for sell
        
        # Create post fill order args
        args = clob.create_post_fill_order_args(
            amount=amount_in_atoms,
            price_limit=price_limit,
            side=contract_side,
            amount_is_base=amount_is_base,
            fill_order_type=FillOrderType.IMMEDIATE_OR_CANCEL,
            settlement=Settlement.INSTANT
        )
        
        # Return the transaction
        return clob.post_fill_order(
            account=self._sender_address,
            args=args,
            sender_address=self._sender_address,
            **kwargs
        )

    async def amend_order(
        self, 
        market: Market,
        order_id: int,
        new_amount: Optional[float] = None,
        new_price: Optional[float] = None,
        **kwargs
    ) -> TypedContractFunction:
        """
        Amend an existing order.
        
        Args:
            market: Market the order is on
            order_id: ID of the order to amend
            new_amount: New amount for the order (None to keep current)
            new_price: New price for the order (None to keep current)
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._get_clob(market.address)
        
        # Get the current order
        order = clob.get_order(order_id)
        
        # Extract order details
        side = order['side']
        current_amount = order['amount']
        current_price = order['price']
        
        # Convert new values to contract format
        base_token = self._get_token(market.base_token_address)
        amount_in_base = base_token.format_amount(new_amount) if new_amount is not None else current_amount
        
        tick_size = market.tick_size
        price_in_ticks = int(new_price / tick_size) if new_price is not None else current_price
        
        # Create amend args
        args = clob.create_amend_args(
            order_id=order_id,
            amount_in_base=amount_in_base,
            price=price_in_ticks,
            side=side,
            cancel_timestamp=0,  # No expiration
            limit_order_type=LimitOrderType.GOOD_TILL_CANCELLED,
            settlement=Settlement.INSTANT
        )
        
        # Return the transaction
        return clob.amend(
            account=self._sender_address,
            args=args,
            sender_address=self._sender_address,
            **kwargs
        )

    async def cancel_order(
        self, 
        market: Market,
        order_id: int,
        **kwargs
    ) -> TypedContractFunction:
        """
        Cancel an existing order.
        
        Args:
            market: Market the order is on
            order_id: ID of the order to cancel
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._get_clob(market.address)
        
        # Create cancel args
        args = clob.create_cancel_args(
            order_ids=[order_id],
            settlement=Settlement.INSTANT
        )
        
        # Return the transaction
        return clob.cancel(
            account=self._sender_address,
            args=args,
            sender_address=self._sender_address,
            **kwargs
        )
    
    async def cancel_all_orders(
        self, 
        market: Market,
        **kwargs
    ) -> TypedContractFunction:
        """
        Cancel all orders for the current user on a specific market.
        
        Args:
            market: Market to cancel orders on
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._get_clob(market.address)
        
        # Get all active orders for the user
        next_order_id = clob.get_next_order_id()
        orders = await self.get_user_orders_from_events(
            user_address=self._sender_address,
            market_address=market.address,
            from_block=self._web3.eth.block_number - 10000,  # Last 10000 blocks
            to_block="latest"
        )
        
        # Filter for open orders
        open_order_ids = [int(order.id) for order in orders if order.status == OrderStatus.OPEN]
        
        if not open_order_ids:
            # No orders to cancel
            raise ValueError("No open orders to cancel")
        
        # Create cancel args
        args = clob.create_cancel_args(
            order_ids=open_order_ids,
            settlement=Settlement.INSTANT
        )
        
        # Return the transaction
        return clob.cancel(
            account=self._sender_address,
            args=args,
            sender_address=self._sender_address,
            **kwargs
        )
    
    async def deposit_to_market(
        self,
        token_address: ChecksumAddress,
        amount: float,
        **kwargs
    ) -> List[TypedContractFunction]:
        """
        Deposit tokens to the exchange for trading.
        
        Args:
            token_address: Address of token to deposit
            amount: Amount to deposit
            **kwargs: Additional transaction parameters
            
        Returns:
            List of TypedContractFunction objects (approve and deposit)
        """
        if not self._factory:
            raise ValueError("Factory not initialized")
        
        token = self._get_token(token_address)
        amount_in_atoms = token.format_amount(amount)
        
        # First approve the factory to spend tokens
        approve_tx = token.approve(
            spender=self._factory.address,
            amount=amount_in_atoms,
            sender_address=self._sender_address,
            **kwargs
        )
        
        # Then deposit the tokens
        deposit_tx = self._factory.deposit(
            account=self._sender_address,
            token=token_address,
            amount=amount_in_atoms,
            from_operator=False,
            sender_address=self._sender_address,
            **kwargs
        )
        
        return [approve_tx, deposit_tx]
    
    async def withdraw_from_market(
        self,
        token_address: ChecksumAddress,
        amount: float,
        **kwargs
    ) -> TypedContractFunction:
        """
        Withdraw tokens from the exchange.
        
        Args:
            token_address: Address of token to withdraw
            amount: Amount to withdraw
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction for the withdraw transaction
        """
        if not self._factory:
            raise ValueError("Factory not initialized")
        
        token = self._get_token(token_address)
        amount_in_atoms = token.format_amount(amount)
        
        # Withdraw the tokens
        return self._factory.withdraw(
            account=self._sender_address,
            token=token_address,
            amount=amount_in_atoms,
            to_operator=False,
            sender_address=self._sender_address,
            **kwargs
        )
    
    async def get_balance(
        self,
        token_address: ChecksumAddress,
        account: Optional[ChecksumAddress] = None
    ) -> Tuple[float, float]:
        """
        Get token balance for an account both on-chain and in the exchange.
        
        Args:
            token_address: Address of token to check
            account: Account to check (defaults to sender address)
            
        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """
        if not self._factory:
            raise ValueError("Factory not initialized")
        
        account = account or self._sender_address
        token = self._get_token(token_address)
        
        # Get wallet balance
        wallet_balance_raw = token.balance_of(account)
        wallet_balance = token.format_amount_readable(wallet_balance_raw)
        
        # Get exchange balance
        exchange_balance_raw = self._factory.get_account_balance(account, token_address)
        exchange_balance = token.format_amount_readable(exchange_balance_raw)
        
        return (wallet_balance, exchange_balance)

    async def _convert_contract_order_to_model(
        self, 
        order_data: Dict[str, Any], 
        market_address: ChecksumAddress
    ) -> Order:
        """
        Convert contract order data to Order model.
        
        Args:
            order_data: Order data from the contract
            market_address: Address of the market
            
        Returns:
            Order model
        """
        # Map contract side to model side
        side = OrderSide.BUY if order_data.get('side', 0) == Side.BUY else OrderSide.SELL
        
        # Determine order status
        status = OrderStatus.OPEN
        if order_data.get('amount', 0) == 0:
            status = OrderStatus.FILLED
        elif order_data.get('cancelTimestamp', 0) > 0 and order_data.get('cancelTimestamp', 0) < get_current_timestamp():
            status = OrderStatus.EXPIRED
            
        # Create Order model
        return Order(
            id=str(order_data.get('id', 0)),
            market_address=market_address,
            side=side,
            order_type=OrderType.LIMIT,
            amount=float(order_data.get('amount', 0)),
            price=float(order_data.get('price', 0)),
            time_in_force=TimeInForce.GTC,  # Default
            status=status,
            filled_amount=0.0,  # Need to be calculated from events
            filled_price=0.0,  # Need to be calculated from events
            created_at=0  # Need to be retrieved from event timestamp
        )

    async def _convert_fill_event_to_trade(
        self, 
        event: EventData, 
        market_address: ChecksumAddress, 
        is_maker: bool = False
    ) -> Trade:
        """
        Convert fill event to Trade model.
        
        Args:
            event: Fill event data
            market_address: Address of the market
            is_maker: Whether this trade was as a maker
            
        Returns:
            Trade model
        """
        # Access args using dictionary syntax since EventData is a TypedDict
        args = event['args']
        
        # Determine side from event data
        side = OrderSide.BUY if args.get('side', 0) == Side.BUY else OrderSide.SELL
        
        # For takers, the side is opposite of the maker's side
        if not is_maker:
            side = OrderSide.BUY if side == OrderSide.SELL else OrderSide.SELL
            
        # Create Trade model
        return Trade(
            market_address=market_address,
            timestamp=args.get('timestamp', get_current_timestamp() * 1000),
            price=float(args.get('price', 0)),
            size=float(args.get('amount', 0)),
            side=side,
            tx_hash=event['transactionHash'],  # Use dictionary access
            maker=args.get('maker'),
            taker=args.get('taker'),
            trade_id=args.get('orderId', 0)
        )

    async def stream_user_orders(
            self,
            user_address: ChecksumAddress,
            market_address: Optional[ChecksumAddress] = None,
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
        # ...existing code...

        async def handle_post_event(event: EventData) -> None:
            # Use dictionary access for EventData
            if event['args'].get("account") != user_address:
                return

            contract_address = event['address']
            order = self._convert_post_event_to_order(event, contract_address)
            orders_by_id[order.id] = order
            callback(order, "posted")

        async def handle_fill_event(event: EventData) -> None:
            # Use dictionary access for EventData
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
            # ...rest of the method...

        async def handle_cancel_event(event: EventData) -> None:
            # Use dictionary access for EventData
            args = event['args']
            if args.get("account") != user_address:
                return

            order_id = args.get("orderId")
            if order_id in orders_by_id:
                order = orders_by_id[order_id]
                order.status = OrderStatus.CANCELLED
                callback(order, "cancelled")

        async def handle_amend_event(event: EventData) -> None:
            # Use dictionary access for EventData
            args = event['args']
            if args.get("account") != user_address:
                return

            order_id = args.get("orderId")
            if order_id in orders_by_id:
                order = orders_by_id[order_id]
                self._update_order_from_amend_event(order, event)
                callback(order, "amended")

        # ...rest of the method...

    async def stream_market_trades(
            self,
            market_address: ChecksumAddress,
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
        # ...existing code...

        async def handle_fill_event(event: EventData) -> None:
            # Use dictionary access for EventData
            trade = self._convert_fill_event_to_trade(event, market_address)
            callback(trade)

        # ...rest of the method...

    async def stream_user_trades(
            self,
            user_address: ChecksumAddress,
            market_address: Optional[ChecksumAddress] = None,
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
        # ...existing code...

        async def handle_maker_fill_event(event: EventData) -> None:
            # Use dictionary access for EventData
            if event['args'].get("maker") != user_address:
                return

            contract_address = event['address']
            trade = self._convert_fill_event_to_trade(event, contract_address, is_maker=True)
            callback(trade)

        async def handle_taker_fill_event(event: EventData) -> None:
            # Use dictionary access for EventData
            if event['args'].get("taker") != user_address:
                return

            contract_address = event['address']
            trade = self._convert_fill_event_to_trade(event, contract_address, is_maker=False)
            callback(trade)

        # ...rest of the method...
