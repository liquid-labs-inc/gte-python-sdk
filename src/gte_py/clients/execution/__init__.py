"""Order execution functionality for the GTE client."""

import logging
from typing import Optional, Tuple, Any, List
import time
from decimal import Decimal

from eth_typing import ChecksumAddress
from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams, Wei

from gte_py.clients.info import InfoClient
from gte_py.api.chain.chain_client import ChainClient
from gte_py.api.chain.events import OrderAmendedEvent, OrderCanceledEvent, FillOrderProcessedEvent, LimitOrderProcessedEvent
from gte_py.api.chain.structs import AmendArgs, OrderSide, Settlement, LimitOrderType, FillOrderType, OperatorRole, PostFillOrderArgs, PostLimitOrderArgs, CancelArgs
from gte_py.api.chain.utils import TypedContractFunction, BoundedNonceTxScheduler
from gte_py.models import Market, Order, OrderStatus, TimeInForce, Token
from gte_py.api.chain.erc20 import Erc20

logger = logging.getLogger(__name__)


class ExecutionClient:
    """Client for executing orders and managing deposits/withdrawals on the GTE exchange."""

    def __init__(
            self,
            web3: AsyncWeb3,
            account: LocalAccount,
            gte_router_address: ChecksumAddress,
            info: InfoClient,
    ):
        """
        Initialize the execution client.

        Args:
            web3: AsyncWeb3 instance for on-chain interactions
            account: Address to send transactions from
            gte_router_address: Address of the GTE router
            clob_manager_address: Address of the CLOB manager
        """
        self._web3 = web3
        self._account = account
        self._chain_client = ChainClient(web3, gte_router_address)
        self._scheduler = BoundedNonceTxScheduler(
            web3=self._web3,
            account=self._account,
        )
        self._info = info
        
        # Cache for approved clob tokens
        self._approved_clob_tokens: set[ChecksumAddress] = set()
        
        # Cache for approved swap tokens
        self._approved_swap_tokens: set[ChecksumAddress] = set()
        
        # Cache for approved launchpad tokens
        self._approved_launchpad_tokens: set[ChecksumAddress] = set()
        
        # TOB cache for market order optimization
        self._tob_cache: dict[ChecksumAddress, tuple[Decimal, Decimal]] = {}  # market -> (bid, ask)
        self._tob_subscriptions: set[ChecksumAddress] = set()
        
        # Maximum approval amount (2^256 - 1)
        self._max_approval = 2**256 - 1

    async def init(self):
        """Initialize the chain client."""
        await self._chain_client.init()
        await self._scheduler.start()

    async def close(self):
        """Clean up resources and unsubscribe from all WebSocket subscriptions."""
        # Unsubscribe from all TOB subscriptions
        for market_address in list(self._tob_subscriptions):
            try:
                await self._info.unsubscribe_orderbook(market_address, limit=1)
                logger.debug(f"Unsubscribed from TOB updates for {market_address}")
            except Exception as e:
                logger.warning(f"Error unsubscribing from {market_address}: {e}")
        
        # Stop the transaction scheduler
        await self._scheduler.stop()
        
        # Clear caches
        self._tob_cache.clear()
        self._tob_subscriptions.clear()
        
        logger.info("ExecutionClient cleanup completed")

    # ================= DEPOSIT/WITHDRAW OPERATIONS =================
    
    async def _ensure_approval(
        self,
        token: Erc20,
        **kwargs,
    ):
        """
        Ensure the correct token is approved for the required amount.
        Uses infinite approvals (2^256 - 1) and caches approved tokens.
        """ 
        token_address = token.address
        
        # Check if we've already approved this token
        if token_address in self._approved_clob_tokens:
            return
        
        # check if allowance is already set
        allowance = await token.allowance(owner=self._account.address, spender=self._chain_client.clob_manager_address)
        if allowance >= self._max_approval // 2:
            self._approved_clob_tokens.add(token_address)
            return
        
        # Need to approve - use infinite approval
        _ = await self._scheduler.send(token.approve(spender=self._chain_client.clob_manager_address, value=self._max_approval, **kwargs))
        
        # Cache the token as approved
        self._approved_clob_tokens.add(token_address)

    async def _ensure_swap_approval(
        self,
        token: Erc20,
        **kwargs,
    ):
        """
        Ensure the token is approved for swap operations.
        Uses infinite approvals (2^256 - 1) and caches approved tokens.
        """ 
        token_address = token.address
        
        # Check if we've already approved this token for swaps
        if token_address in self._approved_swap_tokens:
            return
        
        # check if allowance is already set
        allowance = await token.allowance(owner=self._account.address, spender=self._chain_client.univ2_router_address)
        if allowance >= self._max_approval // 2:
            self._approved_swap_tokens.add(token_address)
            return
        
        # Need to approve - use infinite approval
        _ = await self._scheduler.send(token.approve(spender=self._chain_client.univ2_router_address, value=self._max_approval, **kwargs))
        
        # Cache the token as approved for swaps
        self._approved_swap_tokens.add(token_address)

    # ================= LAUNCHPAD OPERATIONS =================
    
    async def _ensure_launchpad_approval(
        self,
        token: Erc20,
        **kwargs,
    ):
        """
        Ensure the token is approved for launchpad operations.
        Uses infinite approvals (2^256 - 1) and caches approved tokens.
        """ 
        token_address = token.address
        
        # Check if we've already approved this token for launchpad
        if token_address in self._approved_launchpad_tokens:
            return
        
        # check if allowance is already set
        allowance = await token.allowance(owner=self._account.address, spender=self._chain_client.launchpad_address)
        if allowance >= self._max_approval // 2:
            self._approved_launchpad_tokens.add(token_address)
            return
        
        # Standard DeFi pattern: approve the launchpad contract to spend this token
        # This allows launchpad.transferFrom(user, launchpad, amount) to work
        _ = await self._scheduler.send(token.approve(
            spender=self._chain_client.launchpad_address, 
            value=self._max_approval, 
            **kwargs
        ))
        
        # Cache the token as approved
        self._approved_launchpad_tokens.add(token_address)
        
        logger.debug(f"Approved {token_address} for launchpad spending by {self._chain_client.launchpad_address}")

    async def launchpad_buy_exact_quote(
        self,
        launch_token: Token,
        quote_token: Token,
        quote_amount_in: Decimal,
        slippage_tolerance: float = 0.01,
        **kwargs: Unpack[TxParams],
    ):
        """
        Buy launch tokens by spending an exact amount of quote tokens.
        
        Args:
            launch_token: Launch token to buy
            quote_token: Quote token to spend
            quote_amount_in: Exact amount of quote tokens to spend (in decimal units)
            slippage_tolerance: Slippage tolerance (0.01 = 1%)
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the buy operation
        """
        # Convert decimal amount to atomic units
        quote_amount_atomic = quote_token.convert_quantity_to_amount(quote_amount_in)
        
        # Get quote for how much base we'll receive
        expected_base_out = await self._chain_client.launchpad.quote_base_for_quote(
            token=launch_token.address,
            quote_amount=quote_amount_atomic,
            is_buy=True
        )
        
        # Apply slippage to minimum base amount out
        min_base_out = int(expected_base_out * (1 - slippage_tolerance))
        
        # Ensure approval for quote token
        quote_token_contract = self._chain_client.get_erc20(quote_token.address)
        await self._ensure_launchpad_approval(
            token=quote_token_contract,
            **kwargs,
        )
        
        logger.info(f"Buying {launch_token.symbol} with exactly {quote_amount_in} {quote_token.symbol}")

        tx = self._chain_client.launchpad.buy(
            account=self._account.address,
            token=launch_token.address,
            recipient=self._account.address,
            amount_out_base=min_base_out,
            max_amount_in_quote=quote_amount_atomic,
            **kwargs,
        )
        
        return await self._scheduler.send(tx)

    async def launchpad_sell_exact_base(
        self,
        launch_token: Token,
        quote_token: Token,
        base_amount_in: Decimal,
        slippage_tolerance: float = 0.01,
        **kwargs: Unpack[TxParams],
    ):
        """
        Sell an exact amount of launch tokens for quote tokens.
        
        Args:
            launch_token: Launch token to sell
            quote_token: Quote token to receive
            base_amount_in: Exact amount of launch tokens to sell (in decimal units)
            slippage_tolerance: Slippage tolerance (0.01 = 1%)
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the sell operation
        """
        # Convert decimal amount to atomic units
        base_amount_atomic = launch_token.convert_quantity_to_amount(base_amount_in)
        
        # Get quote for how much quote we'll receive
        expected_quote_out = await self._chain_client.launchpad.quote_quote_for_base(
            token=launch_token.address,
            base_amount=base_amount_atomic,
            is_buy=False
        )
        
        # Apply slippage to minimum quote amount out
        min_quote_out = int(expected_quote_out * (1 - slippage_tolerance))
        
        # Ensure approval for launch token
        launch_token_contract = self._chain_client.get_erc20(launch_token.address)
        await self._ensure_launchpad_approval(
            token=launch_token_contract,
            **kwargs,
        )
        
        logger.info(f"Selling exactly {base_amount_in} {launch_token.symbol} for {quote_token.symbol}")

        tx = self._chain_client.launchpad.sell(
            account=self._account.address,
            token=launch_token.address,
            recipient=self._account.address,
            amount_in_base=base_amount_atomic,
            min_amount_out_quote=min_quote_out,
            **kwargs,
        )
        
        return await self._scheduler.send(tx)

    async def get_launchpad_quote_buy(
        self,
        launch_token: Token,
        quote_token: Token,
        quote_amount: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Get a quote for buying launch tokens with quote tokens.
        
        Args:
            launch_token: Launch token to buy
            quote_token: Quote token to spend
            quote_amount: Amount of quote tokens to spend (in decimal units)
            
        Returns:
            Tuple of (base_tokens_received, effective_price_per_base)
        """
        quote_amount_atomic = quote_token.convert_quantity_to_amount(quote_amount)
        
        # Get quote from launchpad
        base_amount_atomic = await self._chain_client.launchpad.quote_base_for_quote(
            token=launch_token.address,
            quote_amount=quote_amount_atomic,
            is_buy=True
        )
        
        # Convert back to decimal units
        base_amount = launch_token.convert_amount_to_quantity(base_amount_atomic)
        
        # Calculate effective price (quote per base)
        effective_price = quote_amount / base_amount if base_amount > 0 else Decimal('0')
        
        return base_amount, effective_price

    async def get_launchpad_quote_sell(
        self,
        launch_token: Token,
        quote_token: Token,
        base_amount: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Get a quote for selling launch tokens for quote tokens.
        
        Args:
            launch_token: Launch token to sell
            quote_token: Quote token to receive
            base_amount: Amount of launch tokens to sell (in decimal units)
            
        Returns:
            Tuple of (quote_tokens_received, effective_price_per_base)
        """
        base_amount_atomic = launch_token.convert_quantity_to_amount(base_amount)
        
        # Get quote from launchpad
        quote_amount_atomic = await self._chain_client.launchpad.quote_quote_for_base(
            token=launch_token.address,
            base_amount=base_amount_atomic,
            is_buy=False
        )

        # Convert back to decimal units
        quote_amount = quote_token.convert_amount_to_quantity(quote_amount_atomic)
        
        # Calculate effective price (quote per base)
        effective_price = quote_amount / base_amount if base_amount > 0 else Decimal('0')
        
        return quote_amount, effective_price
    
    # ================= EXISTING METHODS CONTINUE... =================

    def _convert_amount_to_atomic(self, market: Market, amount: Decimal, is_base: bool) -> int:
        """Convert decimal amount to atomic units based on token type."""
        if is_base:
            return market.base.convert_quantity_to_amount(amount)
        return market.quote.convert_quantity_to_amount(amount)

    # ================= TOKEN SWAP OPERATIONS =================
    
    def _get_swap_function(
        self,
        token_in: Token,
        token_out: Token,
        amount_in_atomic: int,
        amount_out_min: int,
        path: list[ChecksumAddress],
        deadline: int,
        **kwargs,
    ) -> TypedContractFunction[Any]:
        """
        Get the appropriate swap function based on whether WETH is involved.
        
        Args:
            token_in: Input token
            token_out: Output token
            amount_in_atomic: Input amount in atomic units
            amount_out_min: Minimum output amount
            path: Swap path
            deadline: Transaction deadline
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction for the appropriate swap method
        """
        is_eth_in = token_in.address == self._chain_client.weth_address
        is_eth_out = token_out.address == self._chain_client.weth_address
        
        if is_eth_in and not is_eth_out:
            # ETH -> Token: use swapExactETHForTokens
            return self._chain_client.univ2_router.swap_exact_eth_for_tokens(
                amount_out_min=amount_out_min,
                path=path,
                to_=self._account.address,
                deadline=deadline,
                value=amount_in_atomic,  # ETH value sent with transaction
                **kwargs,
            )
        elif not is_eth_in and is_eth_out:
            # Token -> ETH: use swapExactTokensForETH
            return self._chain_client.univ2_router.swap_exact_tokens_for_eth(
                amount_in=amount_in_atomic,
                amount_out_min=amount_out_min,
                path=path,
                to_=self._account.address,
                deadline=deadline,
                **kwargs,
            )
        else:
            # Token -> Token: use swapExactTokensForTokens
            return self._chain_client.univ2_router.swap_exact_tokens_for_tokens(
                amount_in=amount_in_atomic,
                amount_out_min=amount_out_min,
                path=path,
                to_=self._account.address,
                deadline=deadline,
                **kwargs,
            )

    async def swap_tokens(
        self,
        token_in: Token,
        token_out: Token,
        amount_in: Decimal,
        slippage_tolerance: float = 0.01,
        deadline_seconds: int = 1200,
        **kwargs: Unpack[TxParams],
    ):
        """
        Swap tokens using UniswapV2 through the GTE Router.
        
        Args:
            token_in: Input token object with decimals
            token_out: Output token object with decimals
            amount_in: Amount to swap (in decimal units, e.g., Decimal('1.5'))
            slippage_tolerance: Slippage tolerance (0.01 = 1%)
            deadline_seconds: Seconds from now until transaction deadline
            **kwargs: Additional transaction parameters
             
        Returns:
            Transaction receipt from the swap
        """
        # Convert decimal amount to atomic units
        amount_in_atomic = token_in.convert_quantity_to_amount(amount_in)
        
        # Create swap path
        path = [token_in.address, token_out.address]
        
        # Get expected output amount
        amounts_out = await self._chain_client.univ2_router.get_amounts_out(amount_in_atomic, path)
        expected_out = amounts_out[-1]  # Output amount is the last element
        
        # Calculate minimum output with slippage
        amount_out_min = int(expected_out * (1 - slippage_tolerance))
        
        # Calculate deadline
        deadline = int(time.time()) + deadline_seconds
        
        # Only approve if input token is not ETH/WETH (for ETH swaps, no approval needed)
        if token_in.address != self._chain_client.weth_address:
            token_in_contract = self._chain_client.get_erc20(token_in.address)
            await self._ensure_swap_approval(
                token=token_in_contract,
                **kwargs,
            )
        
        logger.info(f"Swapping {amount_in} {token_in.symbol} for {token_out.symbol}")

        # Get the appropriate swap function
        swap_tx = self._get_swap_function(
            token_in=token_in,
            token_out=token_out,
            amount_in_atomic=amount_in_atomic,
            amount_out_min=amount_out_min,
            path=path,
            deadline=deadline,
            **kwargs,
        )
        
        return await self._scheduler.send(swap_tx)

    def _get_swap_for_exact_function(
        self,
        token_in: Token,
        token_out: Token,
        amount_out_atomic: int,
        amount_in_max: int,
        path: list[ChecksumAddress],
        deadline: int,
        **kwargs,
    ) -> TypedContractFunction[Any]:
        """
        Get the appropriate swap function for exact output based on whether WETH is involved.
        
        Args:
            token_in: Input token
            token_out: Output token
            amount_out_atomic: Exact output amount in atomic units
            amount_in_max: Maximum input amount
            path: Swap path
            deadline: Transaction deadline
            **kwargs: Additional transaction parameters
            
        Returns:
            TypedContractFunction for the appropriate swap method
        """
        is_eth_in = token_in.address == self._chain_client.weth_address
        is_eth_out = token_out.address == self._chain_client.weth_address
        
        if is_eth_in and not is_eth_out:
            # ETH -> Token: use swapETHForExactTokens
            return self._chain_client.univ2_router.swap_eth_for_exact_tokens(
                amount_out=amount_out_atomic,
                path=path,
                to=self._account.address,
                deadline=deadline,
                value=amount_in_max,  # ETH value sent with transaction
                **kwargs,
            )
        elif not is_eth_in and is_eth_out:
            # Token -> ETH: use swapTokensForExactETH
            return self._chain_client.univ2_router.swap_tokens_for_exact_eth(
                amount_out=amount_out_atomic,
                amount_in_max=amount_in_max,
                path=path,
                to=self._account.address,
                deadline=deadline,
                **kwargs,
            )
        else:
            # Token -> Token: use swapTokensForExactTokens
            return self._chain_client.univ2_router.swap_tokens_for_exact_tokens(
                amount_out=amount_out_atomic,
                amount_in_max=amount_in_max,
                path=path,
                to=self._account.address,
                deadline=deadline,
                **kwargs,
            )

    async def swap_tokens_for_exact_output(
        self,
        token_in: Token,
        token_out: Token,
        amount_out: Decimal,
        slippage_tolerance: float = 0.01,
        deadline_seconds: int = 1200,
        **kwargs: Unpack[TxParams],
    ):
        """
        Swap tokens for an exact output amount using UniswapV2 through the GTE Router.
        
        Args:
            token_in: Input token object with decimals
            token_out: Output token object with decimals
            amount_out: Exact amount to receive (in decimal units)
            slippage_tolerance: Slippage tolerance (0.01 = 1%)
            deadline_seconds: Seconds from now until transaction deadline
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the swap
        """
        # Convert decimal amount to atomic units
        amount_out_atomic = token_out.convert_quantity_to_amount(amount_out)
        
        # Create swap path
        path = [token_in.address, token_out.address]
        
        # Get required input amount
        amounts_in = await self._chain_client.univ2_router.get_amounts_in(amount_out_atomic, path)
        expected_in = amounts_in[0]  # Input amount is the first element
        
        # Calculate maximum input with slippage
        amount_in_max = int(expected_in * (1 + slippage_tolerance))
        
        # Calculate deadline
        deadline = int(time.time()) + deadline_seconds
        
        # Only approve if input token is not ETH/WETH (for ETH swaps, no approval needed)
        if token_in.address != self._chain_client.weth_address:
            token_in_contract = self._chain_client.get_erc20(token_in.address)
            await self._ensure_swap_approval(
                token=token_in_contract,
                **kwargs,
            )
        
        logger.info(f"Swapping {token_in.symbol} for exactly {amount_out} {token_out.symbol}")

        # Get the appropriate swap function
        swap_tx = self._get_swap_for_exact_function(
            token_in=token_in,
            token_out=token_out,
            amount_out_atomic=amount_out_atomic,
            amount_in_max=amount_in_max,
            path=path,
            deadline=deadline,
            **kwargs,
        )
        
        return await self._scheduler.send(swap_tx)

    async def get_swap_quote(
        self,
        token_in: Token,
        token_out: Token,
        amount_in: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Get a quote for swapping tokens.
        
        Args:
            token_in: Input token object with decimals
            token_out: Output token object with decimals
            amount_in: Amount to swap (in decimal units)
            
        Returns:
            Tuple of (expected_output_amount, effective_price)
        """
        # Convert decimal amount to atomic units
        amount_in_atomic = token_in.convert_quantity_to_amount(amount_in)
        
        # Create swap path
        path = [token_in.address, token_out.address]
        
        # Get expected output amount
        amounts_out = await self._chain_client.univ2_router.get_amounts_out(amount_in_atomic, path)
        expected_out_atomic = amounts_out[1]
        
        # Convert back to decimal units
        expected_out = token_out.convert_amount_to_quantity(expected_out_atomic)
        
        # Calculate effective price
        effective_price = expected_out / amount_in if amount_in > 0 else Decimal('0')
        
        return expected_out, effective_price

    # ================= EXISTING METHODS CONTINUE... =================

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

        token = self._chain_client.get_erc20(token_address)
        
        # time the approval
        await self._ensure_approval(token, **kwargs)

        tx = self._chain_client.clob_manager.deposit(
            account=self._account.address,
            token=token_address,
            amount=amount,
            from_operator=False,
            **kwargs,
        )
        return await self._scheduler.send(tx)

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
        tx = self._chain_client.clob_manager.withdraw(
            account=self._account.address, token=token_address, amount=amount, to_operator=False, **kwargs
        )
        
        return await self._scheduler.send(tx)

    async def get_token_balance(self, token_address: ChecksumAddress) -> int:
        """
        Get the balance of a token in the wallet.
        """
        return await self._chain_client.get_erc20(token_address).balance_of(self._account.address)
    
    async def get_weth_balance(self) -> Decimal:
        """
        Get the balance of WETH in the wallet.
        """
        weth_token = Token(address=self._chain_client.weth_address, decimals=18, name="Wrapped Ether", symbol="WETH", total_supply=None)
        return weth_token.convert_amount_to_quantity(await self.get_token_balance(self._chain_client.weth_address))

    async def wrap_eth(
            self, amount: Decimal, **kwargs: Unpack[TxParams]
    ):
        """
        Wrap ETH to WETH.

        Args:
            amount: Amount of ETH to wrap
            **kwargs: Additional transaction parameters

        Returns:
            Transaction hash from the wrap operation
        """
        weth_token = Token(address=self._chain_client.weth_address, decimals=18, name="Wrapped Ether", symbol="WETH", total_supply=None)
        amount_wei = weth_token.convert_quantity_to_amount(amount)
        weth = self._chain_client.weth

        kwargs['value'] = Wei(amount_wei)
        
        tx = weth.deposit(**kwargs)
        return await self._scheduler.send(tx)

    async def unwrap_eth(
            self, amount: Decimal, **kwargs: Unpack[TxParams]
    ):
        """
        Unwrap WETH to ETH.

        Args:
            amount: Amount of WETH to unwrap
            **kwargs: Additional transaction parameters

        Returns:
            Transaction hash from the unwrap operation
        """
        weth_token = Token(address=self._chain_client.weth_address, decimals=18, name="Wrapped Ether", symbol="WETH", total_supply=None)
        amount_wei = weth_token.convert_quantity_to_amount(amount)
        weth = self._chain_client.weth
        tx = weth.withdraw(value_=amount_wei, **kwargs)
        return await self._scheduler.send(tx)

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
            Transaction hash from the approve_operator operation
        """
        if OperatorRole.WITHDRAW in roles and not unsafe_withdraw:
            raise ValueError("Unsafe withdraw must be enabled to approve withdraw role")
        if OperatorRole.LAUNCHPAD_FILL in roles and not unsafe_launchpad_fill:
            raise ValueError("Unsafe launchpad fill must be enabled to approve launchpad fill role")
        
        roles_int = self._encode_rules(roles)
        logger.info(f"Approving operator {operator_address} for account {self._account.address} with roles {roles}")


        return await self._scheduler.send(self._chain_client.clob_manager.approve_operator(
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
            Transaction hash from the disapprove_operator operation
        """
        roles_int = self._encode_rules(roles)
        logger.info(f"Disapproving operator {operator_address} for account {self._account.address} with roles {roles}")

        return await self._scheduler.send(self._chain_client.clob_manager.disapprove_operator(
            operator=operator_address,
            roles=roles_int,
            **kwargs
        ))

    # ================= ORDER OPERATIONS =================

    async def get_tob(self, market: Market) -> tuple[Decimal, Decimal]:
        """
        Get the top of book for a market.
        Returns:
            Tuple of (best bid price, best ask price)
        """
        clob = self._chain_client.get_clob(market.address)
        best_bid, best_ask = await clob.get_tob()
        return market.quote.convert_amount_to_quantity(best_bid), market.quote.convert_amount_to_quantity(best_ask)
    
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

        # For IOC and FOK orders, we use the fill order API
        if time_in_force in [TimeInForce.IOC, TimeInForce.FOK]:
            if time_in_force == TimeInForce.IOC:
                fill_order_type = FillOrderType.IMMEDIATE_OR_CANCEL
            elif time_in_force == TimeInForce.FOK:
                fill_order_type = FillOrderType.FILL_OR_KILL
            else:
                raise ValueError(f"Unknown time_in_force: {time_in_force}")

            # Create post fill order args using NamedTuple
            args = PostFillOrderArgs(
                amount,
                price,
                side.value,
                True,  # amountIsBase - since amount is in base tokens
                fill_order_type.value,
                settlement.value,
            )

            # Return the router transaction
            return self._chain_client.router.clob_post_fill_order(clob=market_address, args=args, **kwargs)
        else:
            if time_in_force == TimeInForce.GTC:
                tif = LimitOrderType.GOOD_TILL_CANCELLED
            elif time_in_force == TimeInForce.POST_ONLY:
                tif = LimitOrderType.POST_ONLY
            else:
                raise ValueError(f"Unknown time_in_force: {time_in_force}")
            
            # Create post limit order args using NamedTuple
            args = PostLimitOrderArgs(
                amount,
                price,
                0,  # cancelTimestamp - no expiration
                side.value,
                client_order_id,
                tif.value,
                settlement.value,
            )

            # Return the router transaction
            return self._chain_client.router.clob_post_limit_order(clob=market_address, args=args, **kwargs)

    async def place_limit_order(
            self,
            market: Market,
            side: OrderSide,
            amount: Decimal,
            price: Decimal,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            settlement: Settlement = Settlement.INSTANT,
            return_order: bool = False,
            **kwargs: Unpack[TxParams],
    ) -> str | dict[str, Any]:
        """
        Place a limit order using the router contract.
        
        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in decimal units
            price: Order price in decimal units
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Optional client order ID for tracking
            **kwargs: Additional transaction parameters

        Returns:
            Transaction hash of the placed order or Event of the placed order
        """
        amount_atomic = market.base.convert_quantity_to_amount(amount)
        price_atomic = market.quote.convert_quantity_to_amount(price)
        
        token = self._chain_client.get_erc20(market.quote.address) if side == OrderSide.BUY else self._chain_client.get_erc20(market.base.address)
        await self._ensure_approval(
            token=token,
            **kwargs,
        )
        clob = self._chain_client.get_clob(market.address)
        tx = self.place_limit_order_tx(
            market_address=market.address,
            side=side,
            amount=amount_atomic,
            price=price_atomic,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            settlement=settlement,
            **kwargs,
        ).with_event(clob.contract.events.LimitOrderProcessed())
        
        # Send the transaction and return the receipt
        if return_order:
            return await self._scheduler.send_wait(tx)
        else:
            return await self._scheduler.send(tx)

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

        # Create post fill order args using named tuple
        args = PostFillOrderArgs(
            amount,
            price_limit,
            side.value,
            amount_is_base,
            FillOrderType.IMMEDIATE_OR_CANCEL.value,
            Settlement.INSTANT.value,
        )

        # Return the router transaction
        return self._chain_client.router.clob_post_fill_order(clob=market.address, args=args, **kwargs)

    async def _ensure_tob_subscription(self, market: Market):
        """Ensure we have a live TOB subscription for this market."""
        if market.address in self._tob_subscriptions:
            return  # Already subscribed
        
        def tob_callback(data):
            """Callback runs in the same event loop - no threading issues."""
            try:
                bids = data.get("b", [])
                asks = data.get("a", [])
                
                best_bid = Decimal(bids[0]["px"]) if bids else Decimal('0')
                best_ask = Decimal(asks[0]["px"]) if asks else Decimal('0')
                
                # This is thread-safe because it's all in the same event loop
                self._tob_cache[market.address] = (best_bid, best_ask)
                
                logger.debug(f"TOB updated for {market.address}: {best_bid}/{best_ask}")
            except Exception as e:
                logger.warning(f"Error processing TOB update for {market.address}: {e}")
        
        # This uses the existing WebSocket connection - no new threads
        await self._info.subscribe_orderbook(market.address, tob_callback, limit=1)
        self._tob_subscriptions.add(market.address)
        
        logger.info(f"Subscribed to TOB updates for {market.address}")

    async def _get_cached_tob(self, market: Market) -> tuple[Decimal, Decimal]:
        """Get TOB from cache or fallback to RPC."""
        # Ensure subscription exists (this is async but runs in same event loop)
        await self._ensure_tob_subscription(market)
        
        # Check cache
        if market.address in self._tob_cache:
            bid, ask = self._tob_cache[market.address]
            logger.debug(f"Using cached TOB for {market.address}")
            return bid, ask
        
        # Cache miss/stale - fallback to RPC
        logger.debug(f"TOB cache miss for {market.address}, using RPC fallback")
        return await self.get_tob(market)

    async def _get_price_limit(self, market: Market, side: OrderSide, slippage: float = 0.01) -> int:
        """
        Get the price limit for a market order with slippage applied.
        Uses cached WebSocket TOB data for better performance.
        """
        # Use cached TOB data (fast) with RPC fallback
        best_bid, best_ask = await self._get_cached_tob(market)
        
        if side == OrderSide.BUY:
            # For BUY orders, use lowest ask with positive slippage
            return int(market.quote.convert_quantity_to_amount(best_ask * Decimal(str(1 + slippage))))
        else:
            # For SELL orders, use highest bid with negative slippage
            return int(market.quote.convert_quantity_to_amount(best_bid * Decimal(str(1 - slippage))))

    async def place_market_order(
            self,
            market: Market,
            side: OrderSide,
            amount: Decimal,
            amount_is_base: bool = True,
            slippage: float = 0.01,
            **kwargs,
    ):
        """
        Place a market order using the router contract.

        Args:
            market: Market to place the order on
            side: Order side (BUY or SELL)
            amount: Order amount in decimal units
            amount_is_base: Whether the amount is in base tokens
            slippage: Slippage percentage for price limit
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt of the placed order
        """
        amount_atomic = market.base.convert_quantity_to_amount(amount) if amount_is_base else market.quote.convert_quantity_to_amount(amount)
        price_limit = await self._get_price_limit(market, side, slippage)
        token = self._chain_client.get_erc20(market.quote.address) if amount_is_base else self._chain_client.get_erc20(market.base.address)
        
        await self._ensure_approval(
            token=token,
            **kwargs,
        )
        
        tx = self.place_market_order_tx(
            market=market,
            side=side,
            amount=amount_atomic,
            price_limit=price_limit,
            amount_is_base=amount_is_base,
            **kwargs,
        )
        return await self._scheduler.send(tx)
    
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
        clob = self._chain_client.get_clob(market.address)

        # Create amend args
        args = AmendArgs(
            order_id=order_id,
            amount_in_base=amount_in_base,
            price=price_in_ticks,
            cancel_timestamp=0,  # No expiration
            side=side.value,
            limit_order_type=LimitOrderType.POST_ONLY.value,
            settlement=Settlement.INSTANT.value,
        )

        # Return the transaction
        return clob.amend(account=self._account.address, args=args, **kwargs)

    async def amend_order(
            self,
            market: Market,
            order_id: int,
            side: OrderSide,
            original_amount: Decimal | None = None,
            original_price: Decimal | None = None,
            new_amount: Decimal | None = None,
            new_price: Decimal | None = None,
            **kwargs,
    ) -> str:
        """
        Amend an existing order.

        Args:
            market: Market the order is on
            order_id: ID of the order to amend
            side: Order side
            original_amount: Original amount for the order
            original_price: Original price for the order
            new_amount: New amount for the order (None to keep current)
            new_price: New price for the order (None to keep current)
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt from the amend operation
        """
        amount_in_base = market.base.convert_quantity_to_amount(new_amount if new_amount else original_amount) if original_amount else 0
        price_in_ticks = market.quote.convert_quantity_to_amount(new_price if new_price else original_price) if original_price else 0
        
        if amount_in_base == 0 or price_in_ticks == 0:
            raise ValueError("Amount or price is 0")
        
        token = self._chain_client.get_erc20(market.quote.address) if side == OrderSide.BUY else self._chain_client.get_erc20(market.base.address)
        
        await self._ensure_approval(
            token=token,
            **kwargs,
        )

        # Create and execute transaction
        tx = await self.amend_order_tx(
            market=market, 
            order_id=order_id, 
            amount_in_base=int(amount_in_base),
            price_in_ticks=int(price_in_ticks),
            side=side,
            **kwargs
        )

        return await self._scheduler.send(tx)

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

        # Create cancel args
        args = CancelArgs(
            [order_id], 
            Settlement.INSTANT.value          
        )

        # Return the router transaction
        return self._chain_client.router.clob_cancel(clob=market.address, args=args, is_unwrapping=True, **kwargs)

    async def cancel_order(self, market: Market, order_id: int, **kwargs) -> str:
        """
        Cancel an existing order using the router contract.

        Args:
            market: Market the order is on
            order_id: ID of the order to cancel
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt of the cancellation
        """
        clob = self._chain_client.get_clob(market.address)
        tx = self.cancel_order_tx(market=market, order_id=order_id, **kwargs)
        return await self._scheduler.send(tx)

    async def cancel_all_orders(self, market: Market, open_orders: List[Order], **kwargs) -> List[str]:
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
        self._approved_clob_tokens.clear()
        self._approved_swap_tokens.clear()
        self._approved_launchpad_tokens.clear()
        logger.info("Approval cache cleared")

    def clear_tob_cache(self):
        """Clear TOB cache - useful for testing or if stale data is suspected."""
        self._tob_cache.clear()
        logger.info("TOB cache cleared")

    async def unsubscribe_tob(self, market: Market):
        """Unsubscribe from TOB updates for a specific market."""
        if market.address in self._tob_subscriptions:
            try:
                await self._info.unsubscribe_orderbook(market.address, limit=1)
                self._tob_subscriptions.remove(market.address)
                self._tob_cache.pop(market.address, None)
                logger.info(f"Unsubscribed from TOB updates for {market.address}")
            except Exception as e:
                logger.warning(f"Error unsubscribing from {market.address}: {e}")

    # ================= UTILITY OPERATIONS =================

    async def get_balance(
            self, token_address: ChecksumAddress, account: ChecksumAddress | None = None
    ) -> tuple[Decimal, Decimal]:
        """
        Get token balance for an account both on-chain and in the exchange.

        Args:
            token_address: Address of token to check
            account: Account to check (defaults to sender address)

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """
        token_details = await self._info.get_token(token_address)
        account = account if account else self._account.address
        token = self._chain_client.get_erc20(token_address)

        # Get wallet balance
        wallet_balance_raw = await token.balance_of(account)
        wallet_balance = token_details.convert_amount_to_quantity(wallet_balance_raw)

        # Get exchange balance
        exchange_balance_raw = await self._chain_client.clob_manager.get_account_balance(
            account, token_address
        )
        exchange_balance = token_details.convert_amount_to_quantity(exchange_balance_raw)

        return wallet_balance, exchange_balance
