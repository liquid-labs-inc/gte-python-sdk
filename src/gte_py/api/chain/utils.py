"""
Core utilities for blockchain interactions in the GTE Python SDK.
"""

import asyncio
import importlib.resources as pkg_resources
import json
import logging
import time
import warnings
from typing import Any, Generic, TypeVar, Callable, Tuple, Dict, Awaitable, Optional, List
from typing import cast
from typing_extensions import Unpack

from async_timeout import timeout
from eth_account import Account
from web3._utils.events import EventLogErrorFlags
from web3.datastructures import AttributeDict
from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_account.types import PrivateKeyType, TransactionDictType
from eth_typing import ChecksumAddress
from eth_utils.address import is_checksum_address
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction, AsyncContractEvent
from web3.exceptions import ContractCustomError, Web3Exception
from web3.types import TxParams, EventData, Nonce, Wei, TxReceipt
from gte_py.api.chain.errors import ERROR_EXCEPTIONS

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
    """Lift a callable that may return None to one that always returns a value"""
    def wrapper(event: EventData) -> T:
        result = func(event)
        if result is None:
            raise ValueError("Event parser returned None")
        return result
    return wrapper


tx_id = 0


def next_tx_id() -> int:
    """Get the next transaction ID"""
    global tx_id
    tx_id += 1
    return tx_id


class TypedContractFunction(Generic[T]):
    """A typed wrapper for Web3 contract functions with event parsing capabilities."""

    __slots__ = [
        "func_call",
        "params",
        "event",
        "event_parser",
    ]

    def __init__(self, func_call: AsyncContractFunction, params: dict[str, Any] | None = None):
        """
        Initialize a typed contract function.
        
        Args:
            func_call: Web3 contract function with bound arguments
            params: Transaction parameters (gas, maxFeePerGas, value, etc.)
        """
        self.func_call: AsyncContractFunction = func_call
        self.params: dict[str, Any] = params or {}
        
        # Event handling
        self.event: AsyncContractEvent | None = None
        self.event_parser: Callable[[EventData], Any] | None = None
        
    def with_event(
        self, event: AsyncContractEvent, parser: Callable[[EventData], Any] | None = None
    ) -> "TypedContractFunction[T]":
        """
        Configure event monitoring for this contract function.
        
        Args:
            event: Contract event to monitor (e.g., contract.events.Transfer)
            parser: Function to parse event data into typed result
                   If None, raw event data will be returned
        
        Returns:
            Self for method chaining
        """
        self.event = event
        self.event_parser = parser
        return self

    async def call(self) -> T:
        """
        Execute a read-only contract function call.
        
        Returns:
            The result of the contract function call, cast to the expected type
            
        Raises:
            ContractCustomError: If the contract call reverts with a custom error
            Exception: If the call fails due to network or other issues
        """
        try:
            result = await self.func_call.call()
            return cast(T, result)
        except ContractCustomError as e:
            raise convert_web3_error(e, format_contract_function(self.func_call)) from e


def parse_event_from_receipt(receipt: TxReceipt, contract_func: "TypedContractFunction[Any]") -> Any:
    """
    Search through the logs in the receipt for one that matches the event signature and address.
    """
    if not contract_func.event:
        return receipt  # fallback: just return the receipt

    # get relevant logs
    events = contract_func.event.process_receipt(receipt, EventLogErrorFlags.Discard)
    if len(events) == 0:
        return receipt
    if contract_func.event_parser:
        return contract_func.event_parser(events[0])
    return events[0]

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


def make_web3(
    rpc_url: str,
    wallet_private_key: PrivateKeyType | None = None,
) -> tuple[AsyncWeb3, LocalAccount | None]:
    """
    Create a Web3 instance and set the default account.

    Args:
        rpc_url: The URL of the RPC endpoint
        wallet_private_key: The private key of the wallet

    Returns:
        A tuple containing the Web3 instance and the account
    """
    web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc_url))
    if wallet_private_key:
        account = Account.from_key(wallet_private_key)
        return web3, account
    return web3, None

NUMERIC_FIELDS = {
    "blockNumber", "transactionIndex", "logIndex", "cumulativeGasUsed",
    "gasUsed", "status", "type", "effectiveGasPrice", "l1FeeScalar",
    "l1GasUsed", "l1GasPrice", "l1Fee"
}

