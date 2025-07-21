"""Order execution functionality for the GTE client."""

import logging
from typing import Optional, Tuple, Any, List

from eth_typing import ChecksumAddress
from eth_account.signers.local import LocalAccount
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.chain.events import OrderAmendedEvent, OrderCanceledEvent, FillOrderProcessedEvent, LimitOrderProcessedEvent, parse_fill_order_processed, parse_limit_order_processed, parse_deposit, parse_order_canceled, parse_withdraw, parse_order_amended
from gte_py.api.chain.structs import ICLOBAmendArgs, OrderSide, Settlement, LimitOrderType, FillOrderType, OperatorRole, ICLOBPostFillOrderArgs, ICLOBPostLimitOrderArgs, ICLOBCancelArgs
from gte_py.api.chain.utils import TypedContractFunction, BoundedNonceTxScheduler
from gte_py.models import Market, Order, OrderStatus, TimeInForce
from gte_py.api.chain.erc20 import ERC20

logger = logging.getLogger(__name__)


class ExecutionClient:
    """Client for executing orders and managing deposits/withdrawals on the GTE exchange."""

    def __init__(
            self,
            web3: AsyncWeb3,
            account: LocalAccount,
            gte_router_address: ChecksumAddress,
            weth_address: ChecksumAddress,
            clob_manager_address: ChecksumAddress,
    ):
        """
        Initialize the execution client.

        Args:
            web3: AsyncWeb3 instance for on-chain interactions
            main_account: Address to send transactions from
            gte_router_address: Address of the GTE router
        """
        self._web3 = web3
        self._account = account
        self._gte_router_address = gte_router_address
        self._clob_client = CLOBClient(web3, gte_router_address)
        self._token_client = TokenClient(web3)
        self._weth_address = weth_address
        self._clob_factory = None
        self._clob_manager_address = clob_manager_address
        self._scheduler = BoundedNonceTxScheduler(
            web3=self._web3,
            account=self._account,
        )
        
        # Cache for approved tokens to avoid repeated approval checks
        self._approved_tokens: set[ChecksumAddress] = set()
        
        # Maximum approval amount (2^256 - 1)
        self._max_approval = 2**256 - 1
        
        # Cache for price limits to avoid repeated network calls
        self._price_cache: dict[tuple[ChecksumAddress, OrderSide, float], tuple[int, float]] = {}

    async def init(self):
        """Initialize the CLOB client."""
        await self._clob_client.init()
        self._clob_factory = self._clob_client.get_factory_address()
        await self._scheduler.start()

    # ================= DEPOSIT/WITHDRAW OPERATIONS =================
    
    async def _ensure_approval(
        self,
        amount: int,
        token: ERC20,
        **kwargs,
    ):
        """
        Ensure the correct token is approved for the required amount.
        Uses infinite approvals (2^256 - 1) and caches approved tokens.
        """ 
        token_address = token.address
        
        # Check if we've already approved this token
        if token_address in self._approved_tokens:
            return
        
        # Need to approve - use infinite approval
        _ = await self._scheduler.send_wait(token.approve(spender=self._clob_manager_address, amount=self._max_approval, **kwargs))
        
        # Cache the token as approved
        self._approved_tokens.add(token_address)

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
        
        # time the approval
        await self._ensure_approval(amount, token, **kwargs)

        tx = clob_factory.deposit(
            account=self._account.address,
            token=token_address,
            amount=amount,
            from_operator=False,
            **kwargs,
        ).with_event(clob_factory.contract.events.Deposit(), parse_deposit)
        return await self._scheduler.send_wait(tx)

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

        tx = clob_factory.withdraw(
            account=self._account.address, token=token_address, amount=amount, to_operator=False, **kwargs
        ).with_event(clob_factory.contract.events.Withdraw(), parse_withdraw)
        
        return await self._scheduler.send_wait(tx)

    async def get_token_balance(self, token_address: ChecksumAddress) -> int:
        """
        Get the balance of a token in the wallet.
        """
        return await self._token_client.get_erc20(token_address).balance_of(self._account.address)
    
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
        weth = self._token_client.get_weth(self._weth_address)
        tx = weth.deposit_eth(amount, **kwargs).with_event(weth.contract.events.Deposit())
        return await self._scheduler.send_wait(tx)

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
        weth = self._token_client.get_weth(self._weth_address)
        tx = weth.withdraw_eth(amount, **kwargs).with_event(weth.contract.events.Withdrawal())
        return await self._scheduler.send_wait(tx)

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
        logger.info(f"Approving operator {operator_address} for account {self._account.address} with roles {roles}")

        # The clob_factory is actually the clob_manager
        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        return await self._scheduler.send_wait(clob_factory.approve_operator(
            operator=operator_address,
            roles=roles_int,
            **kwargs
        ))

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
        logger.info(f"Disapproving operator {operator_address} for account {self._account.address} with roles {roles}")
        
        # The clob_factory is actually the clob_manager
        clob_factory = self._clob_client.clob_factory
        if not clob_factory:
            await self.init()
            clob_factory = self._clob_client.clob_factory
            assert clob_factory is not None, "CLOB factory should be initialized"

        return await self._scheduler.send_wait(clob_factory.disapprove_operator(
            operator=operator_address,
            roles=roles_int,
            **kwargs
        ))

    # ================= ROUTER-BASED ORDER OPERATIONS =================
    # These methods use the router contract for consistency, but note that router calls
    # don't emit events directly - they route to CLOB contracts which emit the events.

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
        Place a limit order using the router contract.
        
        Note: Router calls don't emit events directly, but route to CLOB contracts.
        Use place_limit_order() if you need event-based order tracking.

        Args:
            market_address: Address of the market/CLOB contract
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
        router = self._clob_client.get_router()
        clob = self._clob_client.get_clob(market_address)

        # For IOC and FOK orders, we use the fill order API
        if time_in_force in [TimeInForce.IOC, TimeInForce.FOK]:
            if time_in_force == TimeInForce.IOC:
                fill_order_type = FillOrderType.IMMEDIATE_OR_CANCEL
            elif time_in_force == TimeInForce.FOK:
                fill_order_type = FillOrderType.FILL_OR_KILL
            else:
                raise ValueError(f"Unknown time_in_force: {time_in_force}")

            # Create post fill order args using NamedTuple
            args = ICLOBPostFillOrderArgs(
                amount,
                price,
                side.value,
                True,  # amountIsBase - since amount is in base tokens
                fill_order_type.value,
                settlement.value,
            )

            # Return the router transaction
            return router.clob_post_fill_order(clob=market_address, args=args, **kwargs).with_event(clob.contract.events.FillOrderProcessed(), parse_fill_order_processed)
        else:
            if time_in_force == TimeInForce.GTC:
                tif = LimitOrderType.GOOD_TILL_CANCELLED
            elif time_in_force == TimeInForce.POST_ONLY:
                tif = LimitOrderType.POST_ONLY
            else:
                raise ValueError(f"Unknown time_in_force: {time_in_force}")
            
            # Create post limit order args using NamedTuple
            args = ICLOBPostLimitOrderArgs(
                amount,
                price,
                0,  # cancelTimestamp - no expiration
                side.value,
                client_order_id,
                tif.value,
                settlement.value,
            )

            # Return the router transaction
            return router.clob_post_limit_order(clob=market_address, args=args, **kwargs).with_event(clob.contract.events.LimitOrderProcessed(), parse_limit_order_processed)

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
    ) -> LimitOrderProcessedEvent | FillOrderProcessedEvent:
        """
        Place a limit order using the router contract.
        
        Note: This method returns a transaction receipt since router calls don't emit events.
        Use place_limit_order_with_events() if you need event-based order tracking.

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
            Transaction receipt of the placed order
        """
        amount = int(market.base.convert_quantity_to_amount(amount) if not amount_is_raw else amount)
        price = int(market.quote.convert_quantity_to_amount(price) if not price_is_raw else price)
        
        token, approval_amount = self._compute_approval_requirements(market, side, amount, True, price)
        await self._ensure_approval(
            amount=approval_amount,
            token=token,
            **kwargs,
        )
        
        clob = self._clob_client.get_clob(market.address)
        
        tx = self.place_limit_order_tx(
            market_address=market.address,
            side=side,
            amount=amount,
            price=price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            settlement=settlement,
            **kwargs,
        ).with_event(clob.contract.events.LimitOrderProcessed(), parse_limit_order_processed)
        
        # Send the transaction and return the receipt
        return await self._scheduler.send_wait(tx)

    def place_market_order_tx(
            self,
            market: Market,
            side: OrderSide,
            amount: int,
            price_limit: int,
            amount_is_base: bool = True,
            **kwargs,
    ) -> TypedContractFunction[Any]:
        """
        Place a market order using the router contract.

        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in base tokens if amount_is_base is True, otherwise in quote tokens
            amount_is_base: Whether the amount is in base tokens
            price_limit: Price limit for the order
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        router = self._clob_client.get_router()

        # Create post fill order args using named tuple
        args = ICLOBPostFillOrderArgs(
            amount,
            price_limit,
            side.value,
            amount_is_base,
            FillOrderType.IMMEDIATE_OR_CANCEL.value,
            Settlement.INSTANT.value,
        )

        # Return the router transaction
        return router.clob_post_fill_order(clob=market.address, args=args, **kwargs)

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
    ) -> FillOrderProcessedEvent:
        """
        Place a market order using the router contract.

        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in base tokens if amount_is_base is True, otherwise in quote tokens
            amount_is_base: Whether the amount is in base tokens
            slippage: Slippage percentage for price limit
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt of the placed order
        """
        amount = self._adjust_amount(market, amount, amount_is_raw, amount_is_base)
        price_limit = await self._get_price_limit(market, side, slippage)
        token, approval_amount = self._compute_approval_requirements(market, side, amount, amount_is_base, price_limit)
        
        await self._ensure_approval(
            amount=approval_amount,
            token=token,
            **kwargs,
        )
        
        clob = self._clob_client.get_clob(market.address)
        
        tx = self.place_market_order_tx(
            market=market,
            side=side,
            amount=amount,
            price_limit=price_limit,
            amount_is_base=amount_is_base,
            **kwargs,
        ).with_event(clob.contract.events.FillOrderProcessed(), parse_fill_order_processed)
        return await self._scheduler.send_wait(tx)
    
    async def amend_order_tx(
            self,
            market: Market,
            order_id: int,
            amount_in_base: int,
            price_in_ticks: int,
            side: OrderSide,
            **kwargs,
    ) -> TypedContractFunction[Any]:
        """
        Create an amend order transaction.

        Args:
            market: Market the order is on
            order_id: ID of the order to amend
            amount_in_base: New amount for the order in base tokens
            price_in_ticks: New price for the order in ticks
            side: Order side
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Get the CLOB contract
        clob = self._clob_client.get_clob(market.address)

        # Create amend args
        args = ICLOBAmendArgs(
            orderId=order_id,
            amountInBase=amount_in_base,
            price=price_in_ticks,
            cancelTimestamp=0,  # No expiration
            side=side.value,
            limitOrderType=LimitOrderType.POST_ONLY.value,
            settlement=Settlement.INSTANT.value,
        )

        # Return the transaction
        return clob.amend(account=self._account.address, args=args, **kwargs)

    async def amend_order(
            self,
            market: Market,
            order_id: int,
            new_amount: Optional[int] = None,
            new_price: Optional[int] = None,
            **kwargs,
    ) -> OrderAmendedEvent:
        """
        Amend an existing order.

        Args:
            market: Market the order is on
            order_id: ID of the order to amend
            new_amount: New amount for the order (None to keep current)
            new_price: New price for the order (None to keep current)
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt from the amend operation
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
        
        # Ensure approval
        token, approval_amount = self._compute_approval_requirements(market, side, amount_in_base, True, price_in_ticks)
        await self._ensure_approval(
            amount=approval_amount,
            token=token,
            **kwargs,
        )

        # Create and execute transaction
        tx = await self.amend_order_tx(
            market=market, 
            order_id=order_id, 
            amount_in_base=amount_in_base,
            price_in_ticks=price_in_ticks,
            side=side,
            **kwargs
        )
        tx = tx.with_event(clob.contract.events.OrderAmended(), parse_order_amended)
        return await self._scheduler.send_wait(tx)

    def cancel_order_tx(
            self, market: Market, order_id: int, **kwargs
    ) -> TypedContractFunction[Any]:
        """
        Cancel an existing order using the router contract.

        Args:
            market: Market the order is on
            order_id: ID of the order to cancel
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        router = self._clob_client.get_router()

        # Create cancel args
        args = ICLOBCancelArgs(
            [order_id], 
            Settlement.INSTANT.value
        )

        # Return the router transaction
        return router.clob_cancel(clob=market.address, args=args, isUnwrapping=False, **kwargs)

    async def cancel_order(self, market: Market, order_id: int, **kwargs) -> OrderCanceledEvent:
        """
        Cancel an existing order using the router contract.

        Args:
            market: Market the order is on
            order_id: ID of the order to cancel
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt of the cancellation
        """
        clob = self._clob_client.get_clob(market.address)
        tx = self.cancel_order_tx(market=market, order_id=order_id, **kwargs).with_event(clob.contract.events.OrderCanceled(), parse_order_canceled)
        return await self._scheduler.send_wait(tx)

    async def cancel_all_orders(self, market: Market, open_orders: List[Order], **kwargs) -> List[OrderCanceledEvent]:
        """
        Cancel all orders for the current user on a specific market using the router.

        Args:
            market: Market to cancel orders on
            open_orders: List of open orders to cancel
            **kwargs: Additional transaction parameters
            
        Returns:
            List of transaction hashes
        """
        cancelled_orders = []
        for order in open_orders:
            if order.status == OrderStatus.OPEN:
                await self.cancel_order(market, order.order_id, **kwargs)
            cancelled_orders.append(order)
        return cancelled_orders

    def clear_approval_cache(self):
        """Clear the approval cache. Use this if you want to force re-checking approvals."""
        self._approved_tokens.clear()
        logger.info("Approval cache cleared")

    def get_approved_tokens(self) -> set[ChecksumAddress]:
        """Get the set of tokens that are cached as approved."""
        return self._approved_tokens.copy()

    def is_token_approved(self, token_address: ChecksumAddress) -> bool:
        """Check if a token is in the approval cache."""
        return token_address in self._approved_tokens

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
        account = account if account else self._account.address
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
