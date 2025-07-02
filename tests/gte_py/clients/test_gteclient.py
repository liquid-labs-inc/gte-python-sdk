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
def wallet_address():
    return to_checksum_address("0x1234567890abcdef1234567890abcdef12345678")


@pytest.fixture
def private_key():
    return b"\x01" * 32


@pytest.fixture
def patched_clients():
    def make_web3_side_effect(*args, **kwargs):
        if kwargs.get("wallet_address") or kwargs.get("wallet_private_key"):
            return MagicMock(), MagicMock()
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
            "execution": execution_instance,
            "ensure_instance": ensure_instance,
        }


def test_initialization_with_wallet(config, wallet_address, private_key, patched_clients):
    client = GTEClient(config=config, wallet_address=wallet_address, wallet_private_key=private_key)

    assert client.config == config
    assert client._wallet_address == wallet_address
    assert client._web3 is not None
    assert client._account is not None
    assert client.rest is patched_clients["rest"].return_value
    assert client.websocket is patched_clients["ws"].return_value
    assert client.info is patched_clients["info"].return_value
    assert client.execution is patched_clients["execution"]
    assert client.connected is False


def test_initialization_without_wallet(config, patched_clients):
    client = GTEClient(config=config)

    assert client._wallet_address is None
    assert client.execution is None
    assert client._web3 is not None
    assert client._account is None


@pytest.mark.asyncio
async def test_connect_and_disconnect(config, wallet_address, private_key, patched_clients):
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

    client = GTEClient(config=config, wallet_address=wallet_address, wallet_private_key=private_key)

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
    assert client.execution is None

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

    wallet_address = to_checksum_address("0x1234567890abcdef1234567890abcdef12345678")
    private_key = b"\x01" * 32
    client = GTEClient(config=config, wallet_address=wallet_address, wallet_private_key=private_key)
    async with client:
        assert client.connected is True
        assert client.execution is patched_clients["execution"]
    assert client.connected is False
    rest.connect.assert_awaited()
    ws.connect.assert_awaited()
    rest.disconnect.assert_awaited()
    ws.disconnect.assert_awaited()
    info.unsubscribe_all.assert_awaited()

    client2 = GTEClient(config=config)
    async with client2:
        assert client2.connected is True
        assert client2.execution is None
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

    wallet_address = to_checksum_address("0x1234567890abcdef1234567890abcdef12345678")
    private_key = b"\x01" * 32
    client = GTEClient(config=config, wallet_address=wallet_address, wallet_private_key=private_key)

    await client.connect()
    await client.connect()  # no-op
    rest.connect.assert_awaited_once()
    ws.connect.assert_awaited_once()
    assert client.execution is patched_clients["execution"]

    await client.disconnect()
    await client.disconnect()  # no-op
    rest.disconnect.assert_awaited_once()
    ws.disconnect.assert_awaited_once()
    info.unsubscribe_all.assert_awaited_once()

    client2 = GTEClient(config=config)
    await client2.connect()
    await client2.connect()  # no-op
    assert client2.execution is None
    await client2.disconnect()
    await client2.disconnect()  # no-op
    info.unsubscribe_all.assert_awaited()
