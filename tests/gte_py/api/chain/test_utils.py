import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from hexbytes import HexBytes
from eth_account import Account
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction, AsyncContractEvent
from web3.types import EventData, TxReceipt
from web3.exceptions import ContractCustomError
from typing import cast

from gte_py.api.chain.utils import (
    TypedContractFunction, 
    BoundedNonceTxScheduler,
    parse_event_from_receipt,
    normalize_receipt
)

class AsyncPropertyMock:
    def __init__(self, value):
        self._value = value
        self._mock = AsyncMock(return_value=value)

    def __get__(self, obj, objtype=None):
        return self._mock()


@pytest.fixture
def mock_web3():
    """Create a mock AsyncWeb3 instance."""
    web3 = AsyncMock(spec=AsyncWeb3)
    
    # Create eth mock with all required methods
    eth_mock = AsyncMock()
    eth_mock.get_transaction_count = AsyncMock(return_value=5)
    type(eth_mock).chain_id = AsyncPropertyMock(1)
    eth_mock.send_raw_transaction = AsyncMock(return_value=HexBytes("0x123"))
    eth_mock.wait_for_transaction_receipt = AsyncMock(return_value={"status": 1})
    eth_mock.get_block = AsyncMock(return_value={"baseFeePerGas": 1000000000})

    # Attach eth mock to web3
    web3.eth = eth_mock
    
    # Create manager mock for realtime requests
    manager_mock = AsyncMock()
    manager_mock.coro_request = AsyncMock(return_value={"status": 1, "transactionHash": "0x123"})
    web3.manager = manager_mock
    
    return web3


@pytest.fixture
def mock_account():
    """Create a mock LocalAccount instance."""
    account = MagicMock()
    account.address = "0x1234567890123456789012345678901234567890"
    account.sign_transaction = MagicMock(return_value=MagicMock(
        hash=HexBytes("0x123"),
        raw_transaction=HexBytes("0x456")
    ))
    return account


@pytest.fixture
def mock_contract_function():
    """Create a mock AsyncContractFunction instance."""
    func = AsyncMock(spec=AsyncContractFunction)
    func.address = "0xabcdef1234567890abcdef1234567890abcdef12"
    func.fn_name = "transfer"
    func.args = ["0x123", 1000]
    func._encode_transaction_data = MagicMock(return_value=b"encoded_data")
    func.call = AsyncMock(return_value=True)
    return func


@pytest.fixture
def mock_contract_event():
    """Create a mock AsyncContractEvent instance."""
    event = AsyncMock(spec=AsyncContractEvent)
    event.address = "0xabcdef1234567890abcdef1234567890abcdef12"
    event.process_receipt = MagicMock(return_value=[
        {"args": {"from": "0x123", "to": "0x456", "value": 1000}}
    ])
    return event


class TestTypedContractFunction:
    """Test TypedContractFunction class."""

    def test_initialization(self, mock_contract_function):
        """Test TypedContractFunction initialization."""
        tx = TypedContractFunction(mock_contract_function)
        
        assert tx.func_call is mock_contract_function
        assert tx.params == {}
        assert tx.event is None
        assert tx.event_parser is None

    def test_initialization_with_params(self, mock_contract_function):
        """Test TypedContractFunction initialization with params."""
        params = {"gas": 100000, "maxFeePerGas": 2000000000}
        tx = TypedContractFunction(mock_contract_function, params)
        
        assert tx.params == params

    def test_with_event(self, mock_contract_function, mock_contract_event):
        """Test with_event method."""
        def parser(event_data):
            return {"parsed": event_data}
        
        tx = TypedContractFunction(mock_contract_function)
        result = tx.with_event(mock_contract_event, parser)
        
        assert result is tx
        assert tx.event is mock_contract_event
        assert tx.event_parser is parser

    def test_with_event_no_parser(self, mock_contract_function, mock_contract_event):
        """Test with_event method without parser."""
        tx = TypedContractFunction(mock_contract_function)
        result = tx.with_event(mock_contract_event)
        
        assert result is tx
        assert tx.event is mock_contract_event
        assert tx.event_parser is None

    @pytest.mark.asyncio
    async def test_call_success(self, mock_contract_function):
        """Test successful call method."""
        tx = TypedContractFunction(mock_contract_function)
        result = await tx.call()
        
        assert result is True
        mock_contract_function.call.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_contract_error(self, mock_contract_function):
        """Test call method with contract error."""
        mock_contract_function.call.side_effect = ContractCustomError("CustomError")
        tx = TypedContractFunction(mock_contract_function)
        
        with pytest.raises(Exception):
            await tx.call()


