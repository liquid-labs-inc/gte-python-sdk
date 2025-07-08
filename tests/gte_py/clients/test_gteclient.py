import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from eth_utils.address import to_checksum_address

from gte_py.configs import NetworkConfig
from gte_py.clients import GTEClient


@pytest.fixture
def config():
    return NetworkConfig(
        name="testnet",
        api_url="https://api.test",
        ws_url="wss://ws.test",
        chain_id=999,
        native_token="TETH",
        rpc_http="https://rpc.test",
        rpc_ws="wss://rpc.test",
        block_explorer="https://explorer.test",
        performance_dashboard="https://perf.test",
        experimental_eips=[],
        eip_1559_base_fee_price=1.0,
        eip_1559_max_block_size=1000000,
        eip_1559_target_block_size=500000,
        block_time="12s",
        router_address=to_checksum_address("0x000000000000000000000000000000000000b00c"),
        launchpad_address=to_checksum_address("0x000000000000000000000000000000000000cafe"),
        clob_manager_address=to_checksum_address("0x000000000000000000000000000000000000beef"),
        weth_address=to_checksum_address("0x000000000000000000000000000000000000feed"),
    )


@pytest.fixture
def private_key():
    return b"\x01" * 32


@pytest.fixture
def patched_clients():
    def make_web3_side_effect(*args, **kwargs):
        if kwargs.get("wallet_private_key"):
            mock_account = MagicMock()
            mock_account.address = to_checksum_address("0x1234567890abcdef1234567890abcdef12345678")
            return MagicMock(), mock_account
        return MagicMock(), None

    with patch("gte_py.clients.make_web3", side_effect=make_web3_side_effect) as make_web3, \
         patch("gte_py.clients.RestApi") as rest, \
         patch("gte_py.clients.WebSocketApi") as ws, \
         patch("gte_py.clients.InfoClient") as info, \
         patch("gte_py.clients.ExecutionClient") as execution_class, \
         patch("gte_py.clients.Web3RequestManager.ensure_instance", new_callable=AsyncMock) as ensure_instance:
        
        execution_instance = MagicMock()
        execution_instance.init = AsyncMock()
        execution_class.return_value = execution_instance
        
        yield {
            "make_web3": make_web3,
            "rest": rest,
            "ws": ws,
            "info": info,
            "execution_class": execution_class,
            "execution": execution_instance,
            "ensure_instance": ensure_instance,
        }


def test_initialization_with_wallet(config, private_key, patched_clients):
    client = GTEClient(config=config, wallet_private_key=private_key)

    assert client.config == config
    assert client._account is not None
    assert client._web3 is not None
    assert client.rest is patched_clients["rest"].return_value
    assert client.websocket is patched_clients["ws"].return_value
    assert client.info is patched_clients["info"].return_value
    assert client.execution is patched_clients["execution"]
    assert client.connected is False
    assert client._account.address == to_checksum_address("0x1234567890abcdef1234567890abcdef12345678")


def test_initialization_without_wallet(config, patched_clients):
    client = GTEClient(config=config)

    assert client._account is None
    assert client._execution is None
    assert client._web3 is not None


def test_execution_client_initialization_parameters(config, private_key, patched_clients):
    """Test that ExecutionClient is initialized with correct parameters."""
    client = GTEClient(config=config, wallet_private_key=private_key)
    
    # Verify ExecutionClient was called with correct parameters
    patched_clients["execution_class"].assert_called_once_with(
        web3=client._web3,
        main_account=client._account.address,
        gte_router_address=config.router_address,
        weth_address=config.weth_address,
    )


def test_execution_property_with_wallet(config, private_key, patched_clients):
    """Test that execution property returns the execution client when wallet is provided."""
    client = GTEClient(config=config, wallet_private_key=private_key)
    
    assert client.execution is patched_clients["execution"]
    assert client._execution is patched_clients["execution"]


def test_execution_property_without_wallet(config, patched_clients):
    """Test that execution property raises assertion error when no wallet address was provided during initialization."""
    client = GTEClient(config=config)
    
    assert client._execution is None
    
    with pytest.raises(AssertionError, match="Execution client not initialized"):
        _ = client.execution


def test_execution_property_after_wallet_removal(config, private_key, patched_clients):
    """Test that execution property works correctly when wallet is provided."""
    client = GTEClient(config=config, wallet_private_key=private_key)
    
    # Should work when execution client is initialized
    assert client.execution is patched_clients["execution"]
    assert client._execution is patched_clients["execution"]