BYTES_FIELDS = {
    "blockHash", "transactionHash", "logsBloom", "data", "contractAddress", "to", "from"
}

DICT_FIELDS = {"logs"}

LIST_OF_BYTES_FIELDS = {"topics"}

def normalize_receipt(receipt: TxReceipt) -> TxReceipt:
    def parse_field(k: str, v: Any) -> Any:
        if isinstance(v, list):
            if k in LIST_OF_BYTES_FIELDS:
                return [HexBytes(i) for i in v]
            return [parse_field(k, i) for i in v]

        if isinstance(v, dict) or isinstance(v, AttributeDict):
            return {sub_k: parse_field(sub_k, sub_v) for sub_k, sub_v in v.items()}

        if isinstance(v, str) and v.startswith("0x"):
            if k in NUMERIC_FIELDS:
                return int(v, 16)
            if k in BYTES_FIELDS or len(v) >= 42:
                return HexBytes(v)
        return v

    return {k: parse_field(k, v) for k, v in receipt.items()}


class BoundedNonceTxScheduler:
    """A transaction scheduler that manages nonce allocation and prevents nonce gaps."""
    
    def __init__(self, web3: AsyncWeb3, account: LocalAccount, max_pending_window: int = 499):
        """
        Initialize the high-throughput transaction scheduler.
        
        Args:
            web3: AsyncWeb3 instance for blockchain interaction
            account: Account for signing transactions
            max_pending_window: Maximum pending transactions (default: 499)
        """
        self.web3 = web3
        self.account = account
        self.from_address = account.address
        self.max_pending_window = max_pending_window
        
        # Lock-based nonce management
        self.nonce_lock = asyncio.Lock()
        self.last_confirmed = 0
        self.last_sent = 0
        self.chain_id: int | None = None
        
        # Optional stuck nonce monitoring
        self._monitoring_task: asyncio.Task[None] | None = None
        self._stuck_nonce_threshold = 30  # seconds
        self._monitor_interval = 10  # seconds
        
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Initialize scheduler and optionally start background monitoring."""
        self.last_confirmed = await self.web3.eth.get_transaction_count(self.from_address, "latest")
        self.last_sent = self.last_confirmed
        self.chain_id = await self.web3.eth.chain_id
        
        self.logger.info(f"BoundedNonceTxScheduler started for {self.from_address}")
        self.logger.info(f"Initial nonce: {self.last_confirmed}, Chain ID: {self.chain_id}")
        
        # Start optional stuck nonce monitoring (only if needed)
        if self._monitor_interval > 0:
            self._monitoring_task = asyncio.create_task(self._monitor_stuck_nonces())
    
    async def stop(self):
        """Stop scheduler and cancel background monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Wait for pending transactions to confirm
        await self._sync_confirmed_nonce()
        pending_count = await self.get_pending_count()
        if pending_count > 0:
            self.logger.warning(f"Stopping with {pending_count} pending transactions")
        
        self.logger.info("BoundedNonceTxScheduler stopped")

    async def get_pending_count(self) -> int:
        """Get current number of pending transactions."""
        async with self.nonce_lock:
            return self.last_sent - self.last_confirmed

    async def _sync_confirmed_nonce(self):
        """Sync last_confirmed from chain (must be called under lock)."""
        network_confirmed = await self.web3.eth.get_transaction_count(self.from_address, "latest")
        self.last_confirmed = network_confirmed
        self.logger.debug(f"Synced confirmed nonce: {self.last_confirmed}")

    async def _check_pending_window(self):
        """
        Check pending window and sync if needed. Fast fail if still full.
        Must be called before transaction signing.
        """
        async with self.nonce_lock:
            pending_count = self.last_sent - self.last_confirmed
            
            # Fast path: if window is not full, no network calls needed
            if pending_count < self.max_pending_window:
                return
            
            self.logger.warning(f"Pending window full ({pending_count}/{self.max_pending_window}), syncing with network")
            
            # Retry with exponential backoff: 0s, 2s, 4s, 8s
            retry_delays = [0, 2, 4, 8]
            
            for delay in retry_delays:
                if delay > 0:
                    self.logger.info(f"Retrying window check in {delay}s")
                    await asyncio.sleep(delay)
                    
                    try:
                        # Sync with network to get latest confirmed nonce
                        network_confirmed = await self.web3.eth.get_transaction_count(self.from_address, "latest")
                        self.last_confirmed = network_confirmed
                        
                        # Check if we still have too many pending after sync
                        pending_after_sync = self.last_sent - self.last_confirmed
                        
                        if pending_after_sync < self.max_pending_window:
                            self.logger.info(f"Window cleared after retry: confirmed={self.last_confirmed}, pending={pending_after_sync}")
                            return
                        
                        self.logger.warning(f"Window still full after attempt: {pending_after_sync}/{self.max_pending_window} pending")
                        
                    except Exception as e:
                        self.logger.error(f"Network error during window check attempt: {e}")
                        continue
                
            # All retries exhausted and window still full
            final_pending = self.last_sent - self.last_confirmed
            raise RuntimeError(
                f"Pending transaction window still full after {len(retry_delays)} retries: "
                f"{final_pending}/{self.max_pending_window} transactions pending"
            )

    async def _sign_transaction(self, contract_func: "TypedContractFunction[Any]") -> SignedTransaction:
        """
        Sign a transaction with automatic nonce allocation.
        
        Args:
            contract_func: The contract function to execute
            
        Returns:
            Signed transaction ready for submission
        """
        await self._check_pending_window()
        
        # Atomic nonce increment
        async with self.nonce_lock:
            nonce = self.last_sent
            self.last_sent += 1
        
        try:
            # Build transaction with required parameters
            tx_params: TransactionDictType = {
                "chainId": self.chain_id or 6342,
                "from": self.from_address,
                "nonce": Nonce(nonce),
                "to": contract_func.func_call.address,
                "data": contract_func.func_call._encode_transaction_data(),
                "gas": contract_func.params.get("gas", 1_000_000_000),
                "maxFeePerGas": contract_func.params.get("maxFeePerGas", 5_000_000_000),
                "maxPriorityFeePerGas": contract_func.params.get("maxPriorityFeePerGas", 0),
                "value": contract_func.params.get("value", 0),
            }
            
            # Sign the transaction using the account's sign_transaction method
            signed = self.account.sign_transaction(tx_params)
            
            self.logger.debug(f"Signed transaction with nonce {nonce}: {signed.hash.hex()}")
            return signed
            
        except Exception as e:
            # If signing fails, return the nonce to the pool
            async with self.nonce_lock:
                self.last_sent -= 1
            self.logger.error(f"Failed to sign transaction with nonce {nonce}: {e}")
            raise

    async def send(self, contract_func: "TypedContractFunction[Any]") -> HexBytes:
        """
        Send transaction with optimistic acknowledgment.
        
        This method checks the pending window, signs the transaction, and submits it
        to the network. It returns immediately after submission without waiting for
        confirmation.
        
        Args:
            contract_func: The contract function to execute
            
        Returns:
            Transaction hash of the submitted transaction
            
        Raises:
            RuntimeError: If the pending transaction window is full
            Exception: If transaction signing or submission fails
        """
        # Sign transaction (includes nonce increment)
        signed = await self._sign_transaction(contract_func)
        
        try:
            # Optimistic send - treat success as nonce consumption
            tx_hash = await self.web3.eth.send_raw_transaction(signed.raw_transaction)
            self.logger.debug(f"Sent transaction: {tx_hash.hex()}")
            return tx_hash
            
        except Exception as e:
            # Failure rewind already handled in _sign_transaction
            self.logger.error(f"Failed to send transaction {signed.hash.hex()}: {e}")
            raise

    async def send_wait(self, contract_func: "TypedContractFunction[Any]") -> Any:
        """
        Send transaction and wait for receipt.
        Uses realtime endpoint if available, falls back to regular send + wait.
        """
        # Sign transaction (includes nonce increment)
        signed = await self._sign_transaction(contract_func)
        
        try:
            receipt = await self._send_realtime(signed.raw_transaction)
            self.logger.debug(f"Realtime transaction completed: {signed.hash.hex()}")
            receipt = normalize_receipt(receipt)
        except Exception as realtime_error:
            self.logger.debug(f"Realtime transaction failed: {realtime_error}")
            raise

        # Parse and return event if specified, else return receipt
        return parse_event_from_receipt(receipt, contract_func)

    async def wait_for_receipt(self, tx_hash: HexBytes, timeout: int = 10) -> TxReceipt:
        """Wait for transaction receipt by hash."""
        try:
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            self.logger.debug(f"Received receipt for transaction: {tx_hash.hex()}")
            receipt = normalize_receipt(receipt)
            return receipt
        except Exception as e:
            self.logger.error(f"Failed to get receipt for transaction {tx_hash.hex()}: {e}")
            raise

    async def _monitor_stuck_nonces(self):
        """
        Background task to monitor and cancel stuck nonces.
        Runs every _monitor_interval seconds.
        """
        stuck_nonce_timestamps: dict[int, float] = {}
        
        while True:
            try:
                await asyncio.sleep(self._monitor_interval)
                
                # Get current nonce states
                latest_nonce = await self.web3.eth.get_transaction_count(self.from_address, "latest")
                pending_nonce = await self.web3.eth.get_transaction_count(self.from_address, "pending")
                
                # If pending_nonce < last_sent, we have a gap
                # This means the network is waiting for a nonce we think we sent
                if pending_nonce < self.last_sent:
                    # The stuck nonce is the pending_nonce (the one the network is waiting for)
                    stuck_nonce = pending_nonce
                    current_time = time.time()
                    
                    if stuck_nonce not in stuck_nonce_timestamps:
                        stuck_nonce_timestamps[stuck_nonce] = current_time
                        self.logger.info(f"Possible stuck nonce {stuck_nonce} (latest: {latest_nonce}, last_sent: {self.last_sent})")
                    
                    elif current_time - stuck_nonce_timestamps[stuck_nonce] > self._stuck_nonce_threshold:
                        # Nonce stuck too long - submit cancel transaction
                        await self._cancel_stuck_nonce(stuck_nonce)
                        del stuck_nonce_timestamps[stuck_nonce]
                else:
                    # No gap - clear stuck nonce tracking
                    stuck_nonce_timestamps.clear()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in stuck nonce monitoring: {e}")

    async def _cancel_stuck_nonce(self, stuck_nonce: int):
        """
        Submit a cancel transaction for a stuck nonce.
        Sends 0 ETH to self with higher gas price.
        """
        try:
            # Get current gas price info
            block = await self.web3.eth.get_block("latest")
            base_fee = block.get("baseFeePerGas", 10_000_000_000)
            
            # Cancel transaction: send 0 ETH to self with higher fees
            cancel_tx: TransactionDictType = {
                "chainId": self.chain_id or 6342,
                "from": self.from_address,
                "to": self.from_address,
                "nonce": Nonce(stuck_nonce),
                "value": 0,
                "gas": 21000,
                "maxFeePerGas": int(base_fee * 2),
                "maxPriorityFeePerGas": 0,
                "data": b"",
            }
            
            # Sign and send cancel transaction
            signed_cancel = self.account.sign_transaction(cancel_tx)
            tx_hash = await self.web3.eth.send_raw_transaction(signed_cancel.raw_transaction)
            
            self.logger.info(f"Submitted cancel transaction for stuck nonce {stuck_nonce}: {tx_hash.hex()}")
            
        except Exception as e:
            self.logger.error(f"Failed to cancel stuck nonce {stuck_nonce}: {e}")

    async def _send_realtime(self, raw_tx: HexBytes) -> TxReceipt:
        """Send transaction using realtime endpoint."""
        return await self.web3.manager.coro_request(
            "realtime_sendRawTransaction",
            [raw_tx.hex()]
        )