class TestParseEventFromReceipt:
    """Test parse_event_from_receipt function."""

    def test_no_event_returns_receipt(self, mock_contract_function):
        """Test when no event is set, returns receipt."""
        tx = TypedContractFunction(mock_contract_function)
        receipt = {"transactionHash": "0x123", "status": 1}  # type: ignore
        
        result = parse_event_from_receipt(receipt, tx)
        
        assert result == receipt

    def test_with_event_no_parser(self, mock_contract_function, mock_contract_event):
        """Test with event but no parser returns raw event."""
        tx = TypedContractFunction(mock_contract_function)
        tx.with_event(mock_contract_event)
        receipt = {"transactionHash": "0x123", "status": 1}  # type: ignore
        
        result = parse_event_from_receipt(receipt, tx)
        
        assert result == {"args": {"from": "0x123", "to": "0x456", "value": 1000}}
        mock_contract_event.process_receipt.assert_called_once()

    def test_with_event_and_parser(self, mock_contract_function, mock_contract_event):
        """Test with event and parser returns parsed result."""
        def parser(event_data):
            return {"parsed": event_data["args"]}
        
        tx = TypedContractFunction(mock_contract_function)
        tx.with_event(mock_contract_event, parser)
        receipt = {"transactionHash": "0x123", "status": 1}  # type: ignore
        
        result = parse_event_from_receipt(receipt, tx)
        
        assert result == {"parsed": {"from": "0x123", "to": "0x456", "value": 1000}}

    def test_no_events_found(self, mock_contract_function, mock_contract_event):
        """Test when no events are found in receipt."""
        mock_contract_event.process_receipt.return_value = []
        tx = TypedContractFunction(mock_contract_function)
        tx.with_event(mock_contract_event)
        receipt = {"transactionHash": "0x123", "status": 1}  # type: ignore
        
        result = parse_event_from_receipt(receipt, tx)
        
        assert result == receipt


