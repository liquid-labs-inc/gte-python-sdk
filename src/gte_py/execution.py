"""Order execution functionality for the GTE client."""

import logging
import time
from typing import Any

from web3 import Web3
from web3.types import TxParams

from .contracts.iclob import ICLOB
from .contracts.router import Router
from .contracts.structs import (
    FillOrderType,
    ICLOBCancelArgs,
    ICLOBPostFillOrderArgs,
    ICLOBPostLimitOrderArgs,
    LimitOrderType,
    Settlement,
    Side,
)
from .contracts.utils import get_current_timestamp
from .info import MarketService
from .models import Market, Order, OrderSide, OrderType, TimeInForce, Trade

logger = logging.getLogger(__name__)


class ExecutionClient:
    """Client for executing orders on the GTE exchange."""

    def __init__(self, web3: Web3 | None = None, router_address: str | None = None):
        """
        Initialize the execution client.

        Args:
            web3: Web3 instance for on-chain interactions
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        self._clob_clients: dict[str, ICLOB] = {}
        self._router: Router | None = None
        self._market_info: MarketService | None = None

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

    def _map_order_params_to_contract_args(
        self,
        market: Market | Market,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float,
        time_in_force: TimeInForce,
    ) -> dict[str, Any]:
        """
        Map order parameters to contract arguments.

        Args:
            market: Market or Market object
            side: Order side
            order_type: Order type
            amount: Order amount
            price: Order price
            time_in_force: Time in force

        Returns:
            Dictionary with contract arguments
        """
        # Get market parameters
        base_decimals = getattr(market, "base_decimals", 18)
        tick_size_in_decimals = getattr(market, "tick_size_in_decimals", 6)
        base_atoms_per_lot = getattr(market, "base_atoms_per_lot", 1)

        # Map order side
        side_value = Side.BUY if side == OrderSide.BUY else Side.SELL

        # Convert amount to base lots
        amount_in_base_lots = int(amount * (10**base_decimals) / base_atoms_per_lot)

        # Convert price to ticks
        price_in_ticks = int(price * (10**tick_size_in_decimals))

        # Map time in force
        if order_type == OrderType.LIMIT:
            # Map time_in_force to LimitOrderType
            limit_type = LimitOrderType.GOOD_TILL_CANCELLED  # Default
            if time_in_force == TimeInForce.IOC:
                limit_type = LimitOrderType.IMMEDIATE_OR_CANCEL
            elif time_in_force == TimeInForce.FOK:
                limit_type = LimitOrderType.FILL_OR_KILL

            return {
                "amount_in_base_lots": amount_in_base_lots,
                "price_in_ticks": price_in_ticks,
                "side_value": side_value,
                "limit_type": limit_type,
            }
        else:  # Market order
            return {
                "amount_in_base_lots": amount_in_base_lots,
                "price_in_ticks": price_in_ticks,
                "side_value": side_value,
                "fill_type": FillOrderType.IMMEDIATE_OR_CANCEL,
            }

    async def create_order(
        self,
        market: Market | Market,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        sender_address: str | None = None,
        use_contract: bool = False,
        use_router: bool = True,
        **tx_kwargs,
    ) -> Order:
        """
        Create a new order.

        Args:
            market: Market object with details
            side: Order side
            order_type: Order type
            amount: Order amount
            price: Order price (required for limit orders)
            time_in_force: Time in force
            sender_address: Address to send transaction from (required for on-chain orders)
            use_contract: Whether to create the order on-chain using contracts
            use_router: Whether to use the router for creating orders (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Created order information or transaction data when using contracts

        Raises:
            ValueError: For missing required parameters or invalid input
        """
        logger.info(
            f"Creating {order_type.value} {side.value} order for {amount} at price {price}"
        )

        # Handle on-chain order creation via contract
        if use_contract:
            if not self._web3:
                raise ValueError("Web3 provider not configured. Cannot create on-chain orders.")

            if not sender_address:
                raise ValueError("sender_address is required for on-chain orders")

            if not price and order_type == OrderType.LIMIT:
                raise ValueError("Price is required for limit orders")

            if not price:
                raise ValueError("Price is required for on-chain orders")

            # Get contract address
            contract_address = getattr(market, "contract_address", None)
            if not contract_address:
                raise ValueError("Market has no contract address")

            # Get mapped contract parameters
            params = self._map_order_params_to_contract_args(
                market=market,
                side=side,
                order_type=order_type,
                amount=amount,
                price=price,
                time_in_force=time_in_force,
            )

            # Create the appropriate order based on type and use router or direct contract
            if order_type == OrderType.LIMIT:
                # Create limit order arguments
                limit_args = ICLOBPostLimitOrderArgs(
                    amountInBase=params["amount_in_base_lots"],
                    price=params["price_in_ticks"],
                    cancelTimestamp=0,
                    side=params["side_value"],
                    limitOrderType=params["limit_type"],
                    settlement=Settlement.INSTANT,
                )

                # Use router or direct CLOB contract
                if use_router and self._router:
                    return self._router.clob_post_limit_order(
                        clob_address=contract_address,
                        args=limit_args,
                        sender_address=sender_address,
                        **tx_kwargs,
                    )
                else:
                    # Use direct CLOB contract
                    clob = self._get_clob(contract_address)
                    return clob.post_limit_order(
                        args=limit_args, sender_address=sender_address, **tx_kwargs
                    )
            else:  # Market order
                # Create fill order arguments
                fill_args = ICLOBPostFillOrderArgs(
                    amountInBaseLots=params["amount_in_base_lots"],
                    priceInTicks=params["price_in_ticks"],
                    side=params["side_value"],
                    fillOrderType=params["fill_type"],
                    settlement=Settlement.INSTANT,
                )

                # Use router or direct CLOB contract
                if use_router and self._router:
                    return self._router.execute_clob_post_fill_order(
                        clob_address=contract_address,
                        args=fill_args,
                        sender_address=sender_address,
                        **tx_kwargs,
                    )
                else:
                    # Use direct CLOB contract
                    clob = self._get_clob(contract_address)
                    return clob.post_fill_order(
                        args=fill_args, sender_address=sender_address, **tx_kwargs
                    )
        else:
            # This is just a placeholder response for the REST API implementation
            # In a real implementation, we would call the API and get order details
            market_address = getattr(market, "address", str(market))

            return Order.from_api(
                {
                    "id": f"placeholder-{int(time.time())}",
                    "marketAddress": market_address,
                    "side": side.value,
                    "type": order_type.value,
                    "amount": amount,
                    "price": price,
                    "timeInForce": time_in_force.value,
                    "status": "open",
                    "filledAmount": 0.0,
                    "filledPrice": 0.0,
                    "createdAt": int(time.time() * 1000),
                }
            )

    def cancel_order(
        self,
        market: Market | Market,
        order_id: int,
        sender_address: str,
        use_router: bool = True,
        **tx_kwargs,
    ) -> TxParams:
        """
        Cancel an order.

        Args:
            market: Market object with details
            order_id: ID of the order to cancel
            sender_address: Address to send transaction from
            use_router: Whether to use the router for cancellation (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction data

        Raises:
            ValueError: If Web3 is not configured or parameters are invalid
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot cancel on-chain orders.")

        contract_address = getattr(market, "contract_address", None)
        if not contract_address:
            raise ValueError("Market has no contract address")

        # Create cancel arguments
        cancel_args = ICLOBCancelArgs(orderIds=[order_id], settlement=Settlement.INSTANT)

        # Use router or direct contract
        if use_router and self._router:
            return self._router.clob_cancel(
                clob_address=contract_address,
                args=cancel_args,
                sender_address=sender_address,
                **tx_kwargs,
            )
        else:
            clob = self._get_clob(contract_address)
            return clob.cancel(args=cancel_args, sender_address=sender_address, **tx_kwargs)

    # def modify_order(
    #     self,
    #     market: Market | Market,
    #     order_id: int,
    #     new_amount: float,
    #     sender_address: str,
    #     use_router: bool = True,
    #     **tx_kwargs,
    # ) -> dict[str, Any]:
    #     """
    #     Modify an existing order's amount (reduce only).
    #
    #     Args:
    #         market: Market object with details
    #         order_id: ID of the order to modify
    #         new_amount: New amount for the order (must be less than current)
    #         sender_address: Address to send transaction from
    #         use_router: Whether to use the router for modification (safer)
    #         **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)
    #
    #     Returns:
    #         Transaction data
    #
    #     Raises:
    #         ValueError: If Web3 is not configured or parameters are invalid
    #     """
    #     if not self._web3:
    #         raise ValueError("Web3 provider not configured. Cannot modify on-chain orders.")
    #
    #     contract_address = getattr(market, "contract_address", None)
    #     if not contract_address:
    #         raise ValueError("Market has no contract address")
    #
    #     # Convert amount to base lots
    #     base_decimals = getattr(market, "base_decimals", 18)
    #     base_atoms_per_lot = getattr(market, "base_atoms_per_lot", 1)
    #     amount_in_base_lots = int(new_amount * (10**base_decimals) / base_atoms_per_lot)
    #
    #     # Create reduce arguments
    #     reduce_args = ICLOBReduceArgs(
    #         orderId=order_id, amountInBaseLots=amount_in_base_lots, settlement=Settlement.INSTANT
    #     )
    #
    #     # Use direct contract - router doesn't support reduce
    #     clob = self._get_clob(contract_address)
    #     return clob.reduce(args=reduce_args, sender_address=sender_address, **tx_kwargs)

    async def get_user_orders(
        self,
        user_address: str,
        market_address: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Order]:
        """
        Fetch orders for a specific user.

        Args:
            user_address: Address of the user
            market_address: Optional market address to filter by
            status: Optional status to filter by (open, filled, cancelled)
            limit: Maximum number of orders to return
            offset: Offset for pagination

        Returns:
            List of user orders
        """
        # This would make a call to the API in a real implementation
        # For now we'll return a placeholder

        placeholder_orders = []
        for i in range(3):  # Create 3 placeholder orders
            order_id = f"order-{int(time.time())}-{i}"
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            order_type = OrderType.LIMIT
            status_val = "open" if i < 2 else "filled"

            placeholder_orders.append(
                Order.from_api(
                    {
                        "id": order_id,
                        "marketAddress": market_address or f"0x123456789abcdef{i}",
                        "side": side.value,
                        "type": order_type.value,
                        "amount": 1.0 + i,
                        "price": 100.0 * (1 + 0.01 * i),
                        "timeInForce": TimeInForce.GTC.value,
                        "status": status_val,
                        "filledAmount": 0.0 if status_val == "open" else 1.0 + i,
                        "filledPrice": 0.0 if status_val == "open" else 100.0 * (1 + 0.01 * i),
                        "createdAt": int(time.time() * 1000) - i * 60000,
                    }
                )
            )

        return placeholder_orders

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
        # This would make a call to the API in a real implementation
        # For now we'll return placeholders

        placeholder_trades = []
        for i in range(5):  # Create 5 placeholder trades
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL

            placeholder_trades.append(
                Trade.from_api(
                    {
                        "m": market_address or f"0x123456789abcdef{i}",
                        "timestamp": int(time.time() * 1000)
                        - i * 3600000,  # Each trade 1 hour apart
                        "price": 100.0 + i,
                        "size": 0.5 + 0.1 * i,
                        "side": side.value,
                        "transactionHash": f"0xabcdef1234567890{i}",
                        "maker": f"0xmaker{i}",
                        "taker": user_address,
                        "id": 1000 + i,
                    }
                )
            )

        return placeholder_trades

    async def get_order_book_snapshot(
        self, market: Market | Market, depth: int = 10
    ) -> dict[str, Any]:
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

        contract_address = getattr(market, "contract_address", None)
        if not contract_address:
            raise ValueError("Market has no contract address")

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
            current_bid = clob.get_next_smallest_tick(current_bid, Side.BUY)

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
            current_ask = clob.get_next_biggest_price(current_ask, Side.SELL)

        return {"bids": bids, "asks": asks, "timestamp": get_current_timestamp()}

    async def get_user_balances(
        self, user_address: str, market: Market | Market
    ) -> dict[str, int]:
        """
        Get user token balances in the CLOB.

        Args:
            user_address: Address of the user
            market: Market object with details

        Returns:
            Dictionary with base and quote token balances

        Raises:
            ValueError: If Web3 is not configured or market has no contract address
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot fetch on-chain balances.")

        contract_address = getattr(market, "contract_address", None)
        if not contract_address:
            raise ValueError("Market has no contract address")

        clob = self._get_clob(contract_address)

        base_balance = clob.get_base_token_amount(user_address)
        quote_balance = clob.get_quote_token_amount(user_address)

        return {"baseBalance": base_balance, "quoteBalance": quote_balance}