# class Web3RequestManager:
#     instances: Dict[ChecksumAddress, "Web3RequestManager"] = {}

#     @classmethod
#     async def ensure_instance(
#             cls, web3: AsyncWeb3,
#             account: LocalAccount
#     ) -> "Web3RequestManager":
#         """Ensure a singleton instance of Web3RequestManager for the given account address"""
#         if account.address not in cls.instances:
#             cls.instances[account.address] = Web3RequestManager(web3, account)
#             await cls.instances[account.address].start()
#         return cls.instances[account.address]

#     def __init__(self, web3: AsyncWeb3, account: LocalAccount):
#         self.web3 = web3
#         self.account = account
#         self._tx_queue: asyncio.Queue[
#             Tuple[TxParams | Awaitable[TxParams], asyncio.Future[HexBytes], asyncio.Future[None]]] = (
#             asyncio.Queue()
#         )
#         self.free_nonces: List[Nonce] = []
#         self._prev_latest_tx_cnt: int = 0
#         self.next_nonce: Nonce = Nonce(0)
#         self.lock = asyncio.Lock()
#         self.is_running = False
#         self.confirmation_task = None
#         self.process_transactions_task = None
#         self.logger = logging.getLogger(__name__)
#         self.chain_id = None

#     async def start(self):
#         """Initialize and start processing"""
#         self.chain_id = await self.web3.eth.chain_id
#         await self.sync_nonce()
#         self.is_running = True
#         # self.confirmation_task = asyncio.create_task(self._monitor_confirmations())
#         self.process_transactions_task = asyncio.create_task(self._process_transactions())
#         self.logger.info("Web3RequestManager started for account %s. next nonce %s", self.account.address,
#                          self.next_nonce)

#     async def stop(self):
#         """Graceful shutdown"""
#         self.is_running = False
#         if self.confirmation_task:
#             await self.confirmation_task
#         if self.process_transactions_task:
#             await self.process_transactions_task

#     async def sync_nonce(self):
#         """Update nonce from blockchain state"""
#         async with self.lock:
#             self.logger.info('Trying to sync nonce for %s', self.account.address)
#             latest_tx_cnt = int(await self.web3.eth.get_transaction_count(
#                 self.account.address, block_identifier="latest"
#             ))
#             pending_tx_cnt = int(await self.web3.eth.get_transaction_count(
#                 self.account.address, block_identifier="pending"
#             ))
#             latest_nonce =  Nonce(latest_tx_cnt - 1)
#             pending_nonce = Nonce(pending_tx_cnt - 1)
#             self.logger.info(f"Latest nonce: {latest_nonce}, pending nonce: {pending_nonce}, next nonce: {self.next_nonce}")
#             # do not update from latest, as there could be blocked transactions already
#             self.next_nonce = Nonce(max(latest_tx_cnt, self.next_nonce))
#             nonce = Nonce(latest_tx_cnt)
#             to_cancel = None
#             if latest_tx_cnt < pending_tx_cnt and (nonce in self.free_nonces or latest_tx_cnt == self._prev_latest_tx_cnt):
#                 # nonce to be recycled
#                 # or
#                 # transactions stuck for 5 seconds: nonce gap, too low fee price, chain stuck
#                 self.logger.warning(f"Nonce stuck at {nonce} for {self.account.address}, trying to cancel")
#                 try:
#                     self.free_nonces.remove(nonce)
#                 except ValueError:
#                     pass
#                 to_cancel = nonce

