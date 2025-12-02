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
import websockets
from typing_extensions import Unpack

from async_timeout import timeout
from eth_account import Account
from web3._utils.events import EventLogErrorFlags
from web3.datastructures import AttributeDict
from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_account.types import PrivateKeyType, TransactionDictType
from eth_typing import ChecksumAddress
from eth_utils.address import is_checksum_address, to_checksum_address
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction, AsyncContractEvent
from web3.exceptions import ContractCustomError, Web3Exception, Web3RPCError
from web3.types import TxParams, EventData, Nonce, Wei, TxReceipt
from gte_py.api.chain.errors import ERROR_SELECTORS

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
    
    # Try to decode the error using our error selectors
    if error_code in ERROR_SELECTORS:
        error_description = ERROR_SELECTORS[error_code]
        return Exception(f"Contract error: {error_description}")
    
    # If not found, try to extract 4-byte selector from hex
    if isinstance(error_code, str) and error_code.startswith('0x') and len(error_code) >= 10:
        selector = error_code[:10]  # First 4 bytes (0x + 8 hex chars)
        if selector in ERROR_SELECTORS:
            error_description = ERROR_SELECTORS[selector]
            return Exception(f"Contract error: {error_description}")
    
    # Fallback: return raw error with context
    return Exception(f"Unknown contract error: {error_code} in {cause}. Check transaction details for more info.")


T = TypeVar("T")


def lift_callable(func: Callable[[EventData], T | None]) -> Callable[[EventData], T]:
    """Lift a callable that may return None to one that always returns a value"""
    def wrapper(event: EventData) -> T:
        result = func(event)
        if result is None:
            raise ValueError("Event parser returned None")
        return result
    return wrapper


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
    wallet_address: ChecksumAddress | None = None,
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
    web3.middleware_onion.clear()
    if wallet_address:
        web3.eth.default_account = wallet_address
    if wallet_private_key:
        account = Account.from_key(wallet_private_key)
        web3.eth.default_account = account.address
        return web3, account
    web3.provider.cache_allowed_requests = True
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

    return {k: parse_field(k, v) for k, v in receipt.items()} # type: ignore


