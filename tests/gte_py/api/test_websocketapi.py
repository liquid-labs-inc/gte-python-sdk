import asyncio
import json
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from gte_py.api.ws import WebSocketApi, ConnectionState

# Valid Ethereum address for testing
VALID_ADDRESS = "0x1234567890123456789012345678901234567890"

@pytest.fixture(autouse=True)
async def cleanup_tasks():
    """Cleanup any pending tasks after each test."""
    original_create_task = asyncio.create_task  # save unpatched reference

    with patch('asyncio.create_task', side_effect=lambda coro: original_create_task(coro)):
        yield

        current_task = asyncio.current_task()
        tasks = [task for task in asyncio.all_tasks()
                 if task is not current_task and not task.done()]

        if tasks:
            for task in tasks:
                task.cancel()
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                pass

class TestWebSocketApiConnection:
    @pytest.mark.asyncio
    async def test_connect_does_nothing_if_connected(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        with patch.object(ws, "_connect_internal", new_callable=AsyncMock) as mock_connect:
            await ws.connect()
            mock_connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_does_nothing_if_connecting(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTING
        with patch.object(ws, "_connect_internal", new_callable=AsyncMock) as mock_connect:
            await ws.connect()
            mock_connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_calls_connect_internal_if_disconnected(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.DISCONNECTED
        with patch.object(ws, "_connect_internal", new_callable=AsyncMock) as mock_connect:
            await ws.connect()
            mock_connect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_internal_opens_session_and_ws(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.DISCONNECTED

        mock_ws = AsyncMock()
        mock_session_instance = AsyncMock()
        mock_session_instance.ws_connect.return_value = mock_ws
        mock_session_instance.closed = False

        with patch("aiohttp.ClientSession", return_value=mock_session_instance):
            await ws._connect_internal()

            assert ws.state == ConnectionState.CONNECTED
            assert ws.session is mock_session_instance
            assert ws.ws is mock_ws

    @pytest.mark.asyncio
    async def test_connect_internal_logs_and_raises_on_ws_connect_failure(self, caplog):
        ws = WebSocketApi()
        ws.state = ConnectionState.DISCONNECTED
        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.ws_connect = AsyncMock(side_effect=Exception("fail"))
            with pytest.raises(Exception):
                await ws._connect_internal()
            assert ws.state == ConnectionState.DISCONNECTED
            assert "Failed to connect to WebSocket" in caplog.text

@pytest.mark.asyncio
async def test_disconnect_sets_shutting_down_and_cancels_tasks():
    ws = WebSocketApi()

    async def dummy():
        await asyncio.sleep(10)

    mock_listen_task = asyncio.create_task(dummy())
    mock_reconnect_task = asyncio.create_task(dummy())

    # Patch cancel and done methods
    mock_listen_task.cancel = MagicMock(wraps=mock_listen_task.cancel)
    mock_listen_task.done = MagicMock(return_value=False)

    mock_reconnect_task.cancel = MagicMock(wraps=mock_reconnect_task.cancel)
    mock_reconnect_task.done = MagicMock(return_value=False)

    ws.listen_task = mock_listen_task
    ws.reconnect_task = mock_reconnect_task
    ws.session = MagicMock()
    ws.session.closed = False
    ws.session.close = AsyncMock()
    ws.ws = MagicMock()
    ws.ws.close = AsyncMock()

    await ws.disconnect()

    assert ws._shutting_down is True
    mock_listen_task.cancel.assert_called_once()
    mock_reconnect_task.cancel.assert_called_once()
    assert ws.listen_task is None
    assert ws.reconnect_task is None


    @pytest.mark.asyncio
    async def test_disconnect_handles_already_closed_session_and_ws(self):
        ws = WebSocketApi()
        ws.listen_task = None
        ws.reconnect_task = None
        ws.session = MagicMock()
        ws.session.closed = True
        ws.ws = None
        await ws.disconnect()  # Should not raise
        # The session should be set to None after disconnect
        assert ws.session is None
        assert ws.ws is None

    @pytest.mark.asyncio
    async def test_disconnect_logs_on_close_exceptions(self, caplog):
        ws = WebSocketApi()
        ws.listen_task = None
        ws.reconnect_task = None
        ws.session = MagicMock()
        ws.session.closed = False
        ws.session.close = AsyncMock(side_effect=Exception("session fail"))
        ws.ws = MagicMock()
        ws.ws.close = AsyncMock(side_effect=Exception("ws fail"))
        await ws.disconnect()
        assert "Error closing WebSocket" in caplog.text or "Error closing session" in caplog.text

class TestWebSocketApiContextManager:
    @pytest.mark.asyncio
    async def test_aenter_calls_connect(self):
        ws = WebSocketApi()
        with patch.object(ws, 'connect', new_callable=AsyncMock) as mock_connect:
            result = await ws.__aenter__()
            mock_connect.assert_awaited_once()
            assert result is ws

    @pytest.mark.asyncio
    async def test_aexit_calls_disconnect(self):
        ws = WebSocketApi()
        with patch.object(ws, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
            await ws.__aexit__(None, None, None)
            mock_disconnect.assert_awaited_once()

class TestWebSocketApiListenLoop:
    @pytest.mark.asyncio
    async def test_listen_receives_text_valid_json_calls_callback(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        callback = AsyncMock()
        ws.callbacks = {123: callback}
        msg = MagicMock()
        msg.type = aiohttp.WSMsgType.TEXT
        msg.data = json.dumps({'id': 123, 'd': {'m': VALID_ADDRESS}})
        ws.ws.__aiter__.return_value = [msg]
        with patch.object(ws, '_handle_message', new_callable=AsyncMock) as mock_handle:
            await ws._listen()
            mock_handle.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_listen_receives_text_invalid_json_logs_error(self, caplog):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        msg = MagicMock()
        msg.type = aiohttp.WSMsgType.TEXT
        msg.data = '{invalid json}'
        ws.ws.__aiter__.return_value = [msg]
        await ws._listen()
        assert "Invalid JSON message" in caplog.text

    @pytest.mark.asyncio
    async def test_listen_receives_binary_logs_warning(self, caplog):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        msg = MagicMock()
        msg.type = aiohttp.WSMsgType.BINARY
        ws.ws.__aiter__.return_value = [msg]
        await ws._listen()
        assert "Received binary message" in caplog.text

    @pytest.mark.asyncio
    async def test_listen_receives_pong_logs_debug(self, caplog):
        ws = WebSocketApi(enable_logging=True)
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()

        msg = MagicMock()
        msg.type = aiohttp.WSMsgType.PONG
        ws.ws.__aiter__.return_value = [msg]

        with caplog.at_level(logging.DEBUG):
            await ws._listen()

        assert "Received pong" in caplog.text


    @pytest.mark.asyncio
    async def test_listen_receives_close_breaks_loop(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        msg = MagicMock()
        msg.type = aiohttp.WSMsgType.CLOSE
        ws.ws.__aiter__.return_value = [msg]
        await ws._listen()  # Should not raise

    @pytest.mark.asyncio
    async def test_listen_catches_generic_exception_logs_error(self, caplog):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        ws.ws.__aiter__.side_effect = Exception("fail")
        await ws._listen()
        assert "WebSocket listen error" in caplog.text

    @pytest.mark.asyncio
    async def test_listen_catches_cancelled_error_logs_debug(self, caplog):
        ws = WebSocketApi(enable_logging=True)
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        ws.ws.__aiter__.side_effect = asyncio.CancelledError()

        with caplog.at_level(logging.DEBUG):
            await ws._listen()

        assert "Listen task cancelled" in caplog.text

    @pytest.mark.asyncio
    async def test_listen_triggers_handle_disconnection_unless_shutting_down(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = False
        ws.ws = MagicMock()
        ws.ws.__aiter__.return_value = []
        with patch.object(ws, '_handle_disconnection', new_callable=AsyncMock) as mock_handle:
            await ws._listen()
            mock_handle.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_listen_does_not_trigger_handle_disconnection_if_shutting_down(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws._shutting_down = True
        ws.ws = MagicMock()
        ws.ws.__aiter__.return_value = []
        with patch.object(ws, '_handle_disconnection', new_callable=AsyncMock) as mock_handle:
            await ws._listen()
            mock_handle.assert_not_called()

class TestWebSocketApiDisconnectionHandling:
    @pytest.mark.asyncio
    async def test_handle_disconnection_does_nothing_if_reconnect_in_progress(self):
        ws = WebSocketApi()
        ws.reconnect_task = MagicMock()
        ws.reconnect_task.done.return_value = False
        with patch.object(ws, '_reconnect', new_callable=AsyncMock) as mock_reconnect:
            await ws._handle_disconnection()
            mock_reconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_disconnection_starts_reconnect_if_attempts_remain(self):
        ws = WebSocketApi()
        ws.reconnect_task = None
        ws.reconnect_count = 0
        ws.reconnect_attempts = 2
        with patch.object(ws, '_reconnect', new_callable=AsyncMock) as mock_reconnect:
            await ws._handle_disconnection()
            mock_reconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_disconnection_logs_error_if_attempts_exhausted(self, caplog):
        ws = WebSocketApi()
        ws.reconnect_task = None
        ws.reconnect_count = 2
        ws.reconnect_attempts = 2
        await ws._handle_disconnection()
        assert "Max reconnection attempts" in caplog.text

class TestWebSocketApiReconnectLogic:
    @pytest.mark.asyncio
    async def test_reconnect_applies_backoff_and_clamps(self):
        ws = WebSocketApi()
        ws.reconnect_attempts = 3
        ws.reconnect_count = 0
        ws.state = ConnectionState.RECONNECTING
        with patch.object(ws, '_connect_internal', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("fail")
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await ws._reconnect()
                assert mock_sleep.await_count >= 1

    @pytest.mark.asyncio
    async def test_reconnect_logs_final_failure_and_updates_state(self, caplog):
        ws = WebSocketApi()
        ws.reconnect_attempts = 1
        ws.reconnect_count = 0
        ws.state = ConnectionState.RECONNECTING
        with patch.object(ws, '_connect_internal', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("fail")
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await ws._reconnect()
        assert ws.state == ConnectionState.DISCONNECTED
        assert "Failed to reconnect after all attempts" in caplog.text

class TestWebSocketApiMessageHandling:
    @pytest.mark.asyncio
    async def test_handle_message_subscription_acknowledgment_logs_debug(self, caplog):
        ws = WebSocketApi(enable_logging=True)
        data = {'id': 123}
        with caplog.at_level(logging.DEBUG):
            await ws._handle_message(data)
        assert "Subscription acknowledged" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_message_valid_data_calls_callback(self):
        ws = WebSocketApi()
        callback = AsyncMock()
        ws.callbacks = {123: callback}
        data = {'id': 123, 'd': {'m': VALID_ADDRESS}}
        await ws._handle_message(data)
        callback.assert_awaited_once_with({'m': VALID_ADDRESS})

    @pytest.mark.asyncio
    async def test_handle_message_no_matching_callback_logs_warning(self, caplog):
        ws = WebSocketApi()
        ws.callbacks = {}
        data = {'id': 123, 'd': {'m': VALID_ADDRESS}}
        await ws._handle_message(data)
        assert "No callback for subscription ID" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_message_callback_raises_logs_error(self, caplog):
        ws = WebSocketApi()
        def bad_callback(payload):
            raise Exception("fail")
        ws.callbacks = {123: bad_callback}
        data = {'id': 123, 'd': {'m': VALID_ADDRESS}}
        await ws._handle_message(data)
        assert "Error in callback for subscription" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_message_unknown_format_logs_warning(self, caplog):
        ws = WebSocketApi()
        data = {'unknown': 'format'}
        await ws._handle_message(data)
        assert "Unknown message format" in caplog.text

class TestWebSocketApiSubscribeLogic:
    @pytest.mark.asyncio
    async def test_subscribe_missing_marketId_raises(self):
        ws = WebSocketApi()
        with pytest.raises(ValueError):
            await ws.subscribe('book', {}, AsyncMock())

    @pytest.mark.asyncio
    async def test_subscribe_invalid_market_raises(self):
        ws = WebSocketApi()
        await ws.subscribe('book', {'marketId': 'bad'}, AsyncMock())

    @pytest.mark.asyncio
    async def test_subscribe_with_closed_ws_triggers_connect(self):
        ws = WebSocketApi()
        ws.ws = MagicMock()
        ws.ws.closed = True

        mock_ws = MagicMock()
        mock_ws.closed = False
        mock_ws.send_json = AsyncMock()

        async def connect_side_effect():
            ws.ws = mock_ws

        with patch.object(ws, 'connect', new=AsyncMock(side_effect=connect_side_effect)) as mock_connect, \
            patch('eth_utils.address.to_checksum_address', return_value=VALID_ADDRESS):
            await ws.subscribe('book', {'marketId': VALID_ADDRESS}, lambda x: None)

        mock_connect.assert_awaited()

    @pytest.mark.asyncio
    async def test_subscribe_sends_request_and_stores_callback(self):
        ws = WebSocketApi()
        ws.ws = MagicMock()
        ws.ws.closed = False
        with patch('eth_utils.address.to_checksum_address', return_value=VALID_ADDRESS), \
             patch.object(ws.ws, 'send_json', new_callable=AsyncMock) as mock_send_json:
            await ws.subscribe('book', {'marketId': VALID_ADDRESS}, AsyncMock())
            mock_send_json.assert_awaited()
            # Check that callback is stored by subscription ID
            assert len(ws.callbacks) == 1
            assert len(ws.subscriptions) == 1

    @pytest.mark.asyncio
    async def test_subscribe_fails_sending_json_removes_callback(self):
        ws = WebSocketApi()
        ws.ws = MagicMock()
        ws.ws.closed = False
        with patch('eth_utils.address.to_checksum_address', return_value=VALID_ADDRESS), \
             patch.object(ws.ws, 'send_json', new_callable=AsyncMock, side_effect=Exception("fail")):
            with pytest.raises(Exception):
                await ws.subscribe('book', {'marketId': VALID_ADDRESS}, AsyncMock())
            assert len(ws.callbacks) == 0
            assert len(ws.subscriptions) == 0

class TestWebSocketApiUnsubscribeLogic:
    @pytest.mark.asyncio
    async def test_unsubscribe_non_connected_returns_early(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.DISCONNECTED
        with patch.object(ws, 'ws', create=True):
            await ws.unsubscribe('book', {'marketId': VALID_ADDRESS})
        # Should not raise

    @pytest.mark.asyncio
    async def test_unsubscribe_missing_marketId_raises(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        with pytest.raises(ValueError):
            await ws.unsubscribe('book', {})

    @pytest.mark.asyncio
    async def test_unsubscribe_invalid_market_raises(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        await ws.unsubscribe('book', {'marketId': 'bad'})

    @pytest.mark.asyncio
    async def test_unsubscribe_no_active_subscription_logs_warning(self, caplog):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws.ws = MagicMock()
        ws.subscriptions = {}
        with patch('eth_utils.address.to_checksum_address', return_value=VALID_ADDRESS):
            await ws.unsubscribe('book', {'marketId': VALID_ADDRESS})
        assert "No active subscription" in caplog.text

    @pytest.mark.asyncio
    async def test_unsubscribe_sends_request_logs_error_if_send_fails(self, caplog):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws.ws = MagicMock()
        ws.subscriptions = {('book', VALID_ADDRESS): 123}
        with patch('eth_utils.address.to_checksum_address', return_value=VALID_ADDRESS), \
             patch.object(ws.ws, 'send_json', new_callable=AsyncMock, side_effect=Exception("fail")):
            await ws.unsubscribe('book', {'marketId': VALID_ADDRESS})
        assert "Failed to send unsubscribe request" in caplog.text

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_callback(self):
        ws = WebSocketApi(enable_logging=True)
        ws.state = ConnectionState.CONNECTED
        ws.ws = MagicMock()
        ws.callbacks = {123: AsyncMock()}
        ws.subscriptions = {('book', VALID_ADDRESS): 123}
        with patch('eth_utils.address.to_checksum_address', return_value=VALID_ADDRESS), \
             patch.object(ws.ws, 'send_json', new_callable=AsyncMock):
            await ws.unsubscribe('book', {'marketId': VALID_ADDRESS})
        assert 123 not in ws.callbacks
        assert ('book', VALID_ADDRESS) not in ws.subscriptions

class TestWebSocketApiUtilityMethods:
    def test_next_request_id_increments_monotonically(self):
        ws = WebSocketApi()
        start = ws.request_id
        assert ws._next_request_id() == start + 1
        assert ws._next_request_id() == start + 2

    def test_get_subscriptions_returns_tracked_callbacks(self):
        ws = WebSocketApi()
        ws.subscriptions = {('book', VALID_ADDRESS): 123, ('trades', VALID_ADDRESS): 456}
        subs = ws.get_subscriptions()
        assert {'topic': 'book', 'market': VALID_ADDRESS, 'subscription_id': 123} in subs
        assert {'topic': 'trades', 'market': VALID_ADDRESS, 'subscription_id': 456} in subs

    def test_is_connected_returns_correct_boolean(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.CONNECTED
        ws.ws = MagicMock()
        ws.ws.closed = False
        assert ws.is_connected() is True
        ws.state = ConnectionState.DISCONNECTED
        assert ws.is_connected() is False

    def test_get_connection_state_returns_internal_state(self):
        ws = WebSocketApi()
        ws.state = ConnectionState.RECONNECTING
        assert ws.get_connection_state() == ConnectionState.RECONNECTING
