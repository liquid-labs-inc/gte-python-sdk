import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import aiohttp
from aiohttp import ClientResponseError, ClientError, ClientTimeout, RequestInfo
from yarl import URL
from multidict import CIMultiDict, CIMultiDictProxy

from gte_py.api.rest import RestApi


class MockResponse:
    def __init__(self, *, status=200, body="", raise_for_status=None):
        self.status = status
        self._body = body
        self._raise = raise_for_status

    async def text(self):
        return self._body

    def raise_for_status(self):
        if self._raise:
            raise self._raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def build_response(status=200, json_body=None, text_body=None, raise_exc=None):
    if json_body is not None:
        body = json.dumps(json_body)
    elif text_body is not None:
        body = text_body
    else:
        body = ""
    return MockResponse(status=status, body=body, raise_for_status=raise_exc)


def build_client_response_error(status=500):
    req_info = RequestInfo(
        url=URL("https://api-testnet.gte.xyz/v1/fail"),
        method="GET",
        headers=CIMultiDictProxy(CIMultiDict())
    )
    return ClientResponseError(
        request_info=req_info,
        history=(),
        status=status,
        message="Error",
        headers=None
    )


class TestRestApiInitialization:
    """Test RestApi initialization."""

    def test_default_parameters(self):
        """Test default parameters create valid instance."""
        client = RestApi()
        
        assert client.base_url == "https://api-testnet.gte.xyz/v1"
        assert client.timeout == 10
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.rate_limit_delay == 0.0
        assert client.enable_logging is True
        assert client.session is None
        assert client._last_request_time == 0.0
        assert client.default_headers == {"Content-Type": "application/json"}

    def test_custom_parameters(self):
        """Test custom parameters override defaults."""
        client = RestApi(
            base_url="https://custom.api.com",
            timeout=30,
            max_retries=5,
            retry_delay=2.0,
            rate_limit_delay=0.5,
            enable_logging=False
        )
        
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 30
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.rate_limit_delay == 0.5
        assert client.enable_logging is False

    def test_base_url_trailing_slash_stripped(self):
        """Test base_url trailing slash is stripped."""
        client = RestApi(base_url="https://api.test.com/")
        assert client.base_url == "https://api.test.com"


class TestRestApiConnectionHandling:
    """Test RestApi connection handling."""

    @pytest.mark.asyncio
    async def test_connect_creates_session_when_none(self):
        """Test connect() creates session when None."""
        client = RestApi()
        assert client.session is None
        
        await client.connect()
        
        assert client.session is not None
        assert not client.session.closed
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_skips_when_session_active(self):
        """Test connect() skips when session is active."""
        client = RestApi()
        await client.connect()
        original_session = client.session
        
        await client.connect()
        
        assert client.session is original_session
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_recreates_session_when_closed(self):
        """Test connect() recreates session when closed."""
        client = RestApi()
        await client.connect()
        original_session = client.session
        if original_session:
            await original_session.close()
        
        await client.connect()
        
        assert client.session is not original_session
        if client.session:
            assert not client.session.closed
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_closes_session_if_active(self):
        """Test disconnect() closes session if active."""
        client = RestApi()
        await client.connect()
        if client.session:
            assert not client.session.closed
        
        await client.disconnect()
        
        assert client.session is None

    @pytest.mark.asyncio
    async def test_disconnect_no_op_when_session_none(self):
        """Test disconnect() is no-op when session is None."""
        client = RestApi()
        assert client.session is None
        
        # Should not raise any exception
        await client.disconnect()
        
        assert client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test __aenter__/__aexit__ create and close session properly."""
        client = RestApi()
        
        async with client:
            assert client.session is not None
            if client.session:
                assert not client.session.closed
        
        assert client.session is None


class TestRestApiRateLimiting:
    """Test RestApi rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_no_delay(self):
        """Test _rate_limit() with rate_limit_delay = 0.0 does not sleep."""
        client = RestApi(rate_limit_delay=0.0)
        
        with patch('asyncio.sleep') as mock_sleep:
            await client._rate_limit()
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_with_delay(self):
        """Test _rate_limit() with rate_limit_delay > 0.0 sleeps correct duration."""
        client = RestApi(rate_limit_delay=0.1)
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('time.monotonic', return_value=0.0):
            await client._rate_limit()
            mock_sleep.assert_awaited_once_with(0.1)

    @pytest.mark.asyncio
    async def test_rate_limit_skips_sleep_when_delayed(self):
        """Test _rate_limit() with delayed last request skips sleep."""
        client = RestApi(rate_limit_delay=0.1)
        client._last_request_time = 0.05  # Recent request
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('time.monotonic', return_value=0.06):  # Only 0.01 seconds passed
            await client._rate_limit()
            # Use approximate comparison for floating point precision
            assert mock_sleep.call_count == 1
            assert abs(mock_sleep.call_args[0][0] - 0.09) < 0.001

    @pytest.mark.asyncio
    async def test_rate_limit_no_sleep_when_enough_time_passed(self):
        """Test _rate_limit() doesn't sleep when enough time has passed."""
        client = RestApi(rate_limit_delay=0.1)
        client._last_request_time = 0.0
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('time.monotonic', return_value=0.2):  # 0.2 seconds passed
            await client._rate_limit()
            mock_sleep.assert_not_called()