class TestBoundedNonceTxScheduler:
    """Test BoundedNonceTxScheduler class."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_web3, mock_account):
        """Test BoundedNonceTxScheduler initialization."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        
        assert scheduler.web3 is mock_web3
        assert scheduler.account is mock_account
        assert scheduler.from_address == mock_account.address
        assert scheduler.max_pending_window == 499
        assert scheduler.last_confirmed == 0
        assert scheduler.last_sent == 0
        assert scheduler.chain_id is None

    @pytest.mark.asyncio
    async def test_initialization_custom_window(self, mock_web3, mock_account):
        """Test BoundedNonceTxScheduler initialization with custom window."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account, max_pending_window=100)
        
        assert scheduler.max_pending_window == 100

    @pytest.mark.asyncio
    async def test_start(self, mock_web3, mock_account):
        """Test scheduler start method."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        
        await scheduler.start()
        
        assert scheduler.last_confirmed == 5
        assert scheduler.last_sent == 5
        assert scheduler.chain_id == 1
        mock_web3.eth.get_transaction_count.assert_awaited_once_with(
            mock_account.address, "latest"
        )
        # Access the underlying mock for assertion
        chain_id_descriptor = type(mock_web3.eth).__dict__['chain_id']
        chain_id_descriptor._mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop(self, mock_web3, mock_account):
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)

        # Create a real awaitable coroutine to mock the task
        async def dummy_coroutine():
            await asyncio.sleep(0)

        task = asyncio.create_task(dummy_coroutine())
        task.cancel = MagicMock()

        scheduler._monitoring_task = task

        await scheduler.stop()

        task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pending_count(self, mock_web3, mock_account):
        """Test get_pending_count method."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        scheduler.last_confirmed = 5
        scheduler.last_sent = 8
        
        count = await scheduler.get_pending_count()
        
        assert count == 3

    @pytest.mark.asyncio
    async def test_send_success(self, mock_web3, mock_account, mock_contract_function):
        """Test successful send method."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        await scheduler.start()
        
        tx = TypedContractFunction(mock_contract_function)
        result = await scheduler.send(tx)
        
        assert result == HexBytes("0x123")
        mock_web3.eth.send_raw_transaction.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_wait_success(self, mock_web3, mock_account, mock_contract_function):
        """Test successful send_wait method."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        await scheduler.start()
        
        mock_web3.manager.coro_request.return_value = {"status": 1, "transactionHash": "0x123"}
        
        tx = TypedContractFunction(mock_contract_function)
        result = await scheduler.send_wait(tx)
        
        # The normalize_receipt function converts transactionHash to HexBytes
        assert result["status"] == 1
        assert result["transactionHash"] == HexBytes("0x123")
        mock_web3.manager.coro_request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_wait_with_event(self, mock_web3, mock_account, mock_contract_function, mock_contract_event):
        """Test send_wait method with event parsing."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        await scheduler.start()
        
        def parser(event_data):
            return {"parsed": event_data["args"]}
        
        mock_web3.manager.coro_request.return_value = {"status": 1, "transactionHash": "0x123"}
        
        tx = TypedContractFunction(mock_contract_function)
        tx.with_event(mock_contract_event, parser)
        result = await scheduler.send_wait(tx)
        
        assert result == {"parsed": {"from": "0x123", "to": "0x456", "value": 1000}}

    @pytest.mark.asyncio
    async def test_wait_for_receipt(self, mock_web3, mock_account):
        """Test wait_for_receipt method."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        mock_web3.eth.wait_for_transaction_receipt.return_value = {"status": 1}
        
        tx_hash = HexBytes("0x123")
        result = await scheduler.wait_for_receipt(tx_hash)
        
        assert result == {"status": 1}
        mock_web3.eth.wait_for_transaction_receipt.assert_awaited_once_with(tx_hash, timeout=10)

    @pytest.mark.asyncio
    async def test_pending_window_full(self, mock_web3, mock_account, mock_contract_function):
        """Test behavior when pending window is full."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account, max_pending_window=2)
        await scheduler.start()
        
        # Fill the window
        scheduler.last_sent = 7  # 2 pending (5-7)
        
        tx = TypedContractFunction(mock_contract_function)
        
        with pytest.raises(RuntimeError, match="Pending transaction window still full"):
            await scheduler.send(tx)

    @pytest.mark.asyncio
    async def test_stuck_nonce_monitoring(self, mock_web3, mock_account):
        """Test stuck nonce monitoring."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        # Use integer values for testing
        scheduler._monitor_interval = 1  # Fast for testing
        scheduler._stuck_nonce_threshold = 1
        await scheduler.start()
        
        # Simulate stuck nonce
        mock_web3.eth.get_transaction_count.side_effect = [
            AsyncMock(return_value=5),  # latest
            AsyncMock(return_value=5),  # pending (same as latest = stuck)
        ]
        
        # Start monitoring
        task = asyncio.create_task(scheduler._monitor_stuck_nonces())
        await asyncio.sleep(0.15)  # Let it run a bit
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_cancel_stuck_nonce(self, mock_web3, mock_account):
        """Test cancel stuck nonce method."""
        scheduler = BoundedNonceTxScheduler(mock_web3, mock_account)
        await scheduler.start()
        
        mock_web3.eth.get_block.return_value = {"baseFeePerGas": 1000000000}
        
        await scheduler._cancel_stuck_nonce(5)
        
        mock_web3.eth.send_raw_transaction.assert_awaited_once()


class TestNormalizeReceipt:
    """Test normalize_receipt function."""

    def test_normalize_receipt_numeric_fields(self):
        """Test normalization of numeric fields."""
        receipt = {
            "blockNumber": "0x123",
            "gasUsed": "0x456",
            "status": "0x1"
        }
        
        result = normalize_receipt(receipt)
        
        assert result["blockNumber"] == 291
        assert result["gasUsed"] == 1110
        assert result["status"] == 1

    def test_normalize_receipt_bytes_fields(self):
        """Test normalization of bytes fields."""
        receipt = {
            "blockHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "transactionHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "to": "0x1234567890123456789012345678901234567890"
        }
        
        result = normalize_receipt(receipt)
        
        assert isinstance(result["blockHash"], HexBytes)
        assert isinstance(result["transactionHash"], HexBytes)
        assert isinstance(result["to"], HexBytes)

    def test_normalize_receipt_topics(self):
        """Test normalization of topics field."""
        receipt = {
            "logs": [{
                "topics": [
                    "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                    "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                ]
            }]
        }
        
        result = normalize_receipt(receipt)
        
        assert isinstance(result["logs"][0]["topics"][0], HexBytes)
        assert isinstance(result["logs"][0]["topics"][1], HexBytes)

    def test_normalize_receipt_preserves_other_fields(self):
        """Test that other fields are preserved unchanged."""
        receipt = {
            "blockNumber": "0x123",
            "extraField": "should_be_preserved",
            "nested": {
                "innerField": "also_preserved"
            }
        }
        
        result = normalize_receipt(receipt)
        
        assert result["extraField"] == "should_be_preserved"
        assert result["nested"]["innerField"] == "also_preserved"