def test_execution_property_edge_cases(config, private_key, patched_clients):
    """Test edge cases for the execution property."""
    client = GTEClient(config=config, wallet_private_key=private_key)
    
    # Normal case - should work when wallet is provided
    assert client.execution is patched_clients["execution"]
    
    # Test that the property returns the same instance consistently
    execution1 = client.execution
    execution2 = client.execution
    assert execution1 is execution2
    assert execution1 is patched_clients["execution"]


@pytest.mark.asyncio
async def test_connect_and_disconnect(config, private_key, patched_clients):
    rest = MagicMock()
    rest.connect = AsyncMock()
    rest.disconnect = AsyncMock()

    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()

    info = MagicMock()
    info.unsubscribe_all = AsyncMock()

    patched_clients["rest"].return_value = rest
    patched_clients["ws"].return_value = ws
    patched_clients["info"].return_value = info

    client = GTEClient(config=config, wallet_private_key=private_key)

    await client.connect()
    assert client.connected is True
    rest.connect.assert_awaited_once()
    ws.connect.assert_awaited_once()
    patched_clients["ensure_instance"].assert_awaited_once()
    patched_clients["execution"].init.assert_awaited_once()

    await client.disconnect()
    assert client.connected is False
    info.unsubscribe_all.assert_awaited_once()
    rest.disconnect.assert_awaited_once()
    ws.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_and_disconnect_without_wallet(config, patched_clients):
    rest = MagicMock()
    rest.connect = AsyncMock()
    rest.disconnect = AsyncMock()

    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()

    info = MagicMock()
    info.unsubscribe_all = AsyncMock()

    patched_clients["rest"].return_value = rest
    patched_clients["ws"].return_value = ws
    patched_clients["info"].return_value = info

    client = GTEClient(config=config)

    await client.connect()
    assert client.connected is True
    rest.connect.assert_awaited_once()
    ws.connect.assert_awaited_once()
    assert client._execution is None  # Use private attribute, not property

    await client.disconnect()
    assert client.connected is False
    info.unsubscribe_all.assert_awaited_once()
    rest.disconnect.assert_awaited_once()
    ws.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_context_manager(config, patched_clients):
    rest = MagicMock()
    rest.connect = AsyncMock()
    rest.disconnect = AsyncMock()

    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()

    info = MagicMock()
    info.unsubscribe_all = AsyncMock()

    patched_clients["rest"].return_value = rest
    patched_clients["ws"].return_value = ws
    patched_clients["info"].return_value = info

    private_key = b"\x01" * 32
    client = GTEClient(config=config, wallet_private_key=private_key)
    async with client:
        assert client.connected is True
        assert client.execution is patched_clients["execution"]  # This should work with wallet
    assert client.connected is False
    rest.connect.assert_awaited()
    ws.connect.assert_awaited()
    rest.disconnect.assert_awaited()
    ws.disconnect.assert_awaited()
    info.unsubscribe_all.assert_awaited()

    client2 = GTEClient(config=config)
    async with client2:
        assert client2.connected is True
        assert client2._execution is None  # Use private attribute, not property
    assert client2.connected is False


@pytest.mark.asyncio
async def test_double_connect_disconnect_noop(config, patched_clients):
    rest = MagicMock()
    rest.connect = AsyncMock()
    rest.disconnect = AsyncMock()

    ws = MagicMock()
    ws.connect = AsyncMock()
    ws.disconnect = AsyncMock()

    info = MagicMock()
    info.unsubscribe_all = AsyncMock()
    patched_clients["rest"].return_value = rest
    patched_clients["ws"].return_value = ws
    patched_clients["info"].return_value = info

    private_key = b"\x01" * 32
    client = GTEClient(config=config, wallet_private_key=private_key)

    await client.connect()
    await client.connect()  # no-op
    rest.connect.assert_awaited_once()
    ws.connect.assert_awaited_once()
    assert client.execution is patched_clients["execution"]  # This should work with wallet

    await client.disconnect()
    await client.disconnect()  # no-op
    rest.disconnect.assert_awaited_once()
    ws.disconnect.assert_awaited_once()
    info.unsubscribe_all.assert_awaited_once()

    client2 = GTEClient(config=config)
    await client2.connect()
    await client2.connect()  # no-op
    assert client2._execution is None  # Use private attribute, not property
    await client2.disconnect()
    await client2.disconnect()  # no-op
    info.unsubscribe_all.assert_awaited()