#             self._prev_latest_tx_cnt = latest_tx_cnt

#         # it has to be outside the lock to avoid deadlock
#         if to_cancel is not None:
#             await self.cancel_tx(nonce)

#     async def get_nonce(self):
#         async with self.lock:
#             if len(self.free_nonces) == 0:
#                 nonce = self.next_nonce
#                 self.logger.debug(f"Get nonce {nonce}")
#                 self.next_nonce = cast(Nonce, self.next_nonce + 1)
#             else:
#                 nonce = self.free_nonces.pop(0)
#                 self.logger.debug(f"Get nonce {nonce}")
#             return nonce

#     async def put_nonce(self, nonce):
#         async with self.lock:
#             self.logger.debug(f"Put nonce {nonce}")
#             self.free_nonces.append(nonce)
#             self.free_nonces.sort()

#             while len(self.free_nonces) > 0:
#                 nonce = self.free_nonces[-1]
#                 if nonce + 1 == self.next_nonce:
#                     self.logger.info(f"Recycling nonce {nonce}")
#                     self.free_nonces.pop()
#                     self.next_nonce = nonce
#                 else:
#                     break

#     async def cancel_tx(self, nonce: Nonce) -> Optional[HexBytes]:
#         """
#         Cancel a pending transaction by submitting a replacement with higher gas price.

