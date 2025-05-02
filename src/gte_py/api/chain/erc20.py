"""Python wrapper for ERC20 token contracts."""

from typing import TypeVar, Dict, Any

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from .utils import TypedContractFunction, load_abi

T = TypeVar("T")


class ERC20:
    """
    Python wrapper for ERC20 token contracts.
    Provides methods to interact with standard ERC20 functionality.
    """

    def __init__(
            self,
            web3: AsyncWeb3,
            contract_address: ChecksumAddress,
    ):
        """
        Initialize the ERC20 wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the ERC20 token contract
        """
        self.web3 = web3
        self.address = contract_address

        loaded_abi = load_abi("erc20")

        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)
        self._token_info_cache: Dict[str, Any] = {}

    # ================= READ METHODS =================

    async def name(self) -> str:
        """Get the name of the token."""
        if "name" not in self._token_info_cache:
            self._token_info_cache["name"] = await self.contract.functions.name().call()
        return self._token_info_cache["name"]

    async def symbol(self) -> str:
        """Get the symbol of the token."""
        if "symbol" not in self._token_info_cache:
            self._token_info_cache["symbol"] = await self.contract.functions.symbol().call()
        return self._token_info_cache["symbol"]

    async def decimals(self) -> int:
        """Get the number of decimals the token uses."""
        if "decimals" not in self._token_info_cache:
            self._token_info_cache["decimals"] = await self.contract.functions.decimals().call()
        return self._token_info_cache["decimals"]

    async def total_supply(self) -> int:
        """Get the total token supply in token base units."""
        return await self.contract.functions.totalSupply().call()

    async def balance_of(self, account: ChecksumAddress) -> int:
        """
        Get the token balance of an account.

        Args:
            account: Address to check balance of

        Returns:
            Token balance in token base units
        """
        return await self.contract.functions.balanceOf(account).call()

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
            self, recipient: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[bool]:
        """
        Transfer tokens to a specified address.

        Args:
            recipient: Address to transfer tokens to
            amount: Amount to transfer in token base units
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.transfer(recipient, amount)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def approve(
            self, spender: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[bool]:
        """
        Approve the passed address to spend the specified amount of tokens on behalf of the sender.

        Args:
            spender: Address which will spend the funds
            amount: Amount of tokens to approve in token base units
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.approve(spender, amount)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def transfer_from(
            self,
            sender: ChecksumAddress,
            recipient: ChecksumAddress,
            amount: int,
            **kwargs: Unpack[TxParams],
    ) -> TypedContractFunction[bool]:
        """
        Transfer tokens from one address to another.

        Args:
            sender: Address to transfer tokens from
            recipient: Address to transfer tokens to
            amount: Amount to transfer in token base units
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.transferFrom(sender, recipient, amount)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def increase_allowance(
            self, spender: ChecksumAddress, added_value: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[bool]:
        """
        Increase the allowance granted to `spender` by the caller.

        Args:
            spender: Address which will spend the funds
            added_value: Amount of tokens to increase allowance by
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.increaseAllowance(spender, added_value)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def decrease_allowance(
            self, spender: ChecksumAddress, subtracted_value: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[bool]:
        """
        Decrease the allowance granted to `spender` by the caller.

        Args:
            spender: Address which will spend the funds
            subtracted_value: Amount of tokens to decrease allowance by
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        func = self.contract.functions.decreaseAllowance(spender, subtracted_value)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    # ================= HELPER METHODS =================

    async def convert_amount_to_quantity(self, amount: int) -> float:
        """
        Convert an amount in token base units to a human-readable float.

        Args:
            amount: Amount in token base units

        Returns:
            Human-readable amount as a float
        """
        assert isinstance(amount, int), f"Amount {amount} must be an integer"
        decimals = await self.decimals()
        return amount / (10 ** decimals)

    def approve_max(
            self, spender: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[bool]:
        """
        Approve the maximum possible amount for a spender.

        Args:
            spender: Address which will spend the funds
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that returns a boolean success value
        """
        # 2^256 - 1, the maximum uint256 value
        max_uint256 = 2 ** 256 - 1
        return self.approve(spender, max_uint256, **kwargs)
