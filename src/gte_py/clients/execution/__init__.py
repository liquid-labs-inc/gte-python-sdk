"""Order execution functionality for the GTE client."""

import asyncio
import logging
from typing import Optional, List, Tuple

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from web3.types import EventData

from gte_py.api.chain.events import OrderCanceledEvent
from gte_py.api.chain.structs import (
    Side,
    Settlement,
    LimitOrderType,
    FillOrderType,
    CLOBOrder
)
from gte_py.api.chain.utils import get_current_timestamp, TypedContractFunction
from gte_py.clients.iclob import CLOBClient
from gte_py.clients.token import TokenClient
from gte_py.models import Market, Order, OrderStatus, Side, OrderType, TimeInForce, Trade

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

    def __init__(self, web3: AsyncWeb3,
                 main_account: ChecksumAddress,
                 clob: CLOBClient,
                 token: TokenClient
                 ):
        """
        Initialize the execution client.

        Args:
            web3: AsyncWeb3 instance for on-chain interactions
            main_account: Address to send transactions from
        """
        self._web3 = web3
        self.clob = clob
        self.token = token
        self.main_account = main_account

    async def place_limit_order_tx(
            self,
            market: Market,
            side: Side,
            amount: int,
            price: int,
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
        clob = self.clob.get_clob(market.address)

        # Convert model types to contract types
        contract_side = Side.BUY if side == Side.BUY else Side.SELL

        if not market.check_lot_size(amount):
            raise ValueError(f"Amount is not multiples of lot size: {amount} (lot size: {market.lot_size_in_base})")
        if not market.check_tick_size(price):
            raise ValueError(f"Price is not multiples of tick size: {price} (tick size: {market.tick_size_in_quote})")

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
                settlement=Settlement.INSTANT
            )

            # Return the transaction
            return clob.post_fill_order(
                account=self.main_account,
                args=args,
                **kwargs
            )
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
                settlement=Settlement.INSTANT
            )

            # Return the transaction
            return clob.post_limit_order(
                account=self.main_account,
                args=args,
                **kwargs
            )

    async def place_limit_order(
            self,
            market: Market,
            side: Side,
            amount: int,
            price: int,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            **kwargs
    ) -> Order:
        tx = await self.place_limit_order_tx(
            market=market,
            side=side,
            amount=amount,
            price=price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            **kwargs
        )
        return await tx.send_wait()

    async def place_market_order_tx(
            self,
            market: Market,
            side: Side,
            amount: int,
            amount_is_base: bool = True,
            slippage: float = 0.01,
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
            settlement=Settlement.INSTANT
        )

        # Return the transaction
        return clob.post_fill_order(
            account=self.main_account,
            args=args,
            **kwargs
        )

    async def place_market_order(
            self,
            market: Market,
            side: Side,
            amount: int,
            amount_is_base: bool = True,
            slippage: float = 0.01,
            **kwargs
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
            **kwargs
        )
        return await tx.send_wait()

    async def amend_order_tx(
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
        clob = self.clob.get_clob(market.address)

        # Get the current order
        order = await clob.get_order(order_id)

        # Extract order details
        side = order.side
        current_amount = order.amount
        current_price = order.price

        amount_in_base = new_amount or current_amount

        tick_size = market.tick_size_in_quote
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
            account=self.main_account,
            args=args,
            **kwargs
        )

    async def amend_order(
            self,
            market: Market,
            order_id: int,
            new_amount: Optional[float] = None,
            new_price: Optional[float] = None,
            **kwargs
    ):
        tx = await self.amend_order_tx(
            market=market,
            order_id=order_id,
            new_amount=new_amount,
            new_price=new_price,
            **kwargs)
        return await tx.send_wait()

    async def cancel_order_tx(
            self,
            market: Market,
            order_id: int,
            **kwargs
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
        args = clob.create_cancel_args(
            order_ids=[order_id],
            settlement=Settlement.INSTANT
        )

        # Return the transaction
        return clob.cancel(
            account=self.main_account,
            args=args,
            **kwargs
        )

    async def cancel_order(
            self,
            market: Market,
            order_id: int,
            **kwargs
    ):
        tx = await self.cancel_order_tx(
            market=market,
            order_id=order_id,
            **kwargs
        )
        return await tx.send_wait()

    async def get_open_orders(self, market: Market, address: ChecksumAddress | None = None) -> List[Order]:
        """
        Get all orders for a specific market and address.

        Args:
            market: Market to get orders from
            address: Address to filter orders by (None for all)

        Returns:
            List of Order objects
        """
        clob = self.clob.get_clob(market.address)
        best_bid, best_ask = await clob.get_tob()
        orders = []
        # Get all orders for the bid and ask price levels
        price_level = best_bid
        tasks = []

        while price_level > 0:
            tasks.append(asyncio.create_task(self.get_orders_for_price_level(
                market=market,
                price=price_level,
                side=Side.BUY,
                address=address
            )))
            price_level = await clob.get_next_smallest_price(price_level, Side.BUY)
        price_level = best_ask
        while price_level > 0:
            tasks.append(asyncio.create_task(self.get_orders_for_price_level(
                market=market,
                price=price_level,
                side=Side.SELL,
                address=address
            )))
            price_level = await clob.get_next_biggest_price(price_level, Side.SELL)

        address = address or self.main_account
        for task in tasks:
            try:
                pl_orders = await task
                for order in pl_orders:
                    if order.owner != address:
                        continue
                    orders.append(order)
            except Exception as e:
                logger.error(f"Error getting orders: {e}")
        return orders

    async def get_orders_for_price_level(self,
                                         market: Market,
                                         price: int,
                                         side: Side,
                                         address: ChecksumAddress | None = None
                                         ) -> List[Order]:
        """
        Get all orders for a specific price level.

        Args:
            market: Market to get orders from
            price: Price level to filter orders by
            side: Side of the order (BUY or SELL)
            address: Address to filter orders by (None for all)

        Returns:
            List of Order objects
        """
        clob = self.clob.get_clob(market.address)
        orders = []
        (num, head, tail) = await clob.get_limit(price, side)
        order_id = head
        for i in range(num):
            order = await clob.get_order(order_id)
            if address is None or order.owner == address:
                orders.append(self._convert_contract_order_to_model(market, order))
            order_id = order.nextOrderId
        return orders

    async def cancel_all_orders(
            self,
            market: Market,
            **kwargs
    ):
        """
        Cancel all orders for the current user on a specific market.
        
        Args:
            market: Market to cancel orders on
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract

        orders = await self.get_open_orders(market, **kwargs)
        for order in orders:
            if order.status != OrderStatus.OPEN:
                continue
            await self.cancel_order(market, order.order_id, **kwargs)

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

        account = account or self.main_account
        token = self.token.get_erc20(token_address)

        # Get wallet balance
        wallet_balance_raw = await token.balance_of(account)
        wallet_balance = await token.convert_amount_to_float(wallet_balance_raw)

        # Get exchange balance
        exchange_balance_raw = await self.clob.clob_factory.get_account_balance(account, token_address)
        exchange_balance = await token.convert_amount_to_float(exchange_balance_raw)

        return wallet_balance, exchange_balance

    async def get_order(self, market: Market, order_id: int) -> Order:
        clob = self.clob.get_clob(market.address)
        order = await clob.get_order(order_id)
        return self._convert_contract_order_to_model(market, order)

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
        elif order_data.cancelTimestamp > 0 and order_data.cancelTimestamp < get_current_timestamp():
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
        side = Side.BUY if args.get('side', 0) == Side.BUY else Side.SELL

        # For takers, the side is opposite of the maker's side
        if not is_maker:
            side = Side.BUY if side == Side.SELL else Side.SELL

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
