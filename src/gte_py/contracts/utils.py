import importlib.resources as pkg_resources
import json
import time
from typing import Any, Generic, TypeVar

from web3.contract.contract import ContractFunction
from web3.types import HexBytes, TxParams


def get_current_timestamp() -> int:
    """Get the current Unix timestamp in seconds."""
    return int(time.time())


def create_deadline(minutes_in_future: int = 30) -> int:
    """
    Create a deadline timestamp for transactions.

    Args:
        minutes_in_future: Number of minutes in the future for the deadline

    Returns:
        Unix timestamp in seconds
    """
    return get_current_timestamp() + (minutes_in_future * 60)


def to_wei(amount: float, decimals: int = 18) -> int:
    """
    Convert a decimal amount to wei (or equivalent for other tokens).

    Args:
        amount: Decimal amount
        decimals: Number of decimals of the token

    Returns:
        Integer amount in wei
    """
    return int(amount * (10**decimals))


def from_wei(amount: int, decimals: int = 18) -> float:
    """
    Convert wei amount to decimal.

    Args:
        amount: Wei amount
        decimals: Number of decimals of the token

    Returns:
        Decimal amount
    """
    return amount / (10**decimals)


# Fix for the Traversable issue
def load_abi(abi_name: str) -> list[dict[str, Any]]:
    """
    Load ABI from a file or package resources.

    Args:
        abi_name: Name of the ABI file (without .json extension)


    Returns:
        The loaded ABI as a Python object

    Raises:
        ValueError: If the ABI file cannot be found
    """
    # Look in the abi directory first
    abi_file = f"{abi_name}.json"

    package_path = pkg_resources.files("gte_py.contracts.abi")
    file_path = package_path.joinpath(abi_file)
    # Convert Traversable to string path
    str_path = str(file_path)
    with open(str_path) as f:
        return json.load(f)


T = TypeVar("T")


class TypedContractFunction(Generic[T]):
    """Generic transaction wrapper with typed results and async support"""

    def __init__(self, func: ContractFunction, params: TxParams | Any = None):
        self.func = func  # Bound contract function (with arguments)
        self.params = params  # Transaction parameters
        self.result: T | None = None
        self.receipt: dict[str, Any] | None = None
        self.tx_hash: HexBytes | None = None

    def call(self) -> T:
        """Synchronous read operation"""
        self.result = self.func.call(self.params)
        return self.result

    def send(self) -> HexBytes:
        """Synchronous write operation"""
        self.tx_hash = self.func.transact(self.params)
        return self.tx_hash

    def retrieve(self) -> T:
        """
        Retrieves the result of a transaction.

        For read operations (call), returns the cached result.
        For write operations (send), waits for the transaction to be mined
        and returns the transaction receipt.

        Returns:
            The result of the operation

        Raises:
            ValueError: If the transaction failed or no transaction has been sent
        """
        if self.result is not None:
            return self.result

        if self.tx_hash is None:
            raise ValueError("Transaction hash is None. Call send() first.")

        # Wait for the transaction to be mined
        # self.receipt = self.func.w3.eth.wait_for_transaction_receipt(self.tx_hash)
        #
        # if self.receipt["status"] != 1:
        #     raise ValueError(f"Transaction failed: {self.receipt}")
        raise NotImplementedError
