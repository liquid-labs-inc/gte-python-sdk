"""Python wrapper for ERC20 token contracts."""

from typing import TypeVar, Optional, Dict, Any

from eth_typing import ChecksumAddress
from web3 import Web3

from .utils import TypedContractFunction, load_abi

T = TypeVar("T")


class ERC20:
    """
    Python wrapper for ERC20 token contracts.
    Provides methods to interact with standard ERC20 functionality.
    """

    def __init__(
            self,
            web3: Web3,
            contract_address: ChecksumAddress,
    ):
        """
        Initialize the ERC20 wrapper.

        Args:
            web3: Web3 instance connected to a provider
            contract_address: Address of the ERC20 token contract
            abi_path: Path to a custom ABI JSON file (optional, defaults to standard ERC20 ABI)
        """
        self.web3 = web3
        self.address = contract_address

        loaded_abi = load_abi("erc20")

        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)
        self._token_info_cache: Dict[str, Any] = {}

    # ================= READ METHODS =================

    def name(self) -> str:
        """Get the name of the token."""
        if "name" not in self._token_info_cache:
            self._token_info_cache["name"] = self.contract.functions.name().call()
        return self._token_info_cache["name"]

    def symbol(self) -> str:
        """Get the symbol of the token."""
        if "symbol" not in self._token_info_cache:
            self._token_info_cache["symbol"] = self.contract.functions.symbol().call()
        return self._token_info_cache["symbol"]

    def decimals(self) -> int:
        """Get the number of decimals the token uses."""
        if "decimals" not in self._token_info_cache:
            self._token_info_cache["decimals"] = self.contract.functions.decimals().call()
        return self._token_info_cache["decimals"]

    def total_supply(self) -> int:
        """Get the total token supply in token base units."""
        return self.contract.functions.totalSupply().call()

    def balance_of(self, account: ChecksumAddress) -> int:
        """
        Get the token balance of an account.

        Args:
            account: Address to check balance of

        Returns:
            Token balance in token base units
        """
        return self.contract.functions.balanceOf(account).call()

    def allowance(self, owner: ChecksumAddress, spender: ChecksumAddress) -> int:
        """
        Get the remaining number of tokens that `spender` is allowed to spend on behalf of `owner`.

        Args:
            owner: Address that owns the tokens
            spender: Address that can spend the tokens

        Returns:
            Remaining allowance in token base units
        """
        return self.contract.functions.allowance(owner, spender).call()

    # ================= WRITE METHODS =================

    def transfer(
            self,
            recipient: ChecksumAddress,
            amount: int,
            sender_address: ChecksumAddress,
            **kwargs
    ) -> TypedContractFunction[bool]:
        """
        Transfer tokens to a specified address.

        Args:
            recipient: Address to transfer tokens to
            amount: Amount to transfer in token base units
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.transfer(recipient, amount)
        params = {
            "from": sender_address,
            "nonce": self.web3.eth.get_transaction_count(sender_address),
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def approve(
            self,
            spender: ChecksumAddress,
            amount: int,
            sender_address: ChecksumAddress,
            **kwargs
    ) -> TypedContractFunction[bool]:
        """
        Approve the passed address to spend the specified amount of tokens on behalf of the sender.

        Args:
            spender: Address which will spend the funds
            amount: Amount of tokens to approve in token base units
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.approve(spender, amount)
        params = {
            "from": sender_address,
            "nonce": self.web3.eth.get_transaction_count(sender_address),
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def transfer_from(
            self,
            sender: ChecksumAddress,
            recipient: ChecksumAddress,
            amount: int,
            sender_address: ChecksumAddress,
            **kwargs
    ) -> TypedContractFunction[bool]:
        """
        Transfer tokens from one address to another.

        Args:
            sender: Address to transfer tokens from
            recipient: Address to transfer tokens to
            amount: Amount to transfer in token base units
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.transferFrom(sender, recipient, amount)
        params = {
            "from": sender_address,
            "nonce": self.web3.eth.get_transaction_count(sender_address),
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def increase_allowance(
            self,
            spender: ChecksumAddress,
            added_value: int,
            sender_address: ChecksumAddress,
            **kwargs
    ) -> TypedContractFunction[bool]:
        """
        Increase the allowance granted to `spender` by the caller.

        Args:
            spender: Address which will spend the funds
            added_value: Amount of tokens to increase allowance by
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.increaseAllowance(spender, added_value)
        params = {
            "from": sender_address,
            "nonce": self.web3.eth.get_transaction_count(sender_address),
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def decrease_allowance(
            self,
            spender: ChecksumAddress,
            subtracted_value: int,
            sender_address: ChecksumAddress,
            **kwargs
    ) -> TypedContractFunction[bool]:
        """
        Decrease the allowance granted to `spender` by the caller.

        Args:
            spender: Address which will spend the funds
            subtracted_value: Amount of tokens to decrease allowance by
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.decreaseAllowance(spender, subtracted_value)
        params = {
            "from": sender_address,
            "nonce": self.web3.eth.get_transaction_count(sender_address),
            **kwargs,
        }
        return TypedContractFunction(func, params)

    # ================= HELPER METHODS =================

    def format_amount(self, amount: float) -> int:
        """
        Convert a float amount to the token's base units.

        Args:
            amount: Amount as a float (e.g., 1.5 ETH)

        Returns:
            Amount in token base units (e.g., 1500000000000000000 wei)
        """
        decimals = self.decimals()
        return int(amount * (10 ** decimals))

    def format_amount_readable(self, amount: int) -> float:
        """
        Convert an amount in token base units to a human-readable float.

        Args:
            amount: Amount in token base units

        Returns:
            Human-readable amount as a float
        """
        decimals = self.decimals()
        return amount / (10 ** decimals)

    def approve_max(
            self,
            spender: ChecksumAddress,
            sender_address: ChecksumAddress,
            **kwargs
    ) -> TypedContractFunction[bool]:
        """
        Approve the maximum possible amount for a spender.

        Args:
            spender: Address which will spend the funds
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        # 2^256 - 1, the maximum uint256 value
        max_uint256 = 2 ** 256 - 1
        return self.approve(spender, max_uint256, sender_address, **kwargs)

    def has_sufficient_allowance(
            self,
            owner: ChecksumAddress,
            spender: ChecksumAddress,
            amount: int
    ) -> bool:
        """
        Check if the spender has sufficient allowance to spend the given amount.

        Args:
            owner: Address that owns the tokens
            spender: Address that wants to spend the tokens
            amount: Amount to check against the allowance

        Returns:
            True if allowance is sufficient, False otherwise
        """
        current_allowance = self.allowance(owner, spender)
        return current_allowance >= amount

    def has_sufficient_balance(self, account: ChecksumAddress, amount: int) -> bool:
        """
        Check if an account has sufficient balance for a transaction.

        Args:
            account: Address to check balance of
            amount: Amount to check against the balance

        Returns:
            True if balance is sufficient, False otherwise
        """
        current_balance = self.balance_of(account)
        return current_balance >= amount
