"""Spot order execution functionality for the GTE client."""

import logging
from typing import Optional, Tuple, Awaitable, Any, List

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.chain.events import OrderCanceledEvent, FillOrderProcessedEvent, LimitOrderProcessedEvent
from gte_py.api.chain.structs import OrderSide, Settlement, LimitOrderType, FillOrderType, OperatorRole
from gte_py.api.chain.utils import TypedContractFunction
from gte_py.models import Market, Order, OrderStatus, TimeInForce
from gte_py.api.chain.erc20 import ERC20

logger = logging.getLogger(__name__)


class SpotExecutionClient:
    """Client for executing spot orders and managing deposits/withdrawals on the GTE exchange."""

    def __init__(self, web3: AsyncWeb3, main_account: ChecksumAddress, gte_router_address: ChecksumAddress, weth_address: ChecksumAddress):
        self._web3 = web3
        self.main_account = main_account
        self._gte_router_address = gte_router_address
        self._clob_client = CLOBClient(web3, gte_router_address)
        self._token_client = TokenClient(web3)
        self._weth_address = weth_address
        self._clob_factory = None

    async def init(self):
        await self._clob_client.init()
        self._clob_factory = self._clob_client.get_factory_address()

    # ================= DEPOSIT/WITHDRAW OPERATIONS =================
    
    async def _ensure_approval(
        self,
        amount: int,
        token: ERC20,
        **kwargs,
    ):
        """
        Ensure the correct token is approved for the required amount. For market orders, calculates price limit using orderbook.
        Returns the amount that was approved.
        """
        if not self._clob_factory:
            await self.init()
            assert self._clob_factory is not None, "CLOB factory should be initialized"
            
        allowance = await token.allowance(owner=self.main_account, spender=self._clob_factory)
        if allowance < amount:
            _ = await token.approve(spender=self._clob_factory, amount=amount, **kwargs).send_wait()

    def _adjust_amount(self, market: Market, amount, amount_is_raw: bool, amount_is_base: bool) -> int:
        if amount_is_raw:
            return amount
        if amount_is_base:
            return market.base.convert_quantity_to_amount(amount)
        return market.quote.convert_quantity_to_amount(amount)

    async def deposit(
            self, token_address: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ):
        """
        Deposit tokens to the exchange for trading.

        Args:
            token_address: Address of token to deposit
            amount: Amount to deposit in base units
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the deposit operation
        """
        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        token = self._token_client.get_erc20(token_address)
        
        await token.approve(spender=self._clob_client.get_factory_address(), amount=amount, **kwargs).send_wait()

        # Then deposit the tokens
        return await clob_factory.deposit(
            account=self.main_account,
            token=token_address,
            amount=amount,
            from_operator=False,
            **kwargs,
        ).send_wait()

    async def withdraw(
            self, token_address: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ):
        """
        Withdraw tokens from the exchange.

        Args:
            token_address: Address of token to withdraw
            amount: Amount to withdraw
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the withdrawal transaction
        """
        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        # Withdraw the tokens
        return await clob_factory.withdraw(
            account=self.main_account, token=token_address, amount=amount, to_operator=False, **kwargs
        ).send_wait()
        
    async def get_token_balance(self, token_address: ChecksumAddress) -> int:
        """
        Get the balance of a token in the wallet.
        """
        return await self._token_client.get_erc20(token_address).balance_of(self.main_account)
    
    async def get_weth_balance(self) -> int:
        """
        Get the balance of WETH in the wallet.
        """
        return await self.get_token_balance(self._weth_address)

    async def wrap_eth(
            self, amount: int, **kwargs: Unpack[TxParams]
    ):
        """
        Wrap ETH to WETH.

        Args:
            amount: Amount of ETH to wrap
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the wrap operation
        """
        return await self._token_client.get_weth(self._weth_address).deposit_eth(amount, **kwargs).send_wait()

    async def unwrap_eth(
            self, amount: int, **kwargs: Unpack[TxParams]
    ):
        """
        Unwrap WETH to ETH.

        Args:
            amount: Amount of WETH to unwrap
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the unwrap operation
        """
        return await self._token_client.get_weth(self._weth_address).withdraw_eth(amount, **kwargs).send_wait()

    # ================= APPROVE OPERATIONS =================

    def _encode_rules(self, roles: list[OperatorRole]) -> int:
        """Encode operator roles into an integer."""
        roles_int = 0
        for role in roles:
            roles_int |= role.value
        return roles_int

    async def approve_operator(self, operator_address: ChecksumAddress,
                               roles: list[OperatorRole] = [],
                               unsafe_withdraw: bool = False,
                               unsafe_launchpad_fill: bool = False,
                               **kwargs: Unpack[TxParams]):
        """
        Approve an operator to act on behalf of the account.

        Args:
            operator_address: Address of the operator to approve
            roles: List of roles to assign to the operator
            unsafe_withdraw: Whether to allow unsafe withdrawals
            unsafe_launchpad_fill: Whether to allow unsafe launchpad fills
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the approve_operator operation
        """
        if OperatorRole.WITHDRAW in roles and not unsafe_withdraw:
            raise ValueError("Unsafe withdraw must be enabled to approve withdraw role")
        if OperatorRole.LAUNCHPAD_FILL in roles and not unsafe_launchpad_fill:
            raise ValueError("Unsafe launchpad fill must be enabled to approve launchpad fill role")
        
        roles_int = self._encode_rules(roles)
        logger.info(f"Approving operator {operator_address} for account {self.main_account} with roles {roles}")

        # The clob_factory is actually the clob_manager
        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        return await clob_factory.approve_operator(
            operator=operator_address,
            roles=roles_int,
            **kwargs
        ).send_wait()

    async def disapprove_operator(self, operator_address: ChecksumAddress,
                                  roles: list[OperatorRole],
                                  **kwargs: Unpack[TxParams]):
        """
        Disapprove an operator from acting on behalf of the account.

        Args:
            operator_address: Address of the operator to disapprove
            roles: List of roles to disapprove
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the disapprove_operator operation
        """
        roles_int = self._encode_rules(roles)
        logger.info(f"Disapproving operator {operator_address} for account {self.main_account} with roles {roles}")
        
        # The clob_factory is actually the clob_manager
        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        return await clob_factory.disapprove_operator(
            operator=operator_address,
            roles=roles_int,
            **kwargs
        ).send_wait()

    # ================= ORDER OPERATIONS =================

    def place_limit_order_tx(
            self,
            market_address: ChecksumAddress,
            side: OrderSide,
            amount: int,
            price: int,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            settlement: Settlement = Settlement.INSTANT,
            **kwargs,
    ) -> TypedContractFunction[Any]:
        """
        Place a limit order on the CLOB.

        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in base tokens
            price: Order price
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Optional client order ID for tracking
            settlement: Settlement type (default is INSTANT)
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._clob_client.get_clob(market_address)

        contract_side = side

        # For IOC and FOK orders, we use the fill order API which has different behavior
        if time_in_force in [TimeInForce.IOC, TimeInForce.FOK]:
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
                settlement=settlement,
            )

            # Return the transaction
            return clob.post_fill_order(account=self.main_account, args=args, **kwargs)
        else:
            if time_in_force == TimeInForce.GTC:
                tif = LimitOrderType.GOOD_TILL_CANCELLED
            elif time_in_force == TimeInForce.POST_ONLY:
                tif = LimitOrderType.POST_ONLY
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
                settlement=settlement,
            )

            # Return the transaction
            return clob.post_limit_order(account=self.main_account, args=args, **kwargs)

    async def place_limit_order(
            self,
            market: Market,
            side: OrderSide,
            amount: int | float,
            price: int | float,
            amount_is_raw: bool = True,
            price_is_raw: bool = True,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            settlement: Settlement = Settlement.INSTANT,
            **kwargs: Unpack[TxParams],
    ) -> Order:
        """
        Place a limit order on the CLOB.

        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount
            amount_is_raw: Whether the amount is in raw units
            price: Order price
            price_is_raw: Whether the price is in raw units
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Optional client order ID for tracking
            **kwargs: Additional transaction parameters

        Returns:
            Order object representing the placed order
        """
        amount = int(market.base.convert_quantity_to_amount(amount) if not amount_is_raw else amount)
        price = int(market.quote.convert_quantity_to_amount(price) if not price_is_raw else price)
        
        token, approval_amount = self._compute_approval_requirements(market, side, amount, True, price)
        await self._ensure_approval(
            amount=approval_amount,
            token=token,
            **kwargs,
        )
        
        tx = self.place_limit_order_tx(
            market_address=market.address,
            side=side,
            amount=amount,
            price=price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            settlement=settlement,
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
                if log is None:
                    raise ValueError("Unexpected event: None")
                raise ValueError(f"Unknown event type: {log.event_name}")
            return order

        return await task()

    async def place_market_order_tx(
            self,
            market: Market,
            side: OrderSide,
            amount: int,
            price_limit: int,
            amount_is_base: bool = True,
            slippage: float = 0.01,
            **kwargs,
    ) -> TypedContractFunction[Any]:
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
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._clob_client.get_clob(market.address)

        # Convert model types to contract types
        contract_side = OrderSide.BUY if side == OrderSide.BUY else OrderSide.SELL

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

    async def _get_price_limit(self, market: Market, side: OrderSide, slippage: float = 0.01) -> int:
        """
        Get the price limit for a market order with slippage applied.
        """
        clob = self._clob_client.get_clob(market.address)
        highest_bid, lowest_ask = await clob.get_tob()
        
        if side == OrderSide.BUY:
            # For BUY orders, use lowest ask with positive slippage
            return int(lowest_ask * (1 + slippage))
        else:
            # For SELL orders, use highest bid with negative slippage
            return int(highest_bid * (1 - slippage))
    
    def _compute_approval_requirements(
            self,
            market: Market,
            side: OrderSide,
            amount: int,
            amount_is_base: bool,
            price_limit: int,
        ):
            if side == OrderSide.BUY:
                token = self._token_client.get_erc20(market.quote.address)
                if amount_is_base:
                    # amount is already in base tokens, so we approve the quote token for the amount * price limit
                    required = amount * market.quote.convert_amount_to_quantity(price_limit)
                else:
                    # amount is in quote tokens, so we approve the quote token for the amount
                    required = amount
            else:
                token = self._token_client.get_erc20(market.base.address)
                if amount_is_base:
                    # amount is in base tokens, so we approve the base token for the amount
                    required = amount
                else:
                    # amount is in quote tokens, so we approve the base token for the amount / price limit
                    required = amount // market.quote.convert_amount_to_quantity(price_limit)
            return token, int(required)

    
    async def place_market_order(
            self,
            market: Market,
            side: OrderSide,
            amount: int | float,
            amount_is_raw: bool = True,
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
        amount = self._adjust_amount(market, amount, amount_is_raw, amount_is_base)
        
        price_limit = await self._get_price_limit(market, side, slippage)
        
        token, approval_amount = self._compute_approval_requirements(market, side, amount, amount_is_base, price_limit)
        
        await self._ensure_approval(
            amount=approval_amount,
            token=token,
            **kwargs,
        )
        
        tx = await self.place_market_order_tx(
            market=market,
            side=side,
            amount=amount,
            price_limit=price_limit,
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
    ) -> TypedContractFunction[Any]:
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
        clob = self._clob_client.get_clob(market.address)

        # Get the current order
        order = await clob.get_order(order_id)

        # Extract order details
        side = order.side
        current_amount = order.amount
        current_price = order.price

        amount_in_base = new_amount or current_amount
        price_in_ticks = new_price if new_price is not None else current_price
        
        # ensure approval
        token, approval_amount = self._compute_approval_requirements(market, side, amount_in_base, True, price_in_ticks)
        await self._ensure_approval(
            amount=approval_amount,
            token=token,
            **kwargs,
        )

        # Create amend args
        args = clob.create_amend_args(
            order_id=order_id,
            amount_in_base=amount_in_base,
            price=price_in_ticks,
            side=side,
            cancel_timestamp=0,  # No expiration
            limit_order_type=LimitOrderType.POST_ONLY,
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
        """
        Amend an existing order.

        Args:
            market: Market the order is on
            order_id: ID of the order to amend
            new_amount: New amount for the order (None to keep current)
            new_price: New price for the order (None to keep current)
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the amend operation
        """
        tx = await self.amend_order_tx(
            market=market, order_id=order_id, new_amount=new_amount, new_price=new_price, **kwargs
        )
        return await tx.send_wait()

    async def cancel_order_tx(
            self, market: Market, order_id: int, **kwargs
    ) -> TypedContractFunction[OrderCanceledEvent]:
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
        clob = self._clob_client.get_clob(market.address)

        # Create cancel args
        args = clob.create_cancel_args(order_ids=[order_id], settlement=Settlement.INSTANT)

        # Return the transaction
        return clob.cancel(account=self.main_account, args=args, **kwargs)

    async def cancel_order(self, market: Market, order_id: int, **kwargs):
        """
        Cancel an existing order.

        Args:
            market: Market the order is on
            order_id: ID of the order to cancel
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the cancel operation
        """
        tx = await self.cancel_order_tx(market=market, order_id=order_id, **kwargs)
        return await tx.send_wait()

    async def cancel_all_orders(self, market: Market, open_orders: List[Order], **kwargs):
        """
        Cancel all orders for the current user on a specific market.

        Args:
            market: Market to cancel orders on
            open_orders: List of open orders to cancel
            **kwargs: Additional transaction parameters
        """
        for order in open_orders:
            if order.status != OrderStatus.OPEN:
                continue
            await self.cancel_order(market, order.order_id, **kwargs)

    # ================= UTILITY OPERATIONS =================

    async def get_balance(
            self, token_address: ChecksumAddress, account: ChecksumAddress | None = None
    ) -> Tuple[float, float]:
        """
        Get token balance for an account both on-chain and in the exchange.

        Args:
            token_address: Address of token to check
            account: Account to check (defaults to sender address)

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """
        account = account if account else self.main_account
        token = self._token_client.get_erc20(token_address)

        # Get wallet balance
        wallet_balance_raw = await token.balance_of(account)
        wallet_balance = await token.convert_amount_to_quantity(wallet_balance_raw)

        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        # Get exchange balance
        exchange_balance_raw = await clob_factory.get_account_balance(
            account, token_address
        )
        exchange_balance = await token.convert_amount_to_quantity(exchange_balance_raw)

        return wallet_balance, exchange_balance