class TestRestApiRequestCore:
    """Test RestApi _request() core functionality."""

    @pytest.mark.asyncio
    async def test_successful_request_valid_json(self):
        """Test successful request path with valid JSON."""
        client = RestApi()
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            result = await client._request("GET", "/test")
            
            assert result == {"ok": True}
            mock_request.assert_called_once()
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_successful_request_empty_body(self):
        """Test successful request with empty body returns {}."""
        client = RestApi()
        await client.connect()
        
        response = build_response(status=200, text_body="  ")
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            result = await client._request("GET", "/test")
            
            assert result == {}
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_successful_request_invalid_json(self):
        """Test successful request with invalid JSON raises ValueError."""
        client = RestApi()
        await client.connect()
        
        response = build_response(status=200, text_body="{invalid json")
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            with pytest.raises(ValueError, match="Invalid JSON response"):
                await client._request("GET", "/test")
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_500_response_triggers_retries(self):
        """Test 500 response triggers retries and eventually raises."""
        client = RestApi(max_retries=2, retry_delay=0.01)
        await client.connect()
        
        error = build_client_response_error(500)
        response = build_response(status=500, raise_exc=error)
        
        with patch.object(client.session, 'request') as mock_request, \
             patch('asyncio.sleep') as mock_sleep:
            mock_request.return_value.__aenter__.return_value = response
            
            with pytest.raises(ClientResponseError):
                await client._request("GET", "/test")
            
            # Should have been called 3 times (initial + 2 retries)
            assert mock_request.call_count == 3
            assert mock_sleep.call_count == 2  # 2 retries
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_502_503_504_responses_trigger_retries(self):
        """Test 502/503/504 responses trigger retries."""
        client = RestApi(max_retries=1, retry_delay=0.01)
        await client.connect()
        
        for status in [502, 503, 504]:
            error = build_client_response_error(status)
            response = build_response(status=status, raise_exc=error)
            
            with patch.object(client.session, 'request') as mock_request, \
                 patch('asyncio.sleep') as mock_sleep:
                mock_request.return_value.__aenter__.return_value = response
                
                with pytest.raises(ClientResponseError):
                    await client._request("GET", "/test")
                
                assert mock_request.call_count == 2  # initial + 1 retry
                assert mock_sleep.call_count == 1
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_400_404_responses_no_retry(self):
        """Test non-retriable 400/404 returns raises immediately."""
        client = RestApi(max_retries=3, retry_delay=0.01)
        await client.connect()
        
        for status in [400, 404]:
            error = build_client_response_error(status)
            response = build_response(status=status, raise_exc=error)
            
            with patch.object(client.session, 'request') as mock_request, \
                 patch('asyncio.sleep') as mock_sleep:
                mock_request.return_value.__aenter__.return_value = response
                
                with pytest.raises(ClientResponseError):
                    await client._request("GET", "/test")
                
                assert mock_request.call_count == 1  # No retries
                assert mock_sleep.call_count == 0
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_network_errors_retry_and_fail(self):
        """Test network errors (ClientError, TimeoutError) retry and fail after limit."""
        client = RestApi(max_retries=2, retry_delay=0.01)
        await client.connect()
        
        for error_type in [ClientError, asyncio.TimeoutError]:
            with patch.object(client.session, 'request') as mock_request, \
                 patch('asyncio.sleep') as mock_sleep:
                mock_request.return_value.__aenter__.side_effect = error_type("Network error")
                
                with pytest.raises(error_type):
                    await client._request("GET", "/test")
                
                assert mock_request.call_count == 3  # initial + 2 retries
                assert mock_sleep.call_count == 2
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_max_retries_zero_skips_retry(self):
        """Test max_retries=0 skips retry."""
        client = RestApi(max_retries=0, retry_delay=0.01)
        await client.connect()
        
        error = build_client_response_error(500)
        response = build_response(status=500, raise_exc=error)
        
        with patch.object(client.session, 'request') as mock_request, \
             patch('asyncio.sleep') as mock_sleep:
            mock_request.return_value.__aenter__.return_value = response
            
            with pytest.raises(ClientResponseError):
                await client._request("GET", "/test")
            
            assert mock_request.call_count == 1  # No retries
            assert mock_sleep.call_count == 0
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_logging_enabled(self):
        """Test logs request/response only if enable_logging=True."""
        client = RestApi(enable_logging=True)
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request, \
             patch('gte_py.api.rest.logger.debug') as mock_logger:
            mock_request.return_value.__aenter__.return_value = response
            
            await client._request("GET", "/test")
            
            # Should have logged request and response
            assert mock_logger.call_count >= 2
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_logging_disabled(self):
        """Test no logging when enable_logging=False."""
        client = RestApi(enable_logging=False)
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request, \
             patch('gte_py.api.rest.logger.debug') as mock_logger:
            mock_request.return_value.__aenter__.return_value = response
            
            await client._request("GET", "/test")
            
            # Should not have logged anything
            mock_logger.assert_not_called()
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_long_responses_skipped_from_logging(self):
        """Test long responses are skipped from logging."""
        client = RestApi(enable_logging=True)
        await client.connect()
        
        # Create a response with very long body (valid JSON)
        long_body = '{"data": "' + "x" * 2000 + '"}'  # Longer than 1000 character limit
        response = build_response(status=200, text_body=long_body)
        
        with patch.object(client.session, 'request') as mock_request, \
             patch('gte_py.api.rest.logger.debug') as mock_logger:
            mock_request.return_value.__aenter__.return_value = response
            
            await client._request("GET", "/test")
            
            # Should not have logged the long response body
            logged_calls = [call.args[0] for call in mock_logger.call_args_list]
            assert not any("Response data:" in call for call in logged_calls)
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_auto_connect_when_session_none(self):
        """Test _request() auto-connects when session is None."""
        client = RestApi()
        assert client.session is None
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client, 'connect') as mock_connect, \
             patch.object(client, 'session') as mock_session:
            mock_session.request.return_value.__aenter__.return_value = response
            
            await client._request("GET", "/test")
            
            mock_connect.assert_awaited_once()


