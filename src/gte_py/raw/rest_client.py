"""REST API client for GTE."""

import logging
from typing import Dict, List, Optional, Union, Any
import aiohttp
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class GTERestClient:
    """REST API client for GTE."""

    def __init__(self, base_url: str = "https://api.gte.io"):
        """Initialize the client.

        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        """Enter the async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                       data: Optional[Dict] = None) -> Dict:
        """Make a request to the API.

        Args:
            method: HTTP method to use
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            Dict: API response
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(method, url, params=params, json=data) as response:
                response_data = await response.json()
                if response.status >= 400:
                    logger.error(f"API error: {response.status} - {response_data}")
                    raise ValueError(f"API error: {response.status} - {response_data}")
                return response_data
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {e}")
            raise

    # Health endpoint
    async def get_health(self) -> Dict:
        """Get API health status.

        Returns:
            Dict: Health status information
        """
        return await self._request("GET", "/health")

    # Assets endpoints
    async def get_assets(self, creator: Optional[str] = None, 
                         limit: int = 100, offset: int = 0) -> Dict:
        """Get list of assets.

        Args:
            creator: Returns assets created by the given user address
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of assets
        """
        params = {"limit": limit, "offset": offset}
        if creator:
            params["creator"] = creator
        return await self._request("GET", "/assets", params=params)

    async def get_asset(self, asset_address: str) -> Dict:
        """Get asset by address.

        Args:
            asset_address: EVM address of the asset

        Returns:
            Dict: Asset information
        """
        return await self._request("GET", f"/assets/{asset_address}")

    # Markets endpoints
    async def get_markets(self, limit: int = 100, offset: int = 0, 
                          market_type: Optional[str] = None, 
                          asset: Optional[str] = None, 
                          price: Optional[float] = None) -> Dict:
        """Get list of markets.

        Args:
            limit: Range 1-1000
            offset: Min value 0
            market_type: Filter by market type (amm, launchpad)
            asset: Address of the base asset to filter by
            price: Returns markets with price less than given value

        Returns:
            Dict: List of markets
        """
        params = {"limit": limit, "offset": offset}
        if market_type:
            params["marketType"] = market_type
        if asset:
            params["asset"] = asset
        if price is not None:
            params["price"] = price
        return await self._request("GET", "/markets", params=params)

    async def get_market(self, market_address: str) -> Dict:
        """Get market by address.

        Args:
            market_address: EVM address of the market

        Returns:
            Dict: Market information
        """
        return await self._request("GET", f"/markets/{market_address}")

    async def get_candles(self, market_address: str, interval: str, 
                         start_time: int, end_time: Optional[int] = None, 
                         limit: int = 500) -> Dict:
        """Get candles for a market.

        Args:
            market_address: EVM address of the market
            interval: Interval of the candle (1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Range 1-1000

        Returns:
            Dict: List of candles
        """
        params = {
            "interval": interval,
            "startTime": start_time,
            "limit": limit
        }
        if end_time:
            params["endTime"] = end_time
        return await self._request("GET", f"/markets/{market_address}/candles", params=params)

    async def get_trades(self, market_address: str, limit: int = 100, offset: int = 0) -> Dict:
        """Get trades for a market.

        Args:
            market_address: EVM address of the market
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of trades
        """
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", f"/markets/{market_address}/trades", params=params)

    # Users endpoints
    async def get_user_positions(self, user_address: str) -> Dict:
        """Get LP positions for a user.

        Args:
            user_address: EVM address of the user

        Returns:
            Dict: List of LP positions
        """
        return await self._request("GET", f"/users/{user_address}/positions")

    async def get_user_assets(self, user_address: str, limit: int = 100, offset: int = 0) -> Dict:
        """Get assets held by a user.

        Args:
            user_address: EVM address of the user
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of assets held by the user
        """
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", f"/users/{user_address}/assets", params=params)
