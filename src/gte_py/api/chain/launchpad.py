from typing import Unpack

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.types import TxParams

from gte_py.api.chain.utils import TypedContractFunction, load_abi


class LaunchpadError(Exception):
    """Base exception for Launchpad contract errors"""

    pass


class Launchpad:
    """
    Python wrapper for the GTE Launchpad smart contract.
    Provides methods to interact with the Launchpad functionality including:
    - Token launches
    - Bonding curve trading
    - Fee management
    """

    def __init__(
        self,
        web3: AsyncWeb3,
        contract_address: str,
    ):
        """
        Initialize the GTELaunchpad wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the Launchpad contract
        """
        self.web3 = web3
        self.address = web3.to_checksum_address(contract_address)

        abi = load_abi("launchpad")
        self.contract = self.web3.eth.contract(address=self.address, abi=abi)

    # ================= READ METHODS =================

    def get_base_scaling(self) -> int:
        """Get the base token scaling factor."""
        return self.contract.functions.BASE_SCALING().call()

    def get_bonding_supply(self) -> int:
        """Get the bonding curve supply."""
        return self.contract.functions.BONDING_SUPPLY().call()

    def get_launch_fee(self) -> int:
        """Get the launch fee."""
        return self.contract.functions.LAUNCH_FEE().call()

    def get_quote_scaling(self) -> int:
        """Get the quote token scaling factor."""
        return self.contract.functions.QUOTE_SCALING().call()

    def get_total_supply(self) -> int:
        """Get the total supply."""
        return self.contract.functions.TOTAL_SUPPLY().call()

    def get_bonding_curve(self) -> ChecksumAddress:
        """Get the bonding curve address."""
        return self.contract.functions.bondingCurve().call()

    def get_event_nonce(self) -> int:
        """Get the event nonce."""
        return self.contract.functions.eventNonce().call()

    def get_gte_router(self) -> ChecksumAddress:
        """Get the GTE Router address."""
        return self.contract.functions.gteRouter().call()

    def get_launches(self, launch_token: str) -> dict:
        """
        Get launch details for a token.

        Args:
            launch_token: Address of the launched token

        Returns:
            Dictionary containing launch details
        """
        launch_token = self.web3.to_checksum_address(launch_token)
        active, bonding_curve, quote, quote_scaling, base_scaling, base_sold, quote_bought = (
            self.contract.functions.launches(launch_token).call()
        )

        return {
            "active": active,
            "bonding_curve": bonding_curve,
            "quote": quote,
            "quote_scaling": quote_scaling,
            "base_scaling": base_scaling,
            "base_sold_from_curve": base_sold,
            "quote_bought_by_curve": quote_bought,
        }

    def get_owner(self) -> ChecksumAddress:
        """Get the contract owner."""
        return self.contract.functions.owner().call()

    def get_ownership_handover_expires_at(self, pending_owner: str) -> int:
        """
        Get the expiration time for an ownership handover request.

        Args:
            pending_owner: Address of the pending owner

        Returns:
            Timestamp when the handover expires
        """
        pending_owner = self.web3.to_checksum_address(pending_owner)
        return self.contract.functions.ownershipHandoverExpiresAt(pending_owner).call()

    def get_quote_asset(self) -> ChecksumAddress:
        """Get the quote asset address."""
        return self.contract.functions.quoteAsset().call()

    def get_univ2_router(self) -> ChecksumAddress:
        """Get the UniswapV2 Router address."""
        return self.contract.functions.uniV2Router().call()

    def quote_base_for_quote(self, token: str, quote_amount: int, is_buy: bool) -> int:
        """
        Quote base amount for a given quote amount.

        Args:
            token: Address of the token
            quote_amount: Amount of quote tokens
            is_buy: Whether this is a buy or sell

        Returns:
            Amount of base tokens
        """
        token = self.web3.to_checksum_address(token)
        return self.contract.functions.quoteBaseForQuote(token, quote_amount, is_buy).call()

    def quote_quote_for_base(self, token: str, base_amount: int, is_buy: bool) -> int:
        """
        Quote  amount for a given base amount.

        Args:
            token: Address of the token
            base_amount: Amount of base tokens
            is_buy: Whether this is a buy or sell

        Returns:
            Amount of quote tokens
        """
        token = self.web3.to_checksum_address(token)
        return self.contract.functions.quoteQuoteForBase(token, base_amount, is_buy).call()

    # ================= WRITE METHODS =================

    def buy(
        self,
        token: str,
        recipient: str,
        amount_out_base: int,
        max_amount_in_quote: int,
        **kwargs: Unpack[TxParams],
    ) -> TypedContractFunction[HexBytes]:
        """
        Buy base tokens with quote tokens.

        Args:
            token: Address of the token
            recipient: Address to receive the tokens
            amount_out_base: Amount of base tokens to buy
            max_amount_in_quote: Maximum amount of quote tokens to spend
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction with the transaction
        """
        token = self.web3.to_checksum_address(token)
        recipient = self.web3.to_checksum_address(recipient)

        func = self.contract.functions.buy(token, recipient, amount_out_base, max_amount_in_quote)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Cancel an ownership handover request.

        Args:
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.cancelOwnershipHandover()

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def complete_ownership_handover(
        self, pending_owner: str, **kwargs
    ) -> TypedContractFunction[HexBytes]:
        """
        Complete an ownership handover.

        Args:
            pending_owner: Address of the pending owner
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        pending_owner = self.web3.to_checksum_address(pending_owner)
        func = self.contract.functions.completeOwnershipHandover(pending_owner)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def initialize(self, owner: str, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Initialize the contract with an owner.

        Args:
            owner: Address of the owner
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        owner = self.web3.to_checksum_address(owner)
        func = self.contract.functions.initialize(owner)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def launch(
        self, name: str, symbol: str, media_uri: str, value: int = 0, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[HexBytes]:
        """
        Launch a new token.

        Args:
            name: Name of the token
            symbol: Symbol of the token
            media_uri: Media URI for the token
            value: ETH value to send with the transaction (for launch fee)
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.launch(name, symbol, media_uri)

        params = {
            "value": value,
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def pull_fees(self, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Pull accumulated fees.

        Args:
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.pullFees()

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Renounce ownership of the contract.

        Args:
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.renounceOwnership()

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def request_ownership_handover(self, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Request an ownership handover.

        Args:
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.requestOwnershipHandover()

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def sell(
        self,
        token: str,
        recipient: str,
        amount_in_base: int,
        min_amount_out_quote: int,
        **kwargs: Unpack[TxParams],
    ) -> TypedContractFunction[HexBytes]:
        """
        Sell base tokens for quote tokens.

        Args:
            token: Address of the token
            recipient: Address to receive the quote tokens
            amount_in_base: Amount of base tokens to sell
            min_amount_out_quote: Minimum amount of quote tokens to receive
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        token = self.web3.to_checksum_address(token)
        recipient = self.web3.to_checksum_address(recipient)

        func = self.contract.functions.sell(token, recipient, amount_in_base, min_amount_out_quote)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def set_virtual_reserves(
        self, virtual_base: int, virtual_quote: int, **kwargs
    ) -> TypedContractFunction[HexBytes]:
        """
        Set virtual reserves for the bonding curve.

        Args:
            virtual_base: Virtual base reserves
            virtual_quote: Virtual quote reserves
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.setVirtualReserves(virtual_base, virtual_quote)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def transfer_ownership(self, new_owner: str, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Transfer ownership of the contract.

        Args:
            new_owner: Address of the new owner
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        new_owner = self.web3.to_checksum_address(new_owner)
        func = self.contract.functions.transferOwnership(new_owner)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def update_bonding_curve(
        self, new_bonding_curve: str, **kwargs
    ) -> TypedContractFunction[HexBytes]:
        """
        Update the bonding curve address.

        Args:
            new_bonding_curve: Address of the new bonding curve
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        new_bonding_curve = self.web3.to_checksum_address(new_bonding_curve)
        func = self.contract.functions.updateBondingCurve(new_bonding_curve)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def update_init_code_hash(self, new_hash: bytes, **kwargs) -> TypedContractFunction[HexBytes]:
        """
        Update the init code hash.

        Args:
            new_hash: New init code hash
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        func = self.contract.functions.updateInitCodeHash(new_hash)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)

    def update_quote_asset(
        self, new_quote_asset: str, **kwargs
    ) -> TypedContractFunction[HexBytes]:
        """
        Update the quote asset address.

        Args:
            new_quote_asset: Address of the new quote asset
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction with the transaction
        """
        new_quote_asset = self.web3.to_checksum_address(new_quote_asset)
        func = self.contract.functions.updateQuoteAsset(new_quote_asset)

        params = {
            **kwargs,
        }

        return TypedContractFunction(func, params)
