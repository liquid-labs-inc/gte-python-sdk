import importlib.resources as pkg_resources
import json
import logging
import time
from typing import Any, Generic, TypeVar, Callable

from eth_account import Account
from eth_account.types import PrivateKeyType
from hexbytes import HexBytes
from web3.contract.contract import ContractFunction
from web3.types import TxParams, EventData

logger = logging.getLogger(__name__)


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
    return int(amount * (10 ** decimals))


def from_wei(amount: int, decimals: int = 18) -> float:
    """
    Convert wei amount to decimal.

    Args:
        amount: Wei amount
        decimals: Number of decimals of the token

    Returns:
        Decimal amount
    """
    return amount / (10 ** decimals)


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


def lift_callable(func: Callable[[EventData], T | None]) -> Callable[[EventData], T]:
    return func  # type: ignore


class TypedContractFunction(Generic[T]):
    """Generic transaction wrapper with typed results and async support"""
    __slots__ = ["web3", "func", "params", "event", "event_parser", "result", "receipt", "tx_hash"]

    def __init__(self, func: ContractFunction, params: TxParams | Any = None):
        self.web3 = func.w3
        self.func = func  # Bound contract function (with arguments)
        self.params = params  # Transaction parameters
        self.event = None
        self.event_parser: Callable[[EventData], T] | None = None
        self.result: T | None = None
        self.receipt: dict[str, Any] | None = None
        self.tx_hash: HexBytes | None = None

    def with_event(self, event, parser: Callable[[EventData], T] | None = None) -> "TypedContractFunction[T]":
        """Set the event to listen for"""
        self.event = event
        self.event_parser = parser
        return self

    def call(self) -> T:
        """Synchronous read operation"""
        self.result = self.func.call(self.params)
        return self.result

    def send(self, private_key: PrivateKeyType | None = None) -> HexBytes:
        """Synchronous write operation"""
        if private_key:
            tx = self.params
            local_account = Account.from_key(private_key)
            if 'from' not in tx:
                tx['from'] = local_account.address
            if 'nonce' not in tx:
                tx['nonce'] = self.web3.eth.get_transaction_count(local_account.address)
            logger.info('Sending %s with %s', self.func, tx)
            tx = self.func.build_transaction(tx)
            # Sign and send the transaction
            signed = self.web3.eth.account.sign_transaction(tx, private_key)
            self.tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        else:
            tx = self.params
            logger.info('Sending %s with %s', self.func, tx)
            tx = self.func.build_transaction(tx)
            # Send the transaction with default account
            self.tx_hash = self.web3.eth.send_transaction(tx)

        return self.tx_hash

    def build_transaction(self) -> TxParams:
        return self.func.build_transaction(self.params)

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
        if self.event is None:
            return None
        # Wait for the transaction to be mined
        self.receipt = self.web3.eth.wait_for_transaction_receipt(self.tx_hash)
        logs = self.event.process_receipt(self.receipt)

        if len(logs) == 0:
            return None
        if len(logs) > 1:
            logger.warning("Multiple logs found, expected one: %s", logs)

        if self.event_parser:
            return self.event_parser(logs[0])
        return logs[0]['args']

    def send_wait(self, private_key: PrivateKeyType | None = None) -> T:
        self.send(private_key)
        return self.retrieve()
