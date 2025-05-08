"""Order execution functionality for the GTE client."""

import logging
from typing import Optional, List, Tuple, Dict, Any, Awaitable

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from gte_py.api.chain.events import OrderCanceledEvent, FillOrderProcessedEvent, LimitOrderProcessedEvent
from gte_py.api.chain.structs import Side, Settlement, LimitOrderType, FillOrderType, CLOBOrder
from gte_py.api.chain.utils import get_current_timestamp, TypedContractFunction
from gte_py.api.rest import RestApi
from gte_py.clients.clob import CLOBClient
from gte_py.clients.orderbook import OrderbookClient
from gte_py.clients.token import TokenClient
from gte_py.models import Market, Order, OrderStatus, Side, OrderType, TimeInForce

logger = logging.getLogger(__name__)


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

    def __init__(
            self,
            web3: AsyncWeb3,
            main_account: ChecksumAddress,
            clob: CLOBClient,
            token: TokenClient,
            rest: RestApi,
            orderbook: OrderbookClient
    ):
        """
        Initialize the execution client.

        Args:
            web3: AsyncWeb3 instance for on-chain interactions
            main_account: Address to send transactions from
            clob: CLOBClient instance
            token: TokenClient instance
            rest: Optional RestApi instance for API interactions
            orderbook: OrderbookClient instance for order book interactions
        """
        self._web3 = web3
        self._rest = rest
        self.clob = clob
        self.token = token
        self.main_account = main_account
        self._orderbook = orderbook

    def place_limit_order_tx(
            self,
            market: Market,
            side: Side,
            amount: int,
            price: int,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            **kwargs,
    ) -> TypedContractFunction[FillOrderProcessedEvent | LimitOrderProcessedEvent]:
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
        clob = self.clob.get_clob(market.address)

        # Convert model types to contract types
        contract_side = Side.BUY if side == Side.BUY else Side.SELL

        # For IOC and FOK orders, we use the fill order API which has different behavior
        if time_in_force in [TimeInForce.IOC, TimeInForce.FOK]:
            # Convert amount to base token atoms

            if time_in_force == TimeInForce.IOC:
                fill_order_type = FillOrderType.IMMEDIATE_OR_CANCEL
            elif time_in_force == TimeInForce.FOK:
                fill_order_type = FillOrderType.FILL_OR_KILL
            else:
                raise ValueError(f"Unknown time_in_force: {time_in_force}")

            # Create post fill order args
            args = clob.create_post_fill_order_args(
                amount=amount,
                price_limit=price,
                side=contract_side,
                amount_is_base=True,  # Since amount is in base tokens
                fill_order_type=fill_order_type,
                settlement=Settlement.INSTANT,
            )

            # Return the transaction
            return clob.post_fill_order(account=self.main_account, args=args, **kwargs)
        else:
            if time_in_force == TimeInForce.GTC:
                tif = LimitOrderType.GOOD_TILL_CANCELLED
            elif time_in_force == TimeInForce.FOK:
                tif = LimitOrderType.FILL_OR_KILL
            elif time_in_force == TimeInForce.IOC:
                tif = LimitOrderType.IMMEDIATE_OR_CANCEL
            elif time_in_force == TimeInForce.GTT:
                tif = LimitOrderType.GOOD_TILL_TIME
            else:
                raise ValueError(f"Unknown time_in_force: {time_in_force}")
            # Create post limit order args
            args = clob.create_post_limit_order_args(
                amount_in_base=amount,
                price=price,
                side=contract_side,
                cancel_timestamp=0,  # No expiration
                client_order_id=client_order_id,
                limit_order_type=tif,
                settlement=Settlement.INSTANT,
            )

            # Return the transaction
            return clob.post_limit_order(account=self.main_account, args=args, **kwargs)

    def place_limit_order(
            self,
            market: Market,
            side: Side,
            amount: int,
            price: int,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            **kwargs: Unpack[TxParams],
    ) -> Awaitable[Order]:
        tx = self.place_limit_order_tx(
            market=market,
            side=side,
            amount=amount,
            price=price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            **kwargs,
        )
        tx.send_nowait()

        async def task():
            log = await tx.retrieve()
            if isinstance(log, FillOrderProcessedEvent):
                order = Order.from_clob_fill_order_processed(
                    log, amount, side, price
                )
            elif isinstance(log, LimitOrderProcessedEvent):
                order = Order.from_clob_limit_order_processed(
                    log, amount, side, price
                )
            else:
                raise ValueError(f"Unknown event type: {log.event_name}")
            return order

        return task()

    async def place_market_order_tx(
            self,
            market: Market,
            side: Side,
            amount: int,
            amount_is_base: bool = True,
            slippage: float = 0.01,
            **kwargs,
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
        clob = self.clob.get_clob(market.address)

        # Convert model types to contract types
        contract_side = Side.BUY if side == Side.BUY else Side.SELL

        # For market orders, use a very aggressive price limit to ensure execution
        # For buy orders: high price, for sell orders: low price
        highest_bid, lowest_ask = await clob.get_tob()
        if contract_side == Side.BUY:
            price_limit = int(lowest_ask * (1 + slippage))
        else:
            price_limit = int(highest_bid * (1 - slippage))

        # Create post fill order args
        args = clob.create_post_fill_order_args(
            amount=amount,
            price_limit=price_limit,
            side=contract_side,
            amount_is_base=amount_is_base,
            fill_order_type=FillOrderType.IMMEDIATE_OR_CANCEL,
            settlement=Settlement.INSTANT,
        )

        # Return the transaction
        return clob.post_fill_order(account=self.main_account, args=args, **kwargs)

    async def place_market_order(
            self,
            market: Market,
            side: Side,
            amount: int,
            amount_is_base: bool = True,
            slippage: float = 0.01,
            **kwargs,
    ):
        """
        Place a market order on the CLOB.

        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in base tokens if amount_is_base is True, otherwise in quote tokens
            amount_is_base: Whether the amount is in base tokens
            slippage: Slippage percentage for price limit
            **kwargs: Additional transaction parameters

        Returns:
            Order object representing the placed order
        """
        tx = await self.place_market_order_tx(
            market=market,
            side=side,
            amount=amount,
            amount_is_base=amount_is_base,
            slippage=slippage,
            **kwargs,
        )
        return await tx.send_wait()

    async def amend_order_tx(
            self,
            market: Market,
            order_id: int,
            new_amount: Optional[int] = None,
            new_price: Optional[int] = None,
            **kwargs,
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
        clob = self.clob.get_clob(market.address)

        # Get the current order
        order = await clob.get_order(order_id)

        # Extract order details
        side = order.side
        current_amount = order.amount
        current_price = order.price

        amount_in_base = new_amount or current_amount

        price_in_ticks = new_price if new_price is not None else current_price

        # Create amend args
        args = clob.create_amend_args(
            order_id=order_id,
            amount_in_base=amount_in_base,
            price=price_in_ticks,
            side=side,
            cancel_timestamp=0,  # No expiration
            limit_order_type=LimitOrderType.GOOD_TILL_CANCELLED,
            settlement=Settlement.INSTANT,
        )

        # Return the transaction
        return clob.amend(account=self.main_account, args=args, **kwargs)

    async def amend_order(
            self,
            market: Market,
            order_id: int,
            new_amount: Optional[int] = None,
            new_price: Optional[int] = None,
            **kwargs,
    ):
        tx = await self.amend_order_tx(
            market=market, order_id=order_id, new_amount=new_amount, new_price=new_price, **kwargs
        )
        return await tx.send_wait()

    async def cancel_order_tx(
            self, market: Market, order_id: int, **kwargs
    ) -> TypedContractFunction[OrderCanceledEvent | None]:
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
        clob = self.clob.get_clob(market.address)

        # Create cancel args
        args = clob.create_cancel_args(order_ids=[order_id], settlement=Settlement.INSTANT)

        # Return the transaction
        return clob.cancel(account=self.main_account, args=args, **kwargs)

    async def cancel_order(self, market: Market, order_id: int, **kwargs):
        tx = await self.cancel_order_tx(market=market, order_id=order_id, **kwargs)
        return await tx.send_wait()

    async def cancel_all_orders(self, market: Market, **kwargs):
        """
        Cancel all orders for the current user on a specific market.

        Args:
            market: Market to cancel orders on
            **kwargs: Additional transaction parameters
        """
        orders = await self.get_open_orders(market, **kwargs)
        for order in orders:
            if order.status != OrderStatus.OPEN:
                continue
            await self.cancel_order(market, order.order_id, **kwargs)

    async def get_balance(
            self, token_address: ChecksumAddress, account: Optional[ChecksumAddress] = None
    ) -> Tuple[float, float]:
        """
        Get token balance for an account both on-chain and in the exchange.

        Args:
            token_address: Address of token to check
            account: Account to check (defaults to sender address)

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """

        account = account or self.main_account
        token = self.token.get_erc20(token_address)

        # Get wallet balance
        wallet_balance_raw = await token.balance_of(account)
        wallet_balance = await token.convert_amount_to_quantity(wallet_balance_raw)

        # Get exchange balance
        exchange_balance_raw = await self.clob.clob_factory.get_account_balance(
            account, token_address
        )
        exchange_balance = await token.convert_amount_to_quantity(exchange_balance_raw)

        return wallet_balance, exchange_balance

    async def get_order(self, market: Market, order_id: int) -> Order:
        return await self._orderbook.get_order(market, order_id)

    async def get_open_orders(
            self, market: Market, level: int | None = None
    ) -> List[Order]:
        """
        Get all orders for a specific market and address from the chain directly.
        This is a fallback method when the REST API is not available.

        Args:
            market: Market to get orders from
            level: Number of price levels to retrieve (None for all)


        Returns:
            List of Order objects
        """
        orders = await self._orderbook.get_open_orders(market, level=level)
        return [o for o in orders if o.owner == self.main_account]

    async def get_open_orders_rest(
            self, market: Market
    ) -> List[Order]:
        """
        Get open orders for an address on a specific market using the REST API.

        Args:
            address: EVM address of the user (defaults to main account)

        Returns:
            List of Order objects representing open orders
        """

        response = await self._rest.get_user_open_orders(self.main_account, market.address)
        return [self._parse_open_order(order_data) for order_data in response]


    async def get_filled_orders(
            self, address: Optional[ChecksumAddress] = None, market_address: ChecksumAddress = None
    ) -> List[Order]:
        """
        Get filled orders for an address on a specific market using the REST API.

        Args:
            address: EVM address of the user (defaults to main account)
            market_address: EVM address of the market

        Returns:
            List of Order objects representing filled orders
        """
        if address is None:
            address = self.main_account

        if market_address is None:
            raise ValueError("market_address is required")

        try:
            response = await self._rest.get_user_filled_orders(address, market_address)
            return [self._parse_filled_order(order_data) for order_data in response]
        except Exception as e:
            logger.error(f"Error fetching filled orders: {e}")
            return []

    async def get_order_history(
            self, address: Optional[ChecksumAddress] = None, market_address: ChecksumAddress = None
    ) -> List[Order]:
        """
        Get order history for an address on a specific market using the REST API.

        Args:
            address: EVM address of the user (defaults to main account)
            market_address: EVM address of the market

        Returns:
            List of Order objects representing order history
        """
        if address is None:
            address = self.main_account

        if market_address is None:
            raise ValueError("market_address is required")

        try:
            response = await self._rest.get_user_order_history(address, market_address)
            return [self._parse_order_history(order_data) for order_data in response]
        except Exception as e:
            logger.error(f"Error fetching order history: {e}")
            return []

    def _convert_contract_order_to_model(
            self,
            market: Market,
            order_data: CLOBOrder,
    ) -> Order:
        """
        Convert contract order data to Order model.

        Args:
            order_data: Order data from the contract
            market: Address of the market

        Returns:
            Order model
        """

        # Determine order status
        status = OrderStatus.OPEN
        if order_data.amount == 0:
            status = OrderStatus.FILLED
        elif (
                order_data.cancelTimestamp > 0 and order_data.cancelTimestamp < get_current_timestamp()
        ):
            status = OrderStatus.EXPIRED

        # Create Order model
        return Order(
            order_id=order_data.id,
            market_address=market.address,
            side=order_data.side,
            order_type=OrderType.LIMIT,
            amount=order_data.amount,
            price=order_data.price,
            time_in_force=TimeInForce.GTC,  # Default
            status=status,
            owner=order_data.owner,
            created_at=0,  # Need to be retrieved from event timestamp
        )

    def _parse_open_order(self, order_data: Dict[str, Any]) -> Order:
        """
        Parse open order data from REST API response.

        Args:
            order_data: Order data from the API

        Returns:
            Order object
        """
        return Order(
            order_id=int(order_data.get("orderId", 0)),
            market_address=order_data.get("marketAddress"),
            side=Side.BUY if order_data.get("side") == "bid" else Side.SELL,
            order_type=OrderType.LIMIT,
            amount=order_data.get("originalSize", 0),
            price=order_data.get("limitPrice", 0),
            time_in_force=TimeInForce.GTC,  # Default for open orders
            status=OrderStatus.OPEN,
            owner=order_data.get("owner", None),  # May be provided in some API responses
            created_at=order_data.get("placedAt", 0),
        )

    def _parse_filled_order(self, order_data: Dict[str, Any]) -> Order:
        """
        Parse filled order data from REST API response.

        Args:
            order_data: Order data from the API

        Returns:
            Order object
        """
        return Order(
            order_id=int(order_data.get("orderId", 0)),
            market_address=order_data.get("marketAddress"),
            side=Side.BUY if order_data.get("side") == "bid" else Side.SELL,
            order_type=OrderType.LIMIT,  # Assuming all filled orders were limit orders
            amount=order_data.get("sizeFilled", 0),
            price=order_data.get("price", 0),
            time_in_force=TimeInForce.GTC,  # Default
            status=OrderStatus.FILLED,
            owner=order_data.get("owner", None),
            created_at=0,  # Not provided
        )

    def _parse_order_history(self, order_data: Dict[str, Any]) -> Order:
        """
        Parse order history data from REST API response.

        Args:
            order_data: Order data from the API

        Returns:
            Order object
        """
        # Determine order status based on available data
        status = OrderStatus.OPEN
        if order_data.get("status") == "filled":
            status = OrderStatus.FILLED
        elif order_data.get("status") == "canceled":
            status = OrderStatus.CANCELLED

        order_type = OrderType.LIMIT
        if order_data.get("orderType") == "fill":
            order_type = OrderType.MARKET

        return Order(
            order_id=int(order_data.get("orderId", 0)),
            market_address=order_data.get("marketAddress"),
            side=Side.BUY if order_data.get("side") == "bid" else Side.SELL,
            order_type=order_type,
            amount=order_data.get("originalSize", 0),
            price=order_data.get("limitPrice", 0),
            time_in_force=TimeInForce.GTC,  # Default
            status=status,
            owner=order_data.get("owner", None),
            created_at=order_data.get("placedAt", 0),
        )