class TestRestApiHttpMethods:
    """Test RestApi HTTP verb methods."""

    @pytest.mark.asyncio
    async def test_get_delegates_to_request(self):
        """Test get() delegates to _request() with method GET."""
        client = RestApi()
        await client.connect()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"ok": True}
            
            result = await client.get("/test", {"param": "value"})
            
            mock_request.assert_awaited_once_with("GET", "/test", params={"param": "value"})
            assert result == {"ok": True}
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_post_uses_post_with_data(self):
        """Test post() uses POST with data payload."""
        client = RestApi()
        await client.connect()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"ok": True}
            
            result = await client.post("/test", {"data": "value"})
            
            mock_request.assert_awaited_once_with("POST", "/test", data={"data": "value"})
            assert result == {"ok": True}
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_put_uses_put(self):
        """Test put() uses PUT."""
        client = RestApi()
        await client.connect()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"ok": True}
            
            result = await client.put("/test", {"data": "value"})
            
            mock_request.assert_awaited_once_with("PUT", "/test", data={"data": "value"})
            assert result == {"ok": True}
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_delete_uses_delete(self):
        """Test delete() uses DELETE."""
        client = RestApi()
        await client.connect()
        
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"ok": True}
            
            result = await client.delete("/test")
            
            mock_request.assert_awaited_once_with("DELETE", "/test")
            assert result == {"ok": True}
        
        await client.disconnect()