class TxScheduler:
    """A transaction scheduler that manages nonce allocation and prevents nonce gaps."""
    
    def __init__(
        self, 
        rpc_url: str, 
        account: LocalAccount
    ):
        """
        Initialize the transaction scheduler.
        
        Args:
            rpc_url: WebSocket RPC URL (e.g., wss://your-rpc-node.com)
            account: Account for signing transactions
        """
        self._rpc_url = rpc_url
        self._ws: websockets.ClientConnection | None = None
        self._account = account
        self.from_address = account.address
        self._chain_id: int | None = None
        self._nonce: int | None = None
        self._request_id = 0
        self.logger = logging.getLogger(__name__)
    
    @property
    def ws(self) -> websockets.ClientConnection:
        """Get the websocket connection."""
        if self._ws is None:
            raise ValueError("WebSocket not connected. Call await start() first.")
        return self._ws
    
    @property
    def account(self) -> LocalAccount:
        """Get the account for signing transactions."""
        return self._account
    
    @property
    def chain_id(self) -> int:
        if self._chain_id is None:
            raise ValueError("Chain ID not initialized. Call await start() first.")
        return self._chain_id
    
    @property
    def nonce(self) -> int:
        if self._nonce is None:
            raise ValueError("Nonce not initialized. Call await start() first.")
        return self._nonce
    
    def _get_request_id(self) -> int:
        """Get next request ID for JSON-RPC calls."""
        self._request_id += 1
        return self._request_id
    
    async def _rpc_call(self, method: str, params: list[Any]) -> Any:
        """Make a JSON-RPC call over the websocket connection."""
        request_id = self._get_request_id()
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }
        
        await self.ws.send(json.dumps(payload))
        response_text = await self.ws.recv()
        response = json.loads(response_text)
        
        if "error" in response:
            error = response["error"]
            raise Exception(f"RPC Error: {error.get('message', error)}")
        
        return response.get("result")
    
    async def _fetch_nonce(self) -> int:
        """Fetch the current nonce for the address."""
        result = await self._rpc_call("eth_getTransactionCount", [self.from_address, "pending"])
        return int(result, 16)

    async def _fetch_chain_id(self) -> int:
        """Fetch the chain ID from the RPC node."""
        result = await self._rpc_call("eth_chainId", [])
        return int(result, 16)

    async def start(self):
        """Connect to RPC node and initialize scheduler by fetching chain ID and nonce."""
        self.logger.info(f"Connecting to RPC node: {self._rpc_url}")
        self._ws = await websockets.connect(self._rpc_url)
        self._chain_id = await self._fetch_chain_id()
        self._nonce = await self._fetch_nonce()
        self.logger.info(f"TxScheduler started: chain_id={self._chain_id}, nonce={self._nonce}")
    
    async def stop(self):
        """Disconnect from RPC node and stop scheduler."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
        self.logger.info("TxScheduler stopped")
    
    def _build_tx_params(self, contract_func: "TypedContractFunction[Any]", nonce: int) -> TransactionDictType:
        """Build transaction parameters with given nonce."""        
        return {
            "chainId": self.chain_id,
            "from": self.from_address,
            "nonce": Nonce(nonce),
            "to": contract_func.func_call.address,
            "data": contract_func.func_call._encode_transaction_data(),
            "gas": contract_func.params.get("gas", 1_000_000_000),
            "maxFeePerGas": contract_func.params.get("maxFeePerGas", 2_500_000),
            "maxPriorityFeePerGas": contract_func.params.get("maxPriorityFeePerGas", 0),
            "value": contract_func.params.get("value", 0),
        }

    async def return_transaction_data(self, contract_func: "TypedContractFunction[Any]") -> TransactionDictType:
        """
        Return the transaction data for a contract function.

        Args:
            contract_func: The contract function to execute

        Returns:
            TransactionDictType: transaction data
        """
        current_nonce = await self._fetch_nonce()
        return self._build_tx_params(contract_func, current_nonce)

    async def _sign_transaction(self, contract_func: "TypedContractFunction[Any]") -> SignedTransaction:
        """
        Sign a transaction with automatic nonce allocation.
        
        Args:
            contract_func: The contract function to execute
            
        Returns:
            Signed transaction ready for submission
        """
        try:
            # Build transaction with required parameters
            tx_params = self._build_tx_params(contract_func, self.nonce)
            
            # Sign the transaction using the account's sign_transaction method
            signed = self.account.sign_transaction(tx_params)
            
            self.logger.debug(f"Signed transaction: {signed.hash.hex()}")
            return signed
            
        except Exception as e:
            self.logger.error(f"Failed to sign transaction: {e}")
            raise
    
    async def send(
        self, 
        contract_func: "TypedContractFunction[Any]",
        callback: Callable[[TxReceipt], Awaitable[None]] | None = None
    ) -> str:
        """
        Send transaction without waiting for receipt. Optionally call a callback when receipt is received.
        
        Args:
            contract_func: The contract function to execute
            callback: Optional async callback function to call with the receipt
        
        Returns:
            Transaction hash of the submitted transaction
        """
        try:
            # Sign transaction
            signed = await self._sign_transaction(contract_func)
            
            # Send via realtime_sendRawTransaction
            request_id = self._get_request_id()
            payload = {
                "jsonrpc": "2.0",
                "method": "realtime_sendRawTransaction",
                "params": [signed.raw_transaction.hex()],
                "id": request_id,
            }
            
            await self.ws.send(json.dumps(payload))
            tx_hash = signed.hash.hex()
            
            # Increment nonce after successful send
            self._nonce = self.nonce + 1
            
            self.logger.debug(f"Transaction sent: {tx_hash}")
            
            # If callback is provided, spawn a task to wait for receipt and call callback
            if callback:
                asyncio.create_task(self._wait_and_callback(request_id, callback))
            
            return tx_hash
            
        except Exception as e:
            self.logger.error(f"Failed to send transaction: {e}")
            raise Exception(f"Transaction failed: {str(e)}")
    
    async def _wait_and_callback(self, request_id: int, callback: Callable[[TxReceipt], Awaitable[None]]):
        """Wait for transaction receipt and call the callback."""
        try:
            # Wait for response from realtime_sendRawTransaction
            response_text = await self.ws.recv()
            response = json.loads(response_text)
            
            # Check if this is our response
            if response.get("id") != request_id:
                self.logger.warning(f"Received response for different request ID: {response.get('id')} vs {request_id}")
                return
            
            if "error" in response:
                error = response["error"]
                self.logger.error(f"Transaction failed: {error}")
                return
            
            # Parse receipt
            receipt = response.get("result", {})
            receipt = normalize_receipt(receipt)
            
            # Check status
            if receipt.get("status") == 0:
                self.logger.error(f"Transaction reverted: {receipt}")
            
            # Call callback
            await callback(receipt)
            
        except Exception as e:
            self.logger.error(f"Error in callback handler: {e}")

    async def send_wait(self, contract_func: "TypedContractFunction[Any]", _retry_count: int = 0) -> Any:
        """
        Send transaction and wait for receipt using realtime_sendRawTransaction.
        
        Args:
            contract_func: The contract function to execute
            _retry_count: Internal parameter to track retry attempts
            
        Returns:
            Parsed event data if event parser is configured, otherwise the receipt
        """
        # Sign transaction
        signed = await self._sign_transaction(contract_func)
        
        try:
            # Send via realtime_sendRawTransaction and wait for receipt
            async with timeout(60):  # 60 second timeout
                request_id = self._get_request_id()
                payload = {
                    "jsonrpc": "2.0",
                    "method": "realtime_sendRawTransaction",
                    "params": [signed.raw_transaction.hex()],
                    "id": request_id,
                }
                
                await self.ws.send(json.dumps(payload))
                
                # Increment nonce after successful send
                self._nonce = self.nonce + 1
                
                self.logger.debug(f"Transaction sent via realtime: {signed.hash.hex()}")
                
                # Wait for response
                response_text = await self.ws.recv()
                response = json.loads(response_text)
                
                if "error" in response:
                    error = response["error"]
                    error_message = error.get('message', str(error))
                    
                    # Check for nonce errors
                    nonce_error_keywords = ['nonce', 'already known', 'replacement transaction']
                    is_nonce_error = any(keyword in error_message.lower() for keyword in nonce_error_keywords)
                    
                    if is_nonce_error and _retry_count == 0:
                        self.logger.warning(f"Nonce error detected: {error_message}. Fetching current nonce and retrying...")
                        # Fetch current nonce from network
                        self._nonce = await self._fetch_nonce()
                        self.logger.info(f"Updated nonce to {self._nonce}, retrying transaction...")
                        # Retry once
                        return await self.send_wait(contract_func, _retry_count=1)
                    
                    raise Exception(f"RPC Error: {error_message}")
                
                # Parse receipt
                receipt = response.get("result", {})
                receipt = normalize_receipt(receipt)
                self.logger.debug(f"Transaction completed: {signed.hash.hex()}")
                
        except asyncio.TimeoutError:
            self.logger.error("Transaction timed out after 60 seconds")
            raise Exception("Transaction timed out - RPC endpoint may be slow")
        except Exception as e:
            # Check if this is a nonce error in exception message
            error_message = str(e).lower()
            nonce_error_keywords = ['nonce', 'already known', 'replacement transaction']
            is_nonce_error = any(keyword in error_message for keyword in nonce_error_keywords)
            
            if is_nonce_error and _retry_count == 0:
                self.logger.warning(f"Nonce error detected: {e}. Fetching current nonce and retrying...")
                # Fetch current nonce from network
                self._nonce = await self._fetch_nonce()
                self.logger.info(f"Updated nonce to {self._nonce}, retrying transaction...")
                # Retry once
                return await self.send_wait(contract_func, _retry_count=1)
            
            self.logger.error(f"Transaction failed: {e}")
            raise
        
        # Check if transaction reverted (status == 0)
        if receipt.get("status") == 0:
            self.logger.error(f"Transaction reverted: {signed.hash.hex()}")
            # Try to extract error information from receipt logs if available
            tx_hash = receipt.get("transactionHash", signed.hash.hex())
            raise Exception(f"Transaction reverted: {tx_hash}")
        
        # Parse and return event if specified, else return receipt
        return parse_event_from_receipt(receipt, contract_func)