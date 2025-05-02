import asyncio
import importlib.resources as pkg_resources
import json
import logging
import time
from typing import Any, Generic, TypeVar, Callable, Tuple, Dict, Awaitable

from eth_account import Account
from eth_account.types import PrivateKeyType
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction
from web3.exceptions import ContractCustomError, TransactionNotFound
from web3.middleware import SignAndSendRawMiddlewareBuilder
from web3.types import TxParams, EventData, Nonce

from gte_py.configs import NetworkConfig
from gte_py.error import (
    InsufficientBalance,
    NotFactory,
    FOKNotFilled,
    UnauthorizedAmend,
    UnauthorizedCancel,
    InvalidAmend,
    OrderAlreadyExpired,
    InvalidAccountOrOperator,
    PostOnlyOrderWouldBeFilled,
    MaxOrdersInBookPostNotCompetitive,
    NonPostOnlyAmend,
    ZeroCostTrade,
    ZeroTrade,
    ZeroOrder,
    TransferFromFailed,
)

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

    package_path = pkg_resources.files("gte_py.api.chain.abi")
    file_path = package_path.joinpath(abi_file)
    # Convert Traversable to string path
    str_path = str(file_path)
    with open(str_path) as f:
        return json.load(f)


ERROR_EXCEPTIONS = {
    "0xf4d678b8": InsufficientBalance,
    "0x32cc7236": NotFactory,
    "0x87e393a7": FOKNotFilled,
    "0x60ab4840": UnauthorizedAmend,
    "0x45bb6073": UnauthorizedCancel,
    "0x4b22649a": InvalidAmend,
    "0x3154078e": OrderAlreadyExpired,
    "0x3d104567": InvalidAccountOrOperator,
    "0x52409ba3": PostOnlyOrderWouldBeFilled,
    "0x315ff5e5": MaxOrdersInBookPostNotCompetitive,
    "0xc1008f10": NonPostOnlyAmend,  # Fixed: changed from string to exception class
    "0xd8a00083": ZeroCostTrade,
    "0x4ef36a18": ZeroTrade,
    "0xb82df155": ZeroOrder,
    "0x7939f424": TransferFromFailed,
}


def convert_web3_error(error: ContractCustomError, cause: str) -> Exception:
    """
    Convert a web3.exceptions.ContractCustomError into our custom exception.

    Args:
        error: AsyncWeb3 contract custom error
        cause: The cause of the error, usually the function name or context

    Returns:
        A custom GTE exception
    """
    error_code = error.message
    if error_code in ERROR_EXCEPTIONS:
        exception_class = ERROR_EXCEPTIONS[error_code]
        return exception_class(cause)
    return error  # Return original error if no mapping exists


T = TypeVar("T")


def lift_callable(func: Callable[[EventData], T | None]) -> Callable[[EventData], T]:
    return func  # type: ignore


tx_id = 0


def next_tx_id() -> int:
    """Get the next transaction ID"""
    global tx_id
    tx_id += 1
    return tx_id


