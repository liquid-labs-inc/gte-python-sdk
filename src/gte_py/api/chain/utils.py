import asyncio
import importlib.resources as pkg_resources
import json
import logging
import time
import warnings
from typing import Any, Generic, TypeVar, Callable, Tuple, Dict, Awaitable, Optional, List
from typing import cast

from async_timeout import timeout
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_account.types import PrivateKeyType
from eth_typing import ChecksumAddress
from eth_utils.address import is_checksum_address
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction
from web3.exceptions import ContractCustomError, Web3Exception
from web3.middleware import SignAndSendRawMiddlewareBuilder, Middleware, validation
from web3.types import TxParams, EventData, Nonce, Wei, TxReceipt
from gte_py.api.chain.errors import ERROR_EXCEPTIONS

from gte_py.configs import NetworkConfig

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
    return Exception(f"Web3 error: {error_code} in {cause}. ")


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
        "tx_send",
        "tx_id",
    ]

    def __init__(self, func_call: AsyncContractFunction, params: TxParams | Any = None):
        self.web3: AsyncWeb3 = func_call.w3
        self.func_call = func_call  # Bound contract function (with arguments)
        self.params = params  # Transaction parameters
        self.event = None
        self.event_parser: Callable[[EventData], T] | None = None
        self.result: T | None = None
        self.receipt: TxReceipt | None = None
        self.tx_hash: HexBytes | Awaitable[HexBytes] | None = None
        self.tx_send: Awaitable[None] | None = None
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
        return cast(T, self.result)

    def send_nowait(self) -> Awaitable[HexBytes]:
        """Asynchronous write operation"""
        try:
            tx = self.params
            tx['nonce'] = cast(Nonce, 0) # to be updated later
            logger.info(
                "Sending tx#%d %s with %s", self.tx_id, format_contract_function(self.func_call), tx
            )
            tx = self.func_call.build_transaction(tx)
            # tx is auto signed

            account = self.web3.eth.default_account
            if not isinstance(account, str) or not is_checksum_address(account):
                raise ValueError("Default account must be a valid ChecksumAddress")

            instance = Web3RequestManager.instances[account]

            self.tx_hash, self.tx_send = instance.submit_tx(tx)

            return self.tx_hash
        except ContractCustomError as e:
            raise convert_web3_error(e, format_contract_function(self.func_call)) from e

    async def send(self) -> HexBytes:
        """Synchronous write operation"""
        try:
            self.tx_hash = await self.send_nowait()
            self.tx_send = cast(Awaitable[None], self.tx_send)
            await self.tx_send
            self.tx_send = None
            logger.info("tx#%d sent: %s", self.tx_id, self.tx_hash.to_0x_hex())
            return self.tx_hash
        except ContractCustomError as e:
            if isinstance(self.tx_hash, Awaitable):
                self.tx_hash = await self.tx_hash
            raise convert_web3_error(e, format_contract_function(self.func_call, self.tx_hash)) from e

    async def build_transaction(self) -> TxParams:
        return await self.func_call.build_transaction(self.params)

    async def retrieve(self) -> T | None:
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
                logger.info(f'tx_hash for tx#{self.tx_id}: {self.tx_hash.to_0x_hex()}')
            if self.tx_send is not None:
                await self.tx_send
                self.tx_send = None
            if self.event is None:
                return None
            # Wait for the transaction to be mined
            self.receipt = await self.web3.eth.wait_for_transaction_receipt(self.tx_hash)
            if self.receipt['status'] != 1:
                tx_params = await self.web3.eth.get_transaction(self.tx_hash)
                try:
                    tx_params = {
                        "from": tx_params.get("from"),
                        "to": tx_params.get("to"),
                        "value": tx_params.get("value"),
                        "gas": tx_params.get("gas"),
                        "maxFeePerGas": tx_params.get("maxFeePerGas"),
                        "maxPriorityFeePerGas": tx_params.get("maxPriorityFeePerGas"),
                        "nonce": tx_params.get("nonce"),
                        "chainId": tx_params.get("chainId"),
                        "type": tx_params.get("type"),
                        "accessList": tx_params.get("accessList"),
                    }
                    await self.func_call.call(cast(TxParams, tx_params), block_identifier=self.receipt['blockNumber'])
                except ContractCustomError:
                    raise
                except Exception as e:
                    logger.warning('Simulatrion failed: ' + format_contract_function(self.func_call, self.tx_hash) +
                                   " : " + str(self.receipt), exc_info=e)
                raise Web3Exception("transaction failed: " +
                                    format_contract_function(self.func_call, self.tx_hash) +
                                    " : " + str(self.receipt)
                                    )
            logs = self.event.process_receipt(self.receipt)

            if len(logs) == 0:
                return None
            if len(logs) > 1:
                logger.warning("Multiple logs found, expected one: %s", logs)

            if self.event_parser:
                return self.event_parser(logs[0])
            return logs[0]["args"]
        except ContractCustomError as e:
            if isinstance(self.tx_hash, Awaitable):
                self.tx_hash = None
            raise convert_web3_error(e, format_contract_function(self.func_call, self.tx_hash)) from e

    async def send_wait(self) -> T | None:
        await self.send()
        return await self.retrieve()


