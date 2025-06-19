import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from eth_utils.address import to_checksum_address

from gte_py.configs import NetworkConfig
from gte_py.clients import Client


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
def account():
    return to_checksum_address("0x1234567890abcdef1234567890abcdef12345678")


@pytest.fixture
def private_key():
    return b"\x01" * 32


@pytest.fixture
def patched_clients():
    with patch("gte_py.clients.make_web3", new=AsyncMock(return_value=MagicMock())) as make_web3, \
         patch("gte_py.clients.CLOBClient", return_value=MagicMock(init=AsyncMock())) as clob, \
         patch("gte_py.clients.TokenClient", return_value=MagicMock()) as token, \
         patch("gte_py.clients.InfoClient", return_value=MagicMock()) as info, \
         patch("gte_py.clients.MarketClient", return_value=MagicMock()) as market, \
         patch("gte_py.clients.UserClient", return_value=MagicMock()) as user, \
         patch("gte_py.clients.ExecutionClient", return_value=MagicMock()) as exec, \
         patch("gte_py.api.rest.RestApi") as rest:
        yield {
            "make_web3": make_web3,
            "clob": clob,
            "token": token,
            "info": info,
            "market": market,
            "user": user,
            "exec": exec,
            "rest": rest
        }


@pytest.mark.asyncio
async def test_connect_initializes_client(config, account, private_key, patched_clients):
    client = await Client.connect(config=config, account=account, wallet_private_key=private_key)

    assert client._web3 == patched_clients["make_web3"].return_value
    assert client._account == account
    assert client.clob is not None
    assert client.token is not None
    assert client.info is not None
    assert client.market is not None
    assert client.user is not None
    assert client.execution is not None


@pytest.mark.asyncio
async def test_context_manager_calls_init_and_rest(config, account, patched_clients):
    mock_web3 = MagicMock()
    mock_rest = MagicMock()
    mock_rest.__aenter__ = AsyncMock()
    mock_rest.__aexit__ = AsyncMock()
    patched_clients["rest"].return_value = mock_rest

    client = Client(config=config, web3=mock_web3, account=account)
    client.rest = mock_rest
    async with client:
        pass

    mock_rest.__aenter__.assert_awaited_once()
    patched_clients["clob"].return_value.init.assert_awaited_once()
    mock_rest.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_calls_aexit(config, account, patched_clients):
    mock_web3 = MagicMock()
    mock_rest = MagicMock()
    mock_rest.__aenter__ = AsyncMock()
    mock_rest.__aexit__ = AsyncMock()
    patched_clients["rest"].return_value = mock_rest

    client = Client(config=config, web3=mock_web3, account=account)
    client.rest = mock_rest
    await client.__aenter__()
    await client.close()

    mock_rest.__aexit__.assert_awaited_once()