class TypedContractFunction(Generic[T]):
    """Generic transaction wrapper with typed results and async support"""

    __slots__ = [
        "web3",
        "func_call",
        "params",
        "event",
        "event_parser",
        "result",
        "receipt",
        "tx_hash",
        "tx_id",
    ]

    def __init__(self, func_call: AsyncContractFunction, params: TxParams | Any = None):
        self.web3: AsyncWeb3 = func_call.w3
        self.func_call = func_call  # Bound contract function (with arguments)
        self.params = params  # Transaction parameters
        self.event = None
        self.event_parser: Callable[[EventData], T] | None = None
        self.result: T | None = None
        self.receipt: dict[str, Any] | None = None
        self.tx_hash: HexBytes | Awaitable[HexBytes] | None = None
        self.tx_id = next_tx_id()

    def with_event(
            self, event, parser: Callable[[EventData], T] | None = None
    ) -> "TypedContractFunction[T]":
        """Set the event to listen for"""
        self.event = event
        self.event_parser = parser
        return self

    async def call(self) -> T:
        """Synchronous read operation"""
        self.result = await self.func_call.call(self.params)
        return self.result

    def send_nowait(self, _show_pending: bool = True) -> Awaitable[HexBytes]:
        """Asynchronous write operation"""
        try:
            tx = self.params
            logger.info(
                "Sending tx#%d %s with %s", self.tx_id, format_contract_function(self.func_call), tx
            )
            tx = self.func_call.build_transaction(tx)
            # tx is auto signed
            instance = Web3RequestManager.instances[
                self.web3.eth.default_account
            ]
            self.tx_hash = instance.send_request(tx)
            if _show_pending:
                logger.info("tx#%d sent: %s", self.tx_id, 'pending')

            return self.tx_hash
        except ContractCustomError as e:
            raise convert_web3_error(e, format_contract_function(self.func_call)) from e

    async def send(self) -> HexBytes:
        """Synchronous write operation"""
        self.tx_hash = await self.send_nowait(_show_pending=False)
        logger.info("tx#%d sent: %s", self.tx_id, self.tx_hash.hex())
        return self.tx_hash

    async def build_transaction(self) -> TxParams:
        return await self.func_call.build_transaction(self.params)

    async def retrieve(self) -> T:
        """
        Retrieves the result of a transaction.

        For read operations (call), returns the cached result.
        For write operations (send), waits for the transaction to be mined
        and returns the transaction receipt.

        Returns:
            The result of the operation

        Raises:
            ValueError: If the transaction failed or no transaction has been sent
            GTEError: If a GTE-specific error occurred
        """
        if self.result is not None:
            return self.result

        if self.tx_hash is None:
            raise ValueError("Transaction hash is None. Call send() first.")
        try:
            if isinstance(self.tx_hash, Awaitable):
                self.tx_hash = await self.tx_hash
                logger.info(f'tx_hash for tx#{self.tx_id}: {self.tx_hash.hex()}')
            if self.event is None:
                return None
            # Wait for the transaction to be mined
            self.receipt = await self.web3.eth.wait_for_transaction_receipt(self.tx_hash)
            logs = self.event.process_receipt(self.receipt)

            if len(logs) == 0:
                return None
            if len(logs) > 1:
                logger.warning("Multiple logs found, expected one: %s", logs)

            if self.event_parser:
                return self.event_parser(logs[0])
            return logs[0]["args"]
        except ContractCustomError as e:
            raise convert_web3_error(e, format_contract_function(self.func_call)) from e

    async def send_wait(self) -> T:
        await self.send()
        return await self.retrieve()


def format_contract_function(func: AsyncContractFunction) -> str:
    """
    Format a ContractFunction into a more readable string with parameter names and values.

    Example output:
    0x1234 postLimitOrder(address: '0x1234...', order: {'amountInBase': 1.0, 'price': 1.0, 'cancelTimestamp': 0,
                                                'side': <Side.SELL: 1>, 'clientOrderId': 0,
                                                'limitOrderType': <LimitOrderType.GOOD_TILL_CANCELLED: 0>,
                                                'settlement': <Settlement.INSTANT: 1>})

    Args:
        func: The ContractFunction to format

    Returns:
        A formatted string representation of the function
    """
    function_name = func.fn_name
    args_values = func.args

    # Try to get parameter names from the ABI
    param_names = []
    try:
        contract = func.contract_abi
        for item in contract:
            if item.get("name") == function_name and item.get("type") == "function":
                param_names = [
                    input_param.get("name", f"param{i}")
                    for i, input_param in enumerate(item.get("inputs", []))
                ]
                break
    except (AttributeError, KeyError):
        # If we can't get parameter names from ABI, use generic param names
        param_names = [f"param{i}" for i in range(len(args_values))]

    # Format each argument with its name
    formatted_args = []
    for i, (name, value) in enumerate(zip(param_names, args_values)):
        if name:
            formatted_args.append(f"{name}: {repr(value)}")
        else:
            formatted_args.append(repr(value))

    return f"{func.address} {function_name}({', '.join(formatted_args)})"


async def make_web3(
        network: NetworkConfig,
        wallet_address: ChecksumAddress | None = None,
        wallet_private_key: PrivateKeyType | None = None,
) -> AsyncWeb3:
    """
    Create an AsyncWeb3 instance with the specified network configuration.

    Args:
        network: Network configuration object
        wallet_address: Optional wallet address to set as default account
        wallet_private_key: Optional wallet private key

    Returns:
        An instance of AsyncWeb3 configured for the specified network
    """
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(network.rpc_http))
    if wallet_address:
        w3.eth.default_account = wallet_address
    if wallet_private_key:
        account = Account.from_key(wallet_private_key)
        w3.eth.default_account = account.address
        w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(account), layer=0)
        await Web3RequestManager.ensure_instance(w3, account.address)
    return w3


