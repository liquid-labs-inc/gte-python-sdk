import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from hexbytes import HexBytes
from eth_account import Account
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction, AsyncContractEvent
from web3.types import EventData, TxReceipt
from web3.exceptions import ContractCustomError
from typing import cast

from gte_py.api.chain.utils import (
    TypedContractFunction, 
    TxScheduler,
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


@pytest.fixture
def mock_websocket():
    """Create a mock websocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


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


class TestTxScheduler:
    """Test TxScheduler class."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_account):
        """Test TxScheduler initialization."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        
        assert scheduler._rpc_url == "wss://test-rpc.com"
        assert scheduler.account is mock_account
        assert scheduler.from_address == mock_account.address
        assert scheduler._chain_id is None
        assert scheduler._nonce is None

    @pytest.mark.asyncio
    async def test_start(self, mock_account, mock_websocket):
        """Test scheduler start method."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        
        # Mock websocket connection and RPC responses
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_websocket
            
            # Mock chain_id response
            chain_id_response = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": "0x1"
            })
            
            # Mock nonce response
            nonce_response = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "result": "0x5"
            })
            
            # Set up recv to return chain_id then nonce
            mock_websocket.recv.side_effect = [chain_id_response, nonce_response]
            
            await scheduler.start()
            
            assert scheduler.chain_id == 1
            assert scheduler.nonce == 5
            assert scheduler._ws is mock_websocket
            mock_connect.assert_awaited_once_with("wss://test-rpc.com")

    @pytest.mark.asyncio
    async def test_stop(self, mock_account, mock_websocket):
        """Test scheduler stop method."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        
        await scheduler.stop()
        
        assert scheduler._ws is None
        mock_websocket.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_no_connection(self, mock_account):
        """Test scheduler stop when not connected."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        
        # Should not raise an error
        await scheduler.stop()
        assert scheduler._ws is None

    @pytest.mark.asyncio
    async def test_chain_id_property_not_initialized(self, mock_account):
        """Test chain_id property raises error when not initialized."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        
        with pytest.raises(ValueError, match="Chain ID not initialized"):
            _ = scheduler.chain_id

    @pytest.mark.asyncio
    async def test_nonce_property_not_initialized(self, mock_account):
        """Test nonce property raises error when not initialized."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        
        with pytest.raises(ValueError, match="Nonce not initialized"):
            _ = scheduler.nonce

    @pytest.mark.asyncio
    async def test_ws_property_not_connected(self, mock_account):
        """Test ws property raises error when not connected."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        
        with pytest.raises(ValueError, match="WebSocket not connected"):
            _ = scheduler.ws

    @pytest.mark.asyncio
    async def test_return_transaction_data(self, mock_account, mock_websocket, mock_contract_function):
        """Test return_transaction_data method."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        scheduler._chain_id = 1
        
        # Mock nonce response
        nonce_response = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x5"
        })
        mock_websocket.recv.return_value = nonce_response
        
        tx = TypedContractFunction(mock_contract_function)
        result = await scheduler.return_transaction_data(tx)
        
        assert result["chainId"] == 1
        assert result["from"] == mock_account.address
        assert result["nonce"] == 5
        assert result["to"] == mock_contract_function.address

    @pytest.mark.asyncio
    async def test_send(self, mock_account, mock_websocket, mock_contract_function):
        """Test send method."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        scheduler._chain_id = 1
        scheduler._nonce = 5
        
        # Mock signed transaction
        signed_tx = MagicMock()
        signed_tx.hash = HexBytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        signed_tx.raw_transaction = HexBytes("0xabcdef")
        mock_account.sign_transaction.return_value = signed_tx
        
        tx = TypedContractFunction(mock_contract_function)
        result = await scheduler.send(tx)
        
        assert result == signed_tx.hash.hex()
        assert scheduler.nonce == 6  # Nonce should be incremented
        mock_websocket.send.assert_awaited_once()
        # Verify the payload contains realtime_sendRawTransaction
        call_args = mock_websocket.send.call_args[0][0]
        payload = json.loads(call_args)
        assert payload["method"] == "realtime_sendRawTransaction"

    @pytest.mark.asyncio
    async def test_send_wait(self, mock_account, mock_websocket, mock_contract_function):
        """Test send_wait method."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        scheduler._chain_id = 1
        scheduler._nonce = 5
        
        # Mock signed transaction
        signed_tx = MagicMock()
        signed_tx.hash = HexBytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        signed_tx.raw_transaction = HexBytes("0xabcdef")
        mock_account.sign_transaction.return_value = signed_tx
        
        # Mock receipt response
        receipt_response = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "status": "0x1",
                "transactionHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "blockNumber": "0x100"
            }
        })
        mock_websocket.recv.return_value = receipt_response
        
        tx = TypedContractFunction(mock_contract_function)
        result = await scheduler.send_wait(tx)
        
        assert result["status"] == 1
        assert scheduler.nonce == 6  # Nonce should be incremented
        mock_websocket.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_wait_with_event(self, mock_account, mock_websocket, mock_contract_function, mock_contract_event):
        """Test send_wait method with event parsing."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        scheduler._chain_id = 1
        scheduler._nonce = 5
        
        # Mock signed transaction
        signed_tx = MagicMock()
        signed_tx.hash = HexBytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        signed_tx.raw_transaction = HexBytes("0xabcdef")
        mock_account.sign_transaction.return_value = signed_tx
        
        # Mock receipt response
        receipt_response = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "status": "0x1",
                "transactionHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "blockNumber": "0x100"
            }
        })
        mock_websocket.recv.return_value = receipt_response
        
        def parser(event_data):
            return {"parsed": event_data["args"]}
        
        tx = TypedContractFunction(mock_contract_function)
        tx.with_event(mock_contract_event, parser)
        result = await scheduler.send_wait(tx)
        
        # Should return parsed event data
        assert result == {"parsed": {"from": "0x123", "to": "0x456", "value": 1000}}

    @pytest.mark.asyncio
    async def test_send_wait_reverted(self, mock_account, mock_websocket, mock_contract_function):
        """Test send_wait method with reverted transaction."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        scheduler._chain_id = 1
        scheduler._nonce = 5
        
        # Mock signed transaction
        signed_tx = MagicMock()
        signed_tx.hash = HexBytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        signed_tx.raw_transaction = HexBytes("0xabcdef")
        mock_account.sign_transaction.return_value = signed_tx
        
        # Mock receipt response with status 0 (reverted)
        receipt_response = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "status": "0x0",
                "transactionHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                "blockNumber": "0x100"
            }
        })
        mock_websocket.recv.return_value = receipt_response
        
        tx = TypedContractFunction(mock_contract_function)
        
        with pytest.raises(Exception, match="Transaction reverted"):
            await scheduler.send_wait(tx)

    @pytest.mark.asyncio
    async def test_send_wait_rpc_error(self, mock_account, mock_websocket, mock_contract_function):
        """Test send_wait method with RPC error."""
        scheduler = TxScheduler("wss://test-rpc.com", mock_account)
        scheduler._ws = mock_websocket
        scheduler._chain_id = 1
        scheduler._nonce = 5
        
        # Mock signed transaction
        signed_tx = MagicMock()
        signed_tx.hash = HexBytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        signed_tx.raw_transaction = HexBytes("0xabcdef")
        mock_account.sign_transaction.return_value = signed_tx
        
        # Mock error response
        error_response = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32000,
                "message": "Transaction failed"
            }
        })
        mock_websocket.recv.return_value = error_response
        
        tx = TypedContractFunction(mock_contract_function)
        
        with pytest.raises(Exception, match="RPC Error"):
            await scheduler.send_wait(tx)