def format_contract_function(func: AsyncContractFunction, tx_hash: HexBytes | None = None) -> str:
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

    result = f"{func.address} {function_name}({', '.join(formatted_args)})"
    if tx_hash:
        result += f" tx_hash: {tx_hash.to_0x_hex()}"
    return result


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

    warnings.warn(
        "web3.middleware.validation.METHODS_TO_VALIDATE is set to [] to avoid repetitive get_chainId. This will affect all web3 instances.")
    validation.METHODS_TO_VALIDATE = []

    if wallet_address:
        w3.eth.default_account = wallet_address
    if wallet_private_key:
        account: LocalAccount = Account.from_key(wallet_private_key)
        w3.eth.default_account = account.address
        middleware = cast(Middleware, SignAndSendRawMiddlewareBuilder.build(account))
        w3.middleware_onion.inject(middleware, layer=0)
        await Web3RequestManager.ensure_instance(w3, account)
    return w3


class Web3RequestManager:
    instances: Dict[ChecksumAddress, "Web3RequestManager"] = {}

    @classmethod
    async def ensure_instance(
            cls, web3: AsyncWeb3,
            account: LocalAccount
    ) -> "Web3RequestManager":
        """Ensure a singleton instance of Web3RequestManager for the given account address"""
        if account.address not in cls.instances:
            cls.instances[account.address] = Web3RequestManager(web3, account)
            await cls.instances[account.address].start()
        return cls.instances[account.address]

    def __init__(self, web3: AsyncWeb3, account: LocalAccount):
        self.web3 = web3
        self.account = account
        self._tx_queue: asyncio.Queue[
            Tuple[TxParams | Awaitable[TxParams], asyncio.Future[HexBytes], asyncio.Future[None]]] = (
            asyncio.Queue()
        )
        self.free_nonces: List[Nonce] = []
        self._prev_latest_tx_cnt: int = 0
        self.next_nonce: Nonce = Nonce(0)
        self.lock = asyncio.Lock()
        self.is_running = False
        self.confirmation_task = None
        self.process_transactions_task = None
        self.logger = logging.getLogger(__name__)
        self.chain_id = None

    async def start(self):
        """Initialize and start processing"""
        self.chain_id = await self.web3.eth.chain_id
        await self.sync_nonce()
        self.is_running = True
        self.confirmation_task = asyncio.create_task(self._monitor_confirmations())
        self.process_transactions_task = asyncio.create_task(self._process_transactions())
        self.logger.info("Web3RequestManager started for account %s. next nonce %s", self.account.address,
                         self.next_nonce)

    async def stop(self):
        """Graceful shutdown"""
        self.is_running = False
        if self.confirmation_task:
            await self.confirmation_task
        if self.process_transactions_task:
            await self.process_transactions_task

    async def sync_nonce(self):
        """Update nonce from blockchain state"""
        async with self.lock:
            self.logger.info('Trying to sync nonce for %s', self.account.address)
            latest_tx_cnt = int(await self.web3.eth.get_transaction_count(
                self.account.address, block_identifier="latest"
            ))
            pending_tx_cnt = int(await self.web3.eth.get_transaction_count(
                self.account.address, block_identifier="pending"
            ))
            latest_nonce =  Nonce(latest_tx_cnt - 1)
            pending_nonce = Nonce(pending_tx_cnt - 1)
            self.logger.info(f"Latest nonce: {latest_nonce}, pending nonce: {pending_nonce}, next nonce: {self.next_nonce}")
            # do not update from latest, as there could be blocked transactions already
            self.next_nonce = Nonce(max(latest_tx_cnt, self.next_nonce))
            nonce = Nonce(latest_tx_cnt)
            to_cancel = None
            if latest_tx_cnt < pending_tx_cnt and (nonce in self.free_nonces or latest_tx_cnt == self._prev_latest_tx_cnt):
                # nonce to be recycled
                # or
                # transactions stuck for 5 seconds: nonce gap, too low fee price, chain stuck
                self.logger.warning(f"Nonce stuck at {nonce} for {self.account.address}, trying to cancel")
                try:
                    self.free_nonces.remove(nonce)
                except ValueError:
                    pass
                to_cancel = nonce

            self._prev_latest_tx_cnt = latest_tx_cnt

        # it has to be outside the lock to avoid deadlock
        if to_cancel is not None:
            await self.cancel_tx(nonce)

    async def get_nonce(self):
        async with self.lock:
            if len(self.free_nonces) == 0:
                nonce = self.next_nonce
                self.logger.debug(f"Get nonce {nonce}")
                self.next_nonce = cast(Nonce, self.next_nonce + 1)
            else:
                nonce = self.free_nonces.pop(0)
                self.logger.debug(f"Get nonce {nonce}")
            return nonce

    async def put_nonce(self, nonce):
        async with self.lock:
            self.logger.debug(f"Put nonce {nonce}")
            self.free_nonces.append(nonce)
            self.free_nonces.sort()

            while len(self.free_nonces) > 0:
                nonce = self.free_nonces[-1]
                if nonce + 1 == self.next_nonce:
                    self.logger.info(f"Recycling nonce {nonce}")
                    self.free_nonces.pop()
                    self.next_nonce = nonce
                else:
                    break

    async def cancel_tx(self, nonce: Nonce) -> Optional[HexBytes]:
        """
        Cancel a pending transaction by submitting a replacement with higher gas price.

        Args:
            nonce: The nonce of the transaction to cancel

        Returns:
            Transaction hash of the cancellation transaction if successful, None otherwise
        """
        max_priority_fee = await self.web3.eth.max_priority_fee
        block = await self.web3.eth.get_block(block_identifier="latest")
        gas_price_multiplier = 1.5

        base_fee = block.get("baseFeePerGas")
        if base_fee is None:
            # baseFeePerGas is optional in BlockData for typing,
            # but this should never occur on post–EIP-1559 networks.
            raise ValueError("Missing baseFeePerGas in block data.")

        # Create a transaction sending 0 ETH to ourselves (cancellation)
        cancel_tx: TxParams = {
            "from": self.account.address,
            "to": self.account.address,
            "value": Wei(0),
            "nonce": Nonce(nonce),
            "maxFeePerGas": Wei(int(base_fee * gas_price_multiplier)),
            # we sometimes receive max_priority_fee=0, which is not helpful
            "maxPriorityFeePerGas": Wei(max(1, int(max_priority_fee * gas_price_multiplier))),
            "gas": 21000  # Minimum gas limit
        }
        self.logger.info(
            f"Cancelling transaction nonce {nonce} with {cancel_tx}")
        await self._send_transaction(cancel_tx, nonce)

    async def _process_transactions(self):
        while self.is_running:
            tx, tx_future, tx_send = await self._tx_queue.get()

            try:
                async with timeout(15):
                    nonce = await self.get_nonce()
                    if isinstance(tx, Awaitable):
                        tx = await tx

                    tx_hash = await self._send_transaction(tx, nonce, tx_future)
                    logger.info(f"Transaction with nonce {nonce} sent: {tx_hash.to_0x_hex()}")
                    tx_future.set_result(tx_hash)
                    tx_send.set_result(None)
            except Exception as e:
                logger.error(f"Failed to send transaction: {e}")
                if not tx_future.done():
                    tx_future.set_exception(e)
                tx_send.set_exception(e)

    async def _monitor_confirmations(self):
        """Dedicated confirmation monitoring task"""
        while self.is_running:
            await asyncio.sleep(5)  # Check every 5 seconds
            try:
                await self.sync_nonce()
            except Exception as e:
                self.logger.error(f"Error during nonce synchronization", exc_info=e)
                continue

    async def _send_transaction(self, tx: TxParams, nonce: Nonce,
                                tx_hash_future: asyncio.Future[HexBytes] | None = None):
        """Transaction sending implementation"""
        try:
            tx["nonce"] = nonce
            if self.chain_id is None:
                raise ValueError("chain_id must be set before sending a transaction")
            tx['chainId'] = self.chain_id
            if "from" not in tx:
                tx["from"] = self.account.address

            if "maxPriorityFeePerGas" not in tx:
                priority_fee = await self.web3.eth.max_priority_fee
                tx["maxPriorityFeePerGas"] = priority_fee

            if "gas" not in tx:
                gas = await self.web3.eth.estimate_gas(tx)
                effective_gas = int(gas * 1.5)
                tx["gas"] = effective_gas
            signed_tx: SignedTransaction = self.web3.eth.account.sign_transaction(tx, self.account.key)
            if tx_hash_future:
                tx_hash_future.set_result(signed_tx.hash)
            await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return signed_tx.hash
        except Exception as e:
            self.logger.error(f"Error sending transaction: {e}")
            error = str(e)
            nonce_already_known = (
                    "replacement transaction underpriced" in error
                    or "nonce too low" in error
            )
            if not nonce_already_known:
                await self.put_nonce(nonce)
            raise e

    def submit_tx(self, tx: TxParams | Awaitable[TxParams]) -> Tuple[Awaitable[HexBytes], Awaitable[None]]:
        """Public API to submit transactions"""
        tx_hash = asyncio.Future()
        tx_send = asyncio.Future()
        self._tx_queue.put_nowait((tx, tx_hash, tx_send))
        return tx_hash, tx_send