#         Args:
#             nonce: The nonce of the transaction to cancel

#         Returns:
#             Transaction hash of the cancellation transaction if successful, None otherwise
#         """
#         max_priority_fee = await self.web3.eth.max_priority_fee
#         block = await self.web3.eth.get_block(block_identifier="latest")
#         gas_price_multiplier = 1.5

#         base_fee = block.get("baseFeePerGas")
#         if base_fee is None:
#             # baseFeePerGas is optional in BlockData for typing,
#             # but this should never occur on post–EIP-1559 networks.
#             raise ValueError("Missing baseFeePerGas in block data.")

#         # Create a transaction sending 0 ETH to ourselves (cancellation)
#         cancel_tx: TxParams = {
#             "from": self.account.address,
#             "to": self.account.address,
#             "value": Wei(0),
#             "nonce": Nonce(nonce),
#             "maxFeePerGas": Wei(int(base_fee * gas_price_multiplier)),
#             # we sometimes receive max_priority_fee=0, which is not helpful
#             "maxPriorityFeePerGas": Wei(max(1, int(max_priority_fee * gas_price_multiplier))),
#             "gas": 21000  # Minimum gas limit
#         }
#         self.logger.info(
#             f"Cancelling transaction nonce {nonce} with {cancel_tx}")
#         await self._send_transaction(cancel_tx, nonce)

#     async def _process_transactions(self):
#         while self.is_running:
#             tx, tx_future, tx_send = await self._tx_queue.get()

#             try:
#                 async with timeout(15):
#                     nonce = await self.get_nonce()
#                     if isinstance(tx, Awaitable):
#                         tx = await tx

#                     tx_hash = await self._send_transaction(tx, nonce, tx_future)
#                     logger.info(f"Transaction with nonce {nonce} sent: {tx_hash.to_0x_hex()}")
#                     tx_send.set_result(None)
#             except Exception as e:
#                 logger.error(f"Failed to send transaction: {e}")
#                 if not tx_future.done():
#                     tx_future.set_exception(e)
#                 tx_send.set_exception(e)

#     async def _monitor_confirmations(self):
#         """Dedicated confirmation monitoring task"""
#         while self.is_running:
#             await asyncio.sleep(5)  # Check every 5 seconds
#             try:
#                 await self.sync_nonce()
#             except Exception as e:
#                 self.logger.error(f"Error during nonce synchronization", exc_info=e)
#                 continue

#     async def _send_transaction(self, tx: TxParams, nonce: Nonce,
#                                 tx_hash_future: asyncio.Future[HexBytes] | None = None):
#         """Transaction sending implementation"""
#         try:
#             tx["nonce"] = nonce
#             if self.chain_id is None:
#                 raise ValueError("chain_id must be set before sending a transaction")
#             tx['chainId'] = self.chain_id
#             if "from" not in tx:
#                 tx["from"] = self.account.address

#             if "maxPriorityFeePerGas" not in tx:
#                 priority_fee = await self.web3.eth.max_priority_fee
#                 tx["maxPriorityFeePerGas"] = priority_fee

#             if "gas" not in tx:
#                 gas = await self.web3.eth.estimate_gas(tx)
#                 effective_gas = int(gas * 1.5)
#                 tx["gas"] = effective_gas
#             signed_tx: SignedTransaction = self.web3.eth.account.sign_transaction(tx, self.account.key)
#             if tx_hash_future:
#                 tx_hash_future.set_result(signed_tx.hash)
#             await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
#             return signed_tx.hash
#         except Exception as e:
#             self.logger.error(f"Error sending transaction: {e}")
#             error = str(e)
#             nonce_already_known = (
#                     "replacement transaction underpriced" in error
#                     or "nonce too low" in error
#             )
#             if not nonce_already_known:
#                 await self.put_nonce(nonce)
#             raise e

#     def submit_tx(self, tx: TxParams | Awaitable[TxParams]) -> Tuple[Awaitable[HexBytes], Awaitable[None]]:
#         """Public API to submit transactions"""
#         tx_hash = asyncio.Future()
#         tx_send = asyncio.Future()
#         self._tx_queue.put_nowait((tx, tx_hash, tx_send))
#         return tx_hash, tx_send

