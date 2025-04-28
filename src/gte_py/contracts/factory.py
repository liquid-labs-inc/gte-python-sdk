"""Python wrapper for the GTE CLOB Factory contract."""

import logging
from typing import TypeVar, List

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from .utils import TypedContractFunction, load_abi

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CLOBFactory:
    """
    Python wrapper for the GTE CLOB Factory contract.
    This contract manages the creation and registry of CLOB markets on the GTE platform.
    """

    def __init__(
            self,
            web3: AsyncWeb3,
            contract_address: ChecksumAddress,
    ):
        """
        Initialize the CLOBFactory wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the CLOBFactory contract
        """
        self.web3 = web3
        self.address = contract_address

        loaded_abi = load_abi("factory")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

    # ================= READ METHODS =================

    async def owner(self) -> ChecksumAddress:
        """Get the owner of the factory."""
        return await self.contract.functions.owner().call()

    async def beacon(self) -> ChecksumAddress:
        """Get the beacon address used for proxy contracts."""
        return await self.contract.functions.beacon().call()

    async def get_fee_recipient(self) -> ChecksumAddress:
        """Get the address that receives fees from CLOB markets."""
        return await self.contract.functions.getFeeRecipient().call()

    async def get_event_nonce(self) -> int:
        """Get the current event nonce."""
        return await self.contract.functions.getEventNonce().call()

    async def max_num_orders(self) -> int:
        """Get the maximum number of orders per market."""
        return await self.contract.functions.maxNumOrders().call()

    async def get_market_address(self, quote_token: ChecksumAddress, base_token: ChecksumAddress) -> ChecksumAddress:
        """
        Get the address of a market given quote and base tokens.

        Args:
            quote_token: Address of the quote token
            base_token: Address of the base token

        Returns:
            The address of the market
        """
        return await self.contract.functions.getMarketAddress(quote_token, base_token).call()

    async def is_market(self, market: ChecksumAddress) -> bool:
        """
        Check if an address is a valid market created by this factory.

        Args:
            market: Address to check

        Returns:
            True if the address is a market, False otherwise
        """
        return await self.contract.functions.isMarket(market).call()

    async def get_account_balance(self, account: ChecksumAddress, token: ChecksumAddress) -> int:
        """
        Get the balance of a token for an account.

        Args:
            account: Address of the account
            token: Address of the token

        Returns:
            The balance amount
        """
        return await self.contract.functions.getAccountBalance(account, token).call()

    async def get_fee_tier(self, account: ChecksumAddress) -> int:
        """
        Get the fee tier for an account.

        Args:
            account: Address of the account

        Returns:
            The fee tier enum value
        """
        return await self.contract.functions.getFeeTier(account).call()

    async def get_maker_fee_rate(self, fee_tier: int) -> int:
        """
        Get the maker fee rate for a fee tier.

        Args:
            fee_tier: Fee tier enum value

        Returns:
            The maker fee rate in basis points
        """
        return await self.contract.functions.getMakerFeeRate(fee_tier).call()

    async def get_taker_fee_rate(self, fee_tier: int) -> int:
        """
        Get the taker fee rate for a fee tier.

        Args:
            fee_tier: Fee tier enum value

        Returns:
            The taker fee rate in basis points
        """
        return await self.contract.functions.getTakerFeeRate(fee_tier).call()

    async def approved_operators(self, account: ChecksumAddress, operator: ChecksumAddress) -> bool:
        """
        Check if an operator is approved for an account.

        Args:
            account: Address of the account
            operator: Address of the operator

        Returns:
            True if the operator is approved, False otherwise
        """
        return await self.contract.functions.approvedOperators(account, operator).call()

    # ================= WRITE METHODS =================

    def create_market(
            self,
            base_token: ChecksumAddress,
            quote_token: ChecksumAddress,
            settings: dict,
            **kwargs,
    ) -> TypedContractFunction[ChecksumAddress]:
        """
        Create a new market.

        Args:
            base_token: Address of the base token
            quote_token: Address of the quote token
            settings: Market settings dictionary with owner, maxLimitsPerTx, 
                      minLimitOrderAmountInBase, and tickSize
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns the new market address
        """
        func = self.contract.functions.createMarket(base_token, quote_token, settings)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def approve_operator(
            self, operator: ChecksumAddress, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Approve an operator for the sender's account.

        Args:
            operator: Address of the operator to approve
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.approveOperator(operator)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def disapprove_operator(
            self, operator: ChecksumAddress, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Disapprove an operator for the sender's account.

        Args:
            operator: Address of the operator to disapprove
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.disapproveOperator(operator)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def deposit(
            self,
            account: ChecksumAddress,
            token: ChecksumAddress,
            amount: int,
            from_operator: bool,
            **kwargs,
    ) -> TypedContractFunction[None]:
        """
        Deposit tokens for an account.

        Args:
            account: Address of the account to deposit for
            token: Address of the token to deposit
            amount: Amount to deposit
            from_operator: Whether the deposit is from an operator
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.deposit(account, token, amount, from_operator)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def withdraw(
            self,
            account: ChecksumAddress,
            token: ChecksumAddress,
            amount: int,
            to_operator: bool,
            **kwargs,
    ) -> TypedContractFunction[None]:
        """
        Withdraw tokens for an account.

        Args:
            account: Address of the account to withdraw from
            token: Address of the token to withdraw
            amount: Amount to withdraw
            to_operator: Whether the withdrawal is to an operator
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.withdraw(account, token, amount, to_operator)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def set_fee_recipient(
            self, new_fee_recipient: ChecksumAddress, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Set a new fee recipient.

        Args:
            new_fee_recipient: Address of the new fee recipient
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.setFeeRecipient(new_fee_recipient)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def set_account_fee_tiers(
            self,
            accounts: List[ChecksumAddress],
            fee_tiers: List[int],
            **kwargs,
    ) -> TypedContractFunction[None]:
        """
        Set fee tiers for multiple accounts.

        Args:
            accounts: List of account addresses
            fee_tiers: List of fee tier enum values
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.setAccountFeeTiers(accounts, fee_tiers)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def collect_fees(
            self, token: ChecksumAddress, **kwargs
    ) -> TypedContractFunction[int]:
        """
        Collect accumulated fees for a token.

        Args:
            token: Address of the token to collect fees for
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns the amount of fees collected
        """
        func = self.contract.functions.collectFees(token)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def transfer_ownership(
            self, new_owner: ChecksumAddress, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Transfer ownership of the factory.

        Args:
            new_owner: Address of the new owner
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.transferOwnership(new_owner)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def renounce_ownership(
            self, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Renounce ownership of the factory.

        Args:
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.renounceOwnership()
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    # ================= ADVANCED OPERATION METHODS =================

    def credit_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Credit an account with tokens (admin operation).

        Args:
            account: Address of the account to credit
            token: Address of the token to credit
            amount: Amount to credit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.creditAccount(account, token, amount)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def debit_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Debit an account with tokens (admin operation).

        Args:
            account: Address of the account to debit
            token: Address of the token to debit
            amount: Amount to debit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.debitAccount(account, token, amount)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def pull_from_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Pull tokens from an account (admin operation).

        Args:
            account: Address of the account to pull from
            token: Address of the token to pull
            amount: Amount to pull
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.pullFromAccount(account, token, amount)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def push_to_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Push tokens to an account (admin operation).

        Args:
            account: Address of the account to push to
            token: Address of the token to push
            amount: Amount to push
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the transaction
        """
        func = self.contract.functions.pushToAccount(account, token, amount)
        params = {

            **kwargs,
        }
        return TypedContractFunction(func, params)

    def settle_incoming_order(
            self, params: dict, **kwargs
    ) -> TypedContractFunction[int]:
        """
        Settle an incoming order (admin operation).

        Args:
            params: Settlement parameters
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns the taker fee
        """
        if "taker" in params and params["taker"]:
            params["taker"] = self.web3.to_checksum_address(params["taker"])
        if "quoteToken" in params and params["quoteToken"]:
            params["quoteToken"] = self.web3.to_checksum_address(params["quoteToken"])
        if "baseToken" in params and params["baseToken"]:
            params["baseToken"] = self.web3.to_checksum_address(params["baseToken"])

        # Process makerCredits if they exist
        if "makerCredits" in params and params["makerCredits"]:
            for i, credit in enumerate(params["makerCredits"]):
                if "maker" in credit and credit["maker"]:
                    params["makerCredits"][i]["maker"] = self.web3.to_checksum_address(credit["maker"])

        func = self.contract.functions.settleIncomingOrder(params)
        tx_params = {

            **kwargs,
        }
        return TypedContractFunction(func, tx_params)

    # ================= HELPER METHODS =================

    def create_market_settings(
            self,
            owner: ChecksumAddress,
            max_limits_per_tx: int,
            min_limit_order_amount_in_base: int,
            tick_size: int
    ) -> dict:
        """
        Create a settings dictionary for use with create_market.
        
        Args:
            owner: Address of the market owner
            max_limits_per_tx: Maximum number of limits per transaction
            min_limit_order_amount_in_base: Minimum limit order amount in base
            tick_size: Tick size for the market
            
        Returns:
            Settings dictionary
        """
        return {
            "owner": owner,
            "maxLimitsPerTx": max_limits_per_tx,
            "minLimitOrderAmountInBase": min_limit_order_amount_in_base,
            "tickSize": tick_size
        }

    def create_settle_params(
            self,
            taker: ChecksumAddress,
            quote_token: ChecksumAddress,
            base_token: ChecksumAddress,
            side: int,
            settlement: int,
            taker_quote_amount: int,
            taker_base_amount: int,
            maker_credits: List[dict] = None
    ) -> dict:
        """
        Create parameters for settle_incoming_order.
        
        Args:
            taker: Address of the taker
            quote_token: Address of the quote token
            base_token: Address of the base token
            side: Side enum value (BUY=0, SELL=1)
            settlement: Settlement enum value
            taker_quote_amount: Taker quote amount
            taker_base_amount: Taker base amount
            maker_credits: List of maker credit dictionaries each with maker, quoteAmount, and baseAmount
            
        Returns:
            Settlement parameters dictionary
        """
        formatted_maker_credits = []
        if maker_credits:
            for credit in maker_credits:
                formatted_maker_credits.append({
                    "maker": self.web3.to_checksum_address(credit["maker"]) if isinstance(credit["maker"], str) else
                    credit["maker"],
                    "quoteAmount": credit["quoteAmount"],
                    "baseAmount": credit["baseAmount"]
                })

        return {
            "taker": taker,
            "quoteToken": quote_token,
            "baseToken": base_token,
            "side": side,
            "settlement": settlement,
            "takerQuoteAmount": taker_quote_amount,
            "takerBaseAmount": taker_base_amount,
            "makerCredits": formatted_maker_credits
        }

    async def owner_async(self) -> ChecksumAddress:
        """Get the owner of the factory using async call."""
        return await self.contract.functions.owner().call()

    async def beacon_async(self) -> ChecksumAddress:
        """Get the beacon address used for proxy contracts using async call."""
        return await self.contract.functions.beacon().call()

    async def get_fee_recipient_async(self) -> ChecksumAddress:
        """Get the address that receives fees from CLOB markets using async call."""
        return await self.contract.functions.getFeeRecipient().call()

    async def get_event_nonce_async(self) -> int:
        """Get the current event nonce using async call."""
        return await self.contract.functions.getEventNonce().call()

    async def max_num_orders_async(self) -> int:
        """Get the maximum number of orders per market using async call."""
        return await self.contract.functions.maxNumOrders().call()

    async def get_market_address_async(self, quote_token: ChecksumAddress, base_token: ChecksumAddress) -> ChecksumAddress:
        """
        Get the address of the market for a specific token pair using async call.

        Args:
            quote_token: Address of the quote token
            base_token: Address of the base token

        Returns:
            Address of the market contract
        """
        return await self.contract.functions.getMarketAddress(quote_token, base_token).call()

    async def get_maker_fees_async(self) -> int:
        """Get the maker fees as a packed uint256 using async call."""
        return await self.contract.functions.makerFees().call()

    async def get_taker_fees_async(self) -> int:
        """Get the taker fees as a packed uint256 using async call."""
        return await self.contract.functions.takerFees().call()

    async def get_is_market_async(self, market_address: ChecksumAddress) -> bool:
        """
        Check if an address is a registered market using async call.

        Args:
            market_address: Address to check

        Returns:
            True if the address is a registered market, False otherwise
        """
        return await self.contract.functions.isMarket(market_address).call()

    async def get_account_balance_async(self, account: ChecksumAddress, token: ChecksumAddress) -> int:
        """
        Get the account balance for a specific token using async call.

        Args:
            account: Address of the account
            token: Address of the token

        Returns:
            Account balance in token atoms
        """
        return await self.contract.functions.getAccountBalance(account, token).call()