class Web3RequestManager:
    instances: Dict[ChecksumAddress, "Web3RequestManager"] = {}

    @classmethod
    async def ensure_instance(
            cls, web3: AsyncWeb3, account_address: ChecksumAddress
    ) -> "Web3RequestManager":
        """Ensure a singleton instance of Web3RequestManager for the given account address"""
        if account_address not in cls.instances:
            cls.instances[account_address] = Web3RequestManager(web3, account_address)
            await cls.instances[account_address].start()
        return cls.instances[account_address]

    def __init__(self, web3: AsyncWeb3, account_address: ChecksumAddress):
        self.web3 = web3
        self.account_address = account_address
        self.request_queue: asyncio.Queue[Tuple[TxParams | Awaitable[TxParams], asyncio.Future[HexBytes]]] = (
            asyncio.Queue()
        )
        self.pending_transactions: Dict[int, HexBytes] = {}  # {nonce: tx_hash}
        self.current_nonce: int = 0
        self.lock = asyncio.Lock()
        self.is_running = False
        self.confirmation_task = None

    async def start(self):
        """Initialize and start processing"""
        await self.sync_nonce()
        self.is_running = True
        self.confirmation_task = asyncio.create_task(self._monitor_confirmations())
        asyncio.create_task(self._process_transactions())

    async def stop(self):
        """Graceful shutdown"""
        self.is_running = False
        if self.confirmation_task:
            await self.confirmation_task

    async def sync_nonce(self):
        """Update nonce from blockchain state"""
        async with self.lock:
            latest = await self.web3.eth.get_transaction_count(
                self.account_address, block_identifier="latest"
            )
            pending = await self.web3.eth.get_transaction_count(
                self.account_address, block_identifier="pending"
            )
            self.current_nonce = max(latest, pending)
            self._cleanup_confirmed_nonces(latest)

    async def bump_nonce(self):
        """Increment nonce for the next transaction"""
        async with self.lock:
            self.current_nonce += 1
            return self.current_nonce

    def _cleanup_confirmed_nonces(self, latest_nonce):
        """Remove confirmed transactions from pending set"""
        for nonce in list(self.pending_transactions.keys()):
            if nonce < latest_nonce:
                del self.pending_transactions[nonce]

    async def _process_transactions(self):
        """Main transaction processing loop"""
        while self.is_running:
            tx, future = await self.request_queue.get()

            async with self.lock:
                nonce = self.current_nonce
                self.current_nonce += 1
            try:
                if isinstance(tx, Awaitable):
                    tx = await tx
                tx_hash = await self._send_transaction(tx, Nonce(nonce))
                future.set_result(tx_hash)
                self.pending_transactions[nonce] = tx_hash

            except Exception as e:
                future.set_exception(e)
                await self._handle_processing_error(e)

    async def _monitor_confirmations(self):
        """Dedicated confirmation monitoring task"""
        while self.is_running:
            await asyncio.sleep(5)  # Check every 5 seconds

            async with self.lock:
                pending_nonces = list(self.pending_transactions.keys())

            for nonce in pending_nonces:
                tx_hash = self.pending_transactions.get(nonce, None)
                if not tx_hash:
                    continue

                try:
                    receipt = await self.web3.eth.get_transaction_receipt(tx_hash)
                    if receipt and receipt["blockNumber"]:
                        # finished
                        async with self.lock:
                            del self.pending_transactions[nonce]
                except TransactionNotFound:
                    # Transaction not found, it might be pending
                    continue
                except Exception as e:
                    logger.error("Error while checking transaction %s: %s", tx_hash.hex(), e)
                    async with self.lock:
                        del self.pending_transactions[nonce]

    async def _handle_processing_error(self, error):
        """Handle transaction sending errors"""
        if isinstance(error, (ValueError, TransactionNotFound)):
            async with self.lock:
                await self.sync_nonce()

    async def _send_transaction(self, tx: TxParams, nonce: Nonce):
        """Transaction sending implementation"""
        if "from" not in tx:
            tx["from"] = self.account_address
        if "nonce" not in tx:
            tx["nonce"] = nonce
        return await self.web3.eth.send_transaction(tx)

    def send_request(self, data: TxParams | Awaitable[TxParams]) -> Awaitable[HexBytes]:
        """Public API to submit transactions"""
        future = asyncio.Future()
        self.request_queue.put_nowait((data, future))
        return future