class TestRestApiHeadersAndPayload:
    """Test RestApi header and payload behavior."""

    @pytest.mark.asyncio
    async def test_content_type_header_sent(self):
        """Test Content-Type: application/json is sent in headers."""
        client = RestApi()
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            await client._request("GET", "/test")
            
            # Check that request was called with correct headers
            call_args = mock_request.call_args
            assert call_args[1]['headers'] == {"Content-Type": "application/json"}
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_query_parameters_passed_correctly(self):
        """Test query parameters are passed correctly."""
        client = RestApi()
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            await client._request("GET", "/test", params={"key": "value", "num": 123})
            
            # Check that params were passed correctly
            call_args = mock_request.call_args
            assert call_args[1]['params'] == {"key": "value", "num": 123}
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_request_body_sent_as_json(self):
        """Test request body is sent as JSON."""
        client = RestApi()
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            data = {"key": "value", "nested": {"inner": 123}}
            await client._request("POST", "/test", data=data)
            
            # Check that data was passed as json parameter
            call_args = mock_request.call_args
            assert call_args[1]['json'] == data
        
        await client.disconnect()


class TestRestApiMiscellaneous:
    """Test RestApi miscellaneous functionality."""

    @pytest.mark.asyncio
    async def test_url_construction_handles_double_slashes(self):
        """Test URL construction handles double slashes safely."""
        client = RestApi(base_url="https://api.test.com")
        await client.connect()
        
        response = build_response(status=200, json_body={"ok": True})
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.return_value.__aenter__.return_value = response
            
            # Test various slash combinations
            await client._request("GET", "/test")
            call_args = mock_request.call_args
            assert call_args[0][1] == "https://api.test.com/test"
            
            await client._request("GET", "test")
            call_args = mock_request.call_args
            assert call_args[0][1] == "https://api.test.com/test"
            
            await client._request("GET", "//test")
            call_args = mock_request.call_args
            assert call_args[0][1] == "https://api.test.com/test"
        
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff for retries."""
        client = RestApi(max_retries=2, retry_delay=0.1)
        await client.connect()
        
        error = build_client_response_error(500)
        response = build_response(status=500, raise_exc=error)
        
        with patch.object(client.session, 'request') as mock_request, \
             patch('asyncio.sleep') as mock_sleep:
            mock_request.return_value.__aenter__.return_value = response
            
            with pytest.raises(ClientResponseError):
                await client._request("GET", "/test")
            
            # Should have exponential backoff: 0.1, 0.2
            expected_calls = [
                ((0.1,),),  # First retry: 0.1 * 2^0
                ((0.2,),),  # Second retry: 0.1 * 2^1
            ]
            assert mock_sleep.call_args_list == expected_calls
        
        await client.disconnect()
