"""REST API client for GTE."""

import asyncio
import json
import logging
import time
from typing import Any, cast
from decimal import Decimal
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)


class RestApi:
    """REST API client for GTE."""

    def __init__(
        self, 
        base_url: str = "https://perps-api.gte.xyz/v1",
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.0,
        enable_logging: bool = True
    ):
        """Initialize the client.

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            rate_limit_delay: Minimum delay between requests to respect rate limits
            enable_logging: Whether to enable request/response logging
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.enable_logging = enable_logging
        
        self.default_headers = {
            "Content-Type": "application/json",
        }
        self.session: aiohttp.ClientSession | None = None
        self._last_request_time = 0.0
    
    async def connect(self):
        """Connect to the API."""
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.debug(f"Created new session for {self.base_url}")
    
    async def disconnect(self):
        """Disconnect from the API."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            logger.debug("Closed session")

    async def __aenter__(self):
        """Enter the async context."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        await self.disconnect()

    async def _rate_limit(self):
        """Ensure minimum delay between requests."""
        now = time.monotonic()
        time_since_last = now - self._last_request_time
        delay = self.rate_limit_delay - time_since_last
        if delay > 0:
            await asyncio.sleep(delay)
        self._last_request_time = time.monotonic()

    async def _request(
            self,
            method: str,
            endpoint: str,
            params: dict[str, Any] | None = None,
            data: dict[str, Any] | None = None,
    ):
        """Make a request to the API.

        Args:
            method: HTTP method to use
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            API response as dictionary or list of dictionaries
            
        Raises:
            aiohttp.ClientError: For HTTP errors
            ValueError: For invalid JSON responses
            Exception: For other errors after retries exhausted
        """
        await self._rate_limit()
        
        if self.session is None or self.session.closed:
            await self.connect()

        self.session = cast(aiohttp.ClientSession, self.session)
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        # Log request if enabled
        if self.enable_logging:
            logger.debug(f"Making {method} request to {url}")
            if params:
                logger.debug(f"Query params: {params}")
            if data:
                logger.debug(f"Request data: {data}")

        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.request(
                        method, url, params=params, json=data, headers=self.default_headers
                ) as response:
                    response_data = await response.text()
                    
                    # Log response if enabled
                    if self.enable_logging:
                        logger.debug(f"Response status: {response.status}")
                        if len(response_data) < 1000:  # Don't log very large responses
                            logger.debug(f"Response data: {response_data}")
                    
                    response.raise_for_status()
                    
                    if not response_data.strip():
                        return {}
                    
                    try:
                        parsed_json = json.loads(response_data, parse_float=Decimal)
                        return parsed_json
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response: {response_data[:200]}...")
                        raise ValueError(f"Invalid JSON response: {e}")
                        
            except aiohttp.ClientResponseError as e:
                last_exception = e
                if e.status >= 500:  # Server errors - retry
                    logger.warning(f"Server error {e.status} on attempt {attempt + 1}/{self.max_retries + 1}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                else:  # Client errors - don't retry
                    logger.error(f"Client error {e.status}: {e.message}")
                    raise
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt + 1}/{self.max_retries + 1}: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts")
                    raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        assert False, "Unreachable retry fall-through"

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response
        """
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a POST request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            API response
        """
        return await self._request("POST", endpoint, data=data)

    async def put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            API response
        """
        return await self._request("PUT", endpoint, data=data)

    async def delete(self, endpoint: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a DELETE request.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            API response
        """
        return await self._request("DELETE", endpoint)
