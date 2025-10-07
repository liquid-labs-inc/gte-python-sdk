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
from gte_py.api.chain.clob import Clob
from gte_py.api.chain.structs import AmendArgs, AmendLimitOrderArgsPerp, Side, Settlement, TiF, CancelArgs, PlaceOrderArgs, PlaceOrderArgsPerp, AmendLimitOrderArgsPerp, SettleParams
from gte_py.api.chain.events import OrderAmendedPerpEvent, OrderProcessedPerpEvent, OrderProcessedEvent, OrderAmendedEvent
from gte_py.api.chain.utils import TypedContractFunction, BoundedNonceTxScheduler
from gte_py.models import Market, Order, OrderStatus, TimeInForce, Token
from gte_py.api.chain.erc20 import Erc20
from gte_py.configs import NetworkConfig

logger = logging.getLogger(__name__)


class ExecutionClient:
    """Client for executing orders and managing deposits/withdrawals on the GTE exchange."""

    def __init__(
            self,
            web3: AsyncWeb3,
            info: InfoClient,
            config: NetworkConfig,
            account: LocalAccount | None = None,
    ):
        """
        Initialize the execution client.

        Args:
            web3: AsyncWeb3 instance for on-chain interactions
            info: InfoClient instance for market data
            config: NetworkConfig instance for network configuration
            account: LocalAccount instance for signing transactions
        """
        self._config = config
        self._web3 = web3
        self._account = account
        self._wallet_address = web3.eth.default_account
        self._chain_client = ChainClient(web3, config.router_address, config.launchpad_address, config.clob_manager_address, config.perp_manager_address, config.account_manager_address, config.operator_address, config.weth_address)
        self._scheduler = BoundedNonceTxScheduler(
            web3=self._web3,
            account=self._account,
        )
        self._info = info
        
        self._approved_am_tokens: set[ChecksumAddress] = set()
        self._approved_pm_tokens: bool = False
        self._max_approval = 2**256 - 1

        self._spot_market_cache: dict[ChecksumAddress, Clob] = {}

    def perp_asset_to_bytes32(self, asset: str) -> HexBytes:
        """
        Convert a perpetual asset name to a bytes32.
        """
        return HexBytes(asset.encode("utf-8").ljust(32, b"\0"))
    
    def _convert_atomic_to_decimal(self, amount: int) -> Decimal:
        """Convert decimal amount to atomic units based on token type."""
        return Decimal(amount) / Decimal(10 ** 18)
    
    def _convert_decimal_to_atomic(self, amount: Decimal) -> int:
        """Convert atomic amount to decimal units based on token type."""
        return int(amount * (10 ** 18))

    async def _ensure_pm_approval(
        self,
        capUSD_address: ChecksumAddress,
        **kwargs,
    ):
        """
        Ensure the correct token is approved for the required amount.
        Uses infinite approvals (2^256 - 1) and caches approved tokens.
        """ 
        token_address = capUSD_address

        # Check if we've already approved this token
        if self._approved_pm_tokens:
            return
        
        # check if allowance is already set
        allowance = await self._chain_client.get_erc20(capUSD_address).allowance(owner=self.wallet_address, spender=self._chain_client.perp_manager_address)
        if allowance >= self._max_approval // 2:
            self._approved_pm_tokens = True
            return
        
        # Need to approve - use infinite approval
        _ = await self._scheduler.send(self._chain_client.get_erc20(capUSD_address).approve(spender=self._chain_client.perp_manager_address, value=self._max_approval, **kwargs))
        
        # Cache the token as approved
        self._approved_pm_tokens = True

    async def perp_deposit(
        self,
        amount: Decimal,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Deposit capUSD collateral to the perpetuals manager.
        
        Args:
            amount: Amount to deposit in decimal units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the deposit operation
        """
        await self._ensure_pm_approval(self._config.collateral_asset_address)

        amount_atomic = self._convert_decimal_to_atomic(amount)
        tx = self._chain_client.perp_manager.deposit(
            account=self.wallet_address,
            amount=amount_atomic,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def perp_withdraw(
        self,
        amount: Decimal,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Withdraw capUSD collateral from the perpetuals manager.
        
        Args:
            amount: Amount to withdraw in decimal units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the withdraw operation
        """
        amount_atomic = self._convert_decimal_to_atomic(amount)
        tx = self._chain_client.perp_manager.withdraw(
            account=self.wallet_address,
            amount=amount_atomic,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def perp_add_margin(
        self,
        subaccount: int,
        amount: Decimal,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Add margin to a perpetuals subaccount.
        
        Args:
            subaccount: Subaccount ID
            amount: Amount to add in decimal units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the add margin operation
        """
        amount_atomic = self._convert_decimal_to_atomic(amount)
        tx = self._chain_client.perp_manager.add_margin(
            account=self.wallet_address,
            subaccount=subaccount,
            amount=amount_atomic,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def perp_remove_margin(
        self,
        subaccount: int,
        amount: Decimal,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Remove margin from a perpetuals subaccount.
        
        Args:
            subaccount: Subaccount ID
            amount: Amount to remove in decimal units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the remove margin operation
        """
        amount_atomic = self._convert_decimal_to_atomic(amount)
        tx = self._chain_client.perp_manager.remove_margin(
            account=self.wallet_address,
            subaccount=subaccount,
            amount=amount_atomic,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)
    
    async def perp_amend_order(
        self,
        asset: str,
        order_id: int,
        subaccount: int,
        side: Side,
        amount: Decimal,
        price: Decimal,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Amend a perpetuals order.
        
        Args:
            asset: Asset identifier
            order_id: Order ID to amend
            subaccount: Subaccount ID
            side: Order side
            amount: Order amount in decimal units
            price: Order price in decimal units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
        """
        amount_atomic = self._convert_decimal_to_atomic(amount)
        price_atomic = self._convert_decimal_to_atomic(price)
        args = AmendLimitOrderArgsPerp(
            asset=self.perp_asset_to_bytes32(asset),
            subaccount=subaccount,
            order_or_client_id=order_id,
            base_amount=amount_atomic,
            price=price_atomic,
            expiry_time=0,
            side=side.value,
            reduce_only=False,
        )
        tx = self._chain_client.perp_manager.amend_limit_order(
            account=self.wallet_address,
            args=args,
            **kwargs,
        ).with_event(self._chain_client.perp_manager.contract.events.OrderAmended())
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)
        
    
    async def perp_update_leverage(
        self,
        asset: str,
        subaccount: int = 1,
        leverage: Decimal = Decimal(1),
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Update the leverage for a perpetual market.
        """
        leverage_atomic = self._convert_decimal_to_atomic(leverage)
        tx = self._chain_client.perp_manager.set_position_leverage(
            account=self.wallet_address,
            asset=self.perp_asset_to_bytes32(asset),
            subaccount=subaccount,
            new_leverage=leverage_atomic,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send_wait(tx)

    async def perp_place_order(
        self,
        asset: str,
        side: Side,
        amount: Decimal,
        limit_price: Decimal,
        subaccount: int = 0,
        expiry_time: int = 0,
        base_denominated: bool = True,
        tif: int = 0,  # 0 = GTC (Good Till Cancelled)
        client_order_id: int = 0,
        reduce_only: bool = False,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Place an order on a perpetual market.
        
        Args:
            asset: Asset identifier (market)
            side: Order side (BUY=0, SELL=1)
            amount: Order amount in decimal units
            limit_price: Limit price in decimal units
            subaccount: Subaccount ID (default: 0)
            expiry_time: Order expiry timestamp (0 = no expiry)
            base_denominated: Whether amount is in base units (default: True)
            tif: Time in force (0 = GTC, default: 0)
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the place order operation
        """
        # Convert decimal inputs to atomic units
        amount_atomic = self._convert_decimal_to_atomic(amount)
        limit_price_atomic = self._convert_decimal_to_atomic(limit_price)
        
        # Create PlaceOrderArgsPerp with the correct fields for PerpManager
        args = PlaceOrderArgsPerp(
            subaccount=subaccount,
            asset=self.perp_asset_to_bytes32(asset),
            side=side.value,
            builder_code=HexBytes('00' * 32),
            limit_price=limit_price_atomic,
            amount=amount_atomic,
            base_denominated=base_denominated,
            tif=tif,
            expiry_time=expiry_time,
            client_order_id=client_order_id,
            reduce_only=reduce_only,
        )
        
        tx = self._chain_client.perp_manager.place_order(
            account=self.wallet_address,
            args=args,
            **kwargs,
        ).with_event(self._chain_client.perp_manager.contract.events.OrderProcessed())
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send_wait(tx)

    async def perp_get_position(
        self,
        asset: str,
        subaccount: int,
    ):
        """
        Get position information for a perpetuals asset.
        
        Args:
            asset: Asset identifier
            subaccount: Subaccount ID
            
        Returns:
            Position data
        """
        return await self._chain_client.perp_manager.get_position(
            asset=self.perp_asset_to_bytes32(asset),
            account=self.wallet_address,
            subaccount=subaccount,
        )

    async def perp_get_margin_balance(
        self,
        subaccount: int,
    ) -> int:
        """
        Get margin balance for a subaccount.
        
        Args:
            subaccount: Subaccount ID
            
        Returns:
            Margin balance in atomic units
        """
        return await self._chain_client.perp_manager.get_margin_balance(
            account=self.wallet_address,
            subaccount=subaccount,
        )
    
    async def perp_get_mark_price(
        self,
        asset: str,
    ) -> int:
        """
        Get mark price for a perpetual market.
        """
        return await self._chain_client.perp_manager.get_mark_price(self.perp_asset_to_bytes32(asset))
    

    async def perp_cancel_limit_orders(
        self,
        asset: str,
        subaccount: int,
        order_ids: list[int],
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Cancel limit orders on a perpetual market.
        
        Args:
            asset: Asset identifier (market)
            subaccount: Subaccount ID
            order_ids: List of order IDs to cancel
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the cancel operation
        """
        tx = self._chain_client.perp_manager.cancel_limit_orders(
            asset=self.perp_asset_to_bytes32(asset),
            account=self.wallet_address,
            subaccount=subaccount,
            order_ids=order_ids,
            **kwargs,
        ).with_event(self._chain_client.perp_manager.contract.events.OrderCanceled())
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def perp_get_account_value(
        self,
        subaccount: int,
    ) -> int:
        """
        Get total account value for a subaccount.
        
        Args:
            subaccount: Subaccount ID
            
        Returns:
            Account value in atomic units
        """
        return await self._chain_client.perp_manager.get_account_value(
            account=self.wallet_address,
            subaccount=subaccount,
        )

    async def perp_get_free_collateral_balance(self) -> int:
        """
        Get free collateral balance available for trading.
        
        Returns:
            Free collateral balance in atomic units
        """
        return await self._chain_client.perp_manager.get_free_collateral_balance(
            account=self.wallet_address,
        )

    async def perp_is_liquidatable(
        self,
        subaccount: int,
    ) -> bool:
        """
        Check if a subaccount is liquidatable.
        
        Args:
            subaccount: Subaccount ID
            
        Returns:
            True if the subaccount is liquidatable
        """
        return await self._chain_client.perp_manager.is_liquidatable(
            account=self.wallet_address,
            subaccount=subaccount,
        )

    # ================= ACCOUNT MANAGER OPERATIONS =================

    async def _ensure_am_approval(
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
        if token_address in self._approved_am_tokens:
            return
        
        # check if allowance is already set
        allowance = await token.allowance(owner=self.wallet_address, spender=self._chain_client.clob_manager_address)
        if allowance >= self._max_approval // 2:
            self._approved_am_tokens.add(token_address)
            return
        
        # Need to approve - use infinite approval
        _ = await self._scheduler.send(token.approve(spender=self._chain_client.clob_manager_address, value=self._max_approval, **kwargs))
        
        # Cache the token as approved
        self._approved_am_tokens.add(token_address)

    async def account_deposit(
        self,
        token: ChecksumAddress,
        amount: Decimal,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Deposit tokens to the account manager.
        
        Args:
            token: Token address
            amount: Amount to deposit in atomic units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the deposit operation
        """
        amount_atomic = self._convert_decimal_to_atomic(amount)
        await self._ensure_am_approval(self._chain_client.get_erc20(token))

        tx = self._chain_client.account_manager.deposit(
            account=self.wallet_address,
            token=token,
            amount=amount_atomic,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def account_withdraw(
        self,
        token: ChecksumAddress,
        amount: int,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Withdraw tokens from the account manager.
        
        Args:
            token: Token address
            amount: Amount to withdraw in atomic units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the withdraw operation
        """
        tx = self._chain_client.account_manager.withdraw(
            account=self.wallet_address,
            token=token,
            amount=amount,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def account_get_balance(
        self,
        token: ChecksumAddress,
        account: ChecksumAddress | None = None,
    ) -> int:
        """
        Get account balance for a token from the account manager.
        
        Args:
            token: Token address
            account: Account address (defaults to wallet address)
            
        Returns:
            Balance in atomic units
        """
        account_addr = account if account else self.wallet_address
        return await self._chain_client.account_manager.get_account_balance(
            account=account_addr,
            token=token,
        )

    async def account_deposit_from_perps(
        self,
        amount: int,
        return_built_tx: bool = False,
        **kwargs: Unpack[TxParams],
    ):
        """
        Deposit collateral from perpetuals to account manager.
        
        Args:
            amount: Amount to deposit in atomic units
            return_built_tx: Whether to return built transaction data
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction receipt from the deposit operation
        """
        tx = self._chain_client.perp_manager.deposit_from_spot(
            account=self.wallet_address,
            amount=amount,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def account_get_fee_tier(
        self,
        account: ChecksumAddress | None = None,
    ) -> int:
        """
        Get fee tier for an account.
        
        Args:
            account: Account address (defaults to wallet address)
            
        Returns:
            Fee tier
        """
        account_addr = account if account else self.wallet_address
        return await self._chain_client.account_manager.get_fee_tier(account=account_addr)

    @property
    def wallet_address(self) -> ChecksumAddress:
        """Get the wallet address."""
        if not self._wallet_address:
            raise ValueError("No wallet address set")
        return self._wallet_address

    async def init(self):
        """Initialize the chain client."""
        await self._chain_client.init()
        await self._scheduler.start()

    async def close(self):
        """Clean up resources and unsubscribe from all WebSocket subscriptions."""
        # Stop the transaction scheduler
        await self._scheduler.stop()
        
        logger.info("ExecutionClient cleanup completed")

    # ================= DEPOSIT/WITHDRAW OPERATIONS =================

    async def approve_token(self, token: Erc20, contract_address: ChecksumAddress, return_built_tx: bool = False, **kwargs):
        """
        Ensure the token is approved for the required amount.
        Uses infinite approvals (2^256 - 1) and caches approved tokens.
        """
        allowance = await token.allowance(owner=self.wallet_address, spender=contract_address)
        if allowance >= self._max_approval // 2:
            return
        
        if return_built_tx:
            return await self._scheduler.return_transaction_data(token.approve(spender=contract_address, value=self._max_approval, **kwargs))
        _ = await self._scheduler.send(token.approve(spender=contract_address, value=self._max_approval, **kwargs))
    
    async def get_erc20(self, token_address: ChecksumAddress) -> Erc20:
        """
        Get an Erc20 token contract.
        """
        return self._chain_client.get_erc20(token_address)


    async def launchpad_buy_exact_quote(
        self,
        launch_token: Token,
        quote_token: Token,
        quote_amount_in: Decimal,
        slippage_tolerance: float = 0.01,
        return_built_tx: bool = False,
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
        await self._ensure_am_approval(
            token=quote_token_contract,
            **kwargs,
        )
        
        logger.info(f"Buying {launch_token.symbol} with exactly {quote_amount_in} {quote_token.symbol}")

        tx = self._chain_client.launchpad.buy(
            account=self.wallet_address,
            token=launch_token.address,
            recipient=self.wallet_address,
            amount_out_base=min_base_out,
            max_amount_in_quote=quote_amount_atomic,
            **kwargs,
        )
        
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def launchpad_sell_exact_base(
        self,
        launch_token: Token,
        quote_token: Token,
        base_amount_in: Decimal,
        slippage_tolerance: float = 0.01,
        return_built_tx: bool = False,
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
        await self._ensure_am_approval(
            token=launch_token_contract,
            **kwargs,
        )
        
        logger.info(f"Selling exactly {base_amount_in} {launch_token.symbol} for {quote_token.symbol}")

        tx = self._chain_client.launchpad.sell(
            account=self.wallet_address,
            token=launch_token.address,
            recipient=self.wallet_address,
            amount_in_base=base_amount_atomic,
            min_amount_out_quote=min_quote_out,
            **kwargs,
        )
        
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
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
                to_=self.wallet_address,
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
                to_=self.wallet_address,
                deadline=deadline,
                **kwargs,
            )
        else:
            # Token -> Token: use swapExactTokensForTokens
            return self._chain_client.univ2_router.swap_exact_tokens_for_tokens(
                amount_in=amount_in_atomic,
                amount_out_min=amount_out_min,
                path=path,
                to_=self.wallet_address,
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
        return_built_tx: bool = False,
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
            await self._ensure_am_approval(
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
        
        if return_built_tx:
            return await self._scheduler.return_transaction_data(swap_tx)
        return await self._scheduler.send(swap_tx)

    def _get_swap_for_exact_function(
        self,
        token_in: ChecksumAddress,
        token_out: ChecksumAddress,
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
        is_eth_in = token_in == self._chain_client.weth_address
        is_eth_out = token_out == self._chain_client.weth_address
        
        if is_eth_in and not is_eth_out:
            # ETH -> Token: use swapETHForExactTokens
            return self._chain_client.univ2_router.swap_eth_for_exact_tokens(
                amount_out=amount_out_atomic,
                path=path,
                to=self.wallet_address,
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
                to=self.wallet_address,
                deadline=deadline,
                **kwargs,
            )
        else:
            # Token -> Token: use swapTokensForExactTokens
            return self._chain_client.univ2_router.swap_tokens_for_exact_tokens(
                amount_out=amount_out_atomic,
                amount_in_max=amount_in_max,
                path=path,
                to=self.wallet_address,
                deadline=deadline,
                **kwargs,
            )

    async def swap_tokens_for_exact_output(
        self,
        token_in: ChecksumAddress,
        token_out: ChecksumAddress,
        amount_out: Decimal,
        slippage_tolerance: float = 0.01,
        deadline_seconds: int = 1200,
        return_built_tx: bool = False,
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
        amount_out_atomic = self._convert_decimal_to_atomic(amount_out)
        
        # Create swap path
        path = [token_in, token_out]
        
        # Get required input amount
        amounts_in = await self._chain_client.univ2_router.get_amounts_in(amount_out_atomic, path)
        expected_in = amounts_in[0]  # Input amount is the first element
        
        # Calculate maximum input with slippage
        amount_in_max = int(expected_in * (1 + slippage_tolerance))
        
        # Calculate deadline
        deadline = int(time.time()) + deadline_seconds
        
        if token_in != self._chain_client.weth_address:
            token_in_contract = self._chain_client.get_erc20(token_in)
            await self._ensure_am_approval(
                token=token_in_contract,
                **kwargs,
            )

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
        
        if return_built_tx:
            return await self._scheduler.return_transaction_data(swap_tx)
        return await self._scheduler.send(swap_tx)

    async def get_swap_quote(
        self,
        token_in: ChecksumAddress,
        token_out: ChecksumAddress,
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
        amount_in_atomic = self._convert_decimal_to_atomic(amount_in)
        
        # Create swap path
        path = [token_in, token_out]
        
        # Get expected output amount
        amounts_out = await self._chain_client.univ2_router.get_amounts_out(amount_in_atomic, path)
        expected_out_atomic = amounts_out[1]
        
        # Convert back to decimal units
        expected_out = self._convert_atomic_to_decimal(expected_out_atomic)
        
        # Calculate effective price
        effective_price = expected_out / amount_in if amount_in > 0 else Decimal('0')
        
        return expected_out, effective_price

    async def get_token_balance(self, token_address: ChecksumAddress) -> int:
        """
        Get the balance of a token in the wallet.
        """
        return await self._chain_client.get_erc20(token_address).balance_of(self.wallet_address)
    
    async def get_weth_balance(self) -> Decimal:
        """
        Get the balance of WETH in the wallet.
        """
        weth_token = Token(address=self._chain_client.weth_address, decimals=18, name="Wrapped Ether", symbol="WETH", total_supply=None)
        return weth_token.convert_amount_to_quantity(await self.get_token_balance(self._chain_client.weth_address))

    async def wrap_eth(
            self, amount: Decimal, return_built_tx: bool = False, **kwargs: Unpack[TxParams]
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

        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def unwrap_eth(
            self, amount: Decimal, return_built_tx: bool = False, **kwargs: Unpack[TxParams]
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
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    # ================= APPROVE OPERATIONS =================

    async def approve_operator(self, operator_address: ChecksumAddress,
                               roles: int = 0,
                               return_built_tx: bool = False,
                               **kwargs: Unpack[TxParams]):
        """
        Approve an operator to act on behalf of the account.

        Args:
            operator_address: Address of the operator to approve
            roles: Integer representing roles to assign to the operator
            **kwargs: Additional transaction parameters

        Returns:
            Transaction hash from the approve_operator operation
        """
        logger.info(f"Approving operator {operator_address} for account {self.wallet_address} with roles {roles}")

        tx = self._chain_client.account_manager.approve_operator(
            account=self.wallet_address,
            operator=operator_address,
            roles=roles,
            **kwargs,
        )
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send(tx)

    async def disapprove_operator(self, operator_address: ChecksumAddress,
                                  roles: int,
                                  **kwargs: Unpack[TxParams]):
        """
        Disapprove an operator from acting on behalf of the account.

        Args:
            operator_address: Address of the operator to disapprove
            roles: Integer representing roles to disapprove
            **kwargs: Additional transaction parameters

        Returns:
            Transaction hash from the disapprove_operator operation
        """
        logger.info(f"Disapproving operator {operator_address} for account {self.wallet_address} with roles {roles}")

        return await self._scheduler.send(self._chain_client.account_manager.disapprove_operator(
            account=self.wallet_address,
            operator=operator_address,
            roles=roles,
            **kwargs
        ))

    async def get_tob(self, market_address: ChecksumAddress) -> tuple[Decimal, Decimal]:
        """
        Get the top of book for a market.
        Returns:
            Tuple of (best bid price, best ask price)
        """
        clob = self._chain_client.get_clob(market_address)
        best_bid, best_ask = await clob.get_tob()
        best_bid = self._convert_atomic_to_decimal(best_bid)
        best_ask = self._convert_atomic_to_decimal(best_ask)
        return best_bid, best_ask
    
    def spot_place_order_tx(
            self,
            market_address: ChecksumAddress,
            side: Side,
            amount: int,
            price: int,
            time_in_force: TiF,
            client_order_id: int,
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
        clob = self._chain_client.get_clob(market_address)
        return clob.place_order(
            account=self.wallet_address,
            args=PlaceOrderArgs(
                side=side,
                amount=amount,
                builder_code=HexBytes('00' * 32),
                expiry_time=0,
                base_denominated=True,
                limit_price=price,
                tif=time_in_force,
                client_order_id=client_order_id,
            ),
            **kwargs,
        )

    async def spot_place_order(
            self,
            market_address: ChecksumAddress,
            side: Side,
            amount: Decimal,
            price: Decimal,
            time_in_force: TiF,
            client_order_id: int = 0,
            return_order: bool = False,
            return_built_tx: bool = False,
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
        amount_atomic = self._convert_decimal_to_atomic(amount)
        price_atomic = self._convert_decimal_to_atomic(price)

        clob = self._chain_client.get_clob(market_address)
        tx = self.spot_place_order_tx(
            market_address=market_address,
            side=side,
            amount=amount_atomic,
            price=price_atomic,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            **kwargs,
        ).with_event(clob.contract.events.LimitOrderProcessed())
        
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        if return_order:
            return await self._scheduler.send_wait(tx)
        else:
            return await self._scheduler.send(tx)

    def amend_order_tx(
            self,
            market_address: ChecksumAddress,
            order_id: int,
            amount_atomic: int,
            price_atomic: int,
            side: Side,
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
        clob = self._chain_client.get_clob(market_address)

        # Create amend args
        args = AmendArgs(
            order_or_client_id=order_id,
            amount_in_base=amount_atomic,
            price=price_atomic,
            cancel_timestamp=0,
            side=side.value,
        )

        # Return the transaction
        return clob.amend(account=self.wallet_address, args=args, **kwargs)

    async def spot_amend_order(
            self,
            market_address: ChecksumAddress,
            order_id: int,
            side: Side,
            new_amount: Decimal,
            new_price: Decimal,
            return_built_tx: bool = False,
            **kwargs,
    ):
        """
        Amend an existing order.

        Args:
            market: Market the order is on
            order_id: ID of the order to amend
            side: Order side
            new_amount: New amount for the order
            new_price: New price for the order
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt from the amend operation
        """
        amount_atomic = self._convert_decimal_to_atomic(new_amount)
        price_atomic = self._convert_decimal_to_atomic(new_price)

        # Create and execute transaction
        clob = self._chain_client.get_clob(market_address)
        tx = self.amend_order_tx(
            market_address=market_address, 
            order_id=order_id, 
            amount_atomic=amount_atomic,
            price_atomic=price_atomic,
            side=side,
            **kwargs
        ).with_event(clob.contract.events.OrderAmended())
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send_wait(tx)

    def spot_cancel_order_tx(
            self, market_address: ChecksumAddress, order_ids: list[int], **kwargs
    ) -> TypedContractFunction[Any]:
        """
        Cancel an existing order using the router contract.

        Args:
            market: Market the order is on
            order_ids: IDs of the orders to cancel
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """

        clob = self._chain_client.get_clob(market_address)
        return clob.cancel(account=self.wallet_address, order_or_client_ids=order_ids, **kwargs)

    async def spot_cancel_orders(self, market_address: ChecksumAddress, order_ids: list[int], return_built_tx: bool = False, **kwargs):
        """
        Cancel existing orders using the router contract.

        Args:
            market_address: Address of the market to cancel orders on
            order_ids: IDs of the orders to cancel
            **kwargs: Additional transaction parameters

        Returns:
            Transaction receipt of the cancellation
        """
        clob = self._chain_client.get_clob(market_address)
        tx = self.spot_cancel_order_tx(market_address=market_address, order_ids=order_ids, **kwargs).with_event(clob.contract.events.OrderCanceled())
        if return_built_tx:
            return await self._scheduler.return_transaction_data(tx)
        return await self._scheduler.send_wait(tx)

    async def get_account_manager_balance(
            self, token_address: ChecksumAddress, account: ChecksumAddress | None = None
    ) -> tuple[Decimal, Decimal]:
        """
        Get token balance for an account both on-chain and in the account manager.

        Args:
            token_address: Address of token to check
            account: Account to check (defaults to sender address)

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """
        account = account if account else self.wallet_address
        token = self._chain_client.get_erc20(token_address)

        wallet_balance_atomic = await token.balance_of(account)
        wallet_balance = self._convert_atomic_to_decimal(wallet_balance_atomic)

        exchange_balance_atomic = await self._chain_client.account_manager.get_account_balance(
            account=account,
            token=token_address,
        )
        exchange_balance = self._convert_atomic_to_decimal(exchange_balance_atomic)

        return wallet_balance, exchange_balance
