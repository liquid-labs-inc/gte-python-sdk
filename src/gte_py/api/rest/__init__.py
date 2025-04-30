"""REST API client for GTE."""
import json
import logging

import aiohttp

from gte_py.models import OrderBookSnapshot

logger = logging.getLogger(__name__)


class RestApi:
    """REST API client for GTE."""

    def __init__(self, base_url: str = "https://api.gte.io"):
        """Initialize the client.

        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url.rstrip("/")
        self.default_headers = {
            'Content-Type': 'application/json',
        }
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Enter the async context."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        if self.session:
            await self.session.close()

    async def _request(
            self,
            method: str,
            endpoint: str,
            params: dict | None = None,
            data: dict | None = None,
    ) -> dict:
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
            await self.__aenter__()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with self.session.request(method, url, params=params, json=data,
                                            headers=self.default_headers) as response:
                response_data = await response.text()
                response.raise_for_status()

                data = json.loads(response_data)
                return data
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {e} url={url} params={params} data={data}")
            raise

    # Health endpoint
    async def get_health(self) -> dict:
        """Get API health status.

        Returns:
            Dict: Health status information
        """
        return await self._request("GET", "/v1/health")

    # Assets endpoints
    async def get_assets(
            self, creator: str | None = None, limit: int = 100, offset: int = 0
    ) -> dict:
        """Get list of assets.

        Args:
            creator: Returns assets created by the given user address
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of assets
        """
        params: dict = {"limit": limit, "offset": offset}
        if creator:
            params["creator"] = creator
        return await self._request("GET", "/v1/assets", params=params)

    async def get_asset(self, asset_address: str) -> dict:
        """Get asset by address.

        Args:
            asset_address: EVM address of the asset

        Returns:
            Dict: Asset information
        """
        return await self._request("GET", f"/v1/assets/{asset_address}")

    # Markets endpoints
    async def get_markets(
            self,
            limit: int = 100,
            offset: int = 0,
            market_type: str | None = None,
            asset: str | None = None,
            price: float | None = None,
    ) -> dict:
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
        params: dict = {"limit": limit, "offset": offset}
        if market_type:
            params["marketType"] = market_type
        if asset:
            params["asset"] = asset
        if price is not None:
            params["price"] = price
        return await self._request("GET", "/v1/markets", params=params)

    async def get_market(self, market_address: str) -> dict:
        """Get market by address.

        Args:
            market_address: EVM address of the market

        Returns:
            Dict: Market information
        """
        return await self._request("GET", f"/v1/markets/{market_address}")

    async def get_candles(
            self,
            market_address: str,
            interval: str,
            start_time: int,
            end_time: int | None = None,
            limit: int = 500,
    ) -> dict:
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
        params: dict = {"interval": interval, "startTime": start_time, "limit": limit}
        if end_time:
            params["endTime"] = end_time
        return await self._request("GET", f"/v1/markets/{market_address}/candles", params=params)

    async def get_trades(self, market_address: str, limit: int = 100, offset: int = 0) -> dict:
        """Get trades for a market.

        Args:
            market_address: EVM address of the market
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of trades
        """
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", f"/v1/markets/{market_address}/trades", params=params)

    # Users endpoints
    async def get_user_positions(self, user_address: str) -> dict:
        """Get LP positions for a user.

        Args:
            user_address: EVM address of the user

        Returns:
            Dict: List of LP positions
        """
        return await self._request("GET", f"/v1/users/{user_address}/positions")

    async def get_user_assets(self, user_address: str, limit: int = 100, offset: int = 0) -> dict:
        """Get assets held by a user.

        Args:
            user_address: EVM address of the user
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of assets held by the user
        """
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", f"/v1/users/{user_address}/assets", params=params)

    async def get_order_book(self, market_address: str, limit: int = 5) -> dict:
        """Get order book snapshot for a market.

        Args:
            market_address: EVM address of the market
            limit: Number of price levels to include on each side, range 1-100

        Returns:
            Dict: Order book data with bids and asks
        """
        params = {"limit": limit}
        return await self._request("GET", f"/v1/markets/{market_address}/book", params=params)

    async def get_order_book_snapshot(self, market_address: str, limit: int = 5) -> OrderBookSnapshot:
        """Get typed order book snapshot for a market.

        Args:
            market_address: EVM address of the market
            limit: Number of price levels to include on each side, range 1-100

        Returns:
            OrderBookSnapshot: Typed order book data with bids and asks
        """
        response = await self.get_order_book(market_address, limit)

        # Convert bid and ask data to appropriate format
        bids = [
            (float(bid["px"]), float(bid["sz"]), bid.get("n", 0))
            for bid in response.get("bids", [])
        ]

        asks = [
            (float(ask["px"]), float(ask["sz"]), ask.get("n", 0))
            for ask in response.get("asks", [])
        ]

        return OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=response.get("timestamp", 0),
            market_address=market_address
        )
