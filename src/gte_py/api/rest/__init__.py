"""REST API client for GTE."""

import json
import logging

import aiohttp
from eth_typing import ChecksumAddress

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
            "Content-Type": "application/json",
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
            async with self.session.request(
                method, url, params=params, json=data, headers=self.default_headers
            ) as response:
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

    # Info endpoint
    async def get_info(self) -> dict:
        """Get GTE info.

        Returns:
            Dict: GTE information including stats
        """
        return await self._request("GET", "/v1/info")

    # Token endpoints
    async def get_tokens(
        self,
        metadata: bool = False,
        creator: str | None = None,
        market_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get list of tokens supported on GTE.

        Args:
            metadata: Returns tokens with metadata
            creator: Returns assets created by the given user address
            market_type: Filters assets by the given market type (amm, launchpad)
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            Dict: List of tokens
        """
        params: dict = {"limit": limit, "offset": offset, "metadata": metadata}
        if creator:
            params["creator"] = creator
        if market_type:
            params["marketType"] = market_type
        return await self._request("GET", "/v1/tokens", params=params)

    async def search_tokens(self, query: str, limit: int = 100) -> dict:
        """Search tokens based on name or symbol.

        Args:
            query: Search query
            limit: Range 1-1000

        Returns:
            Dict: List of matching tokens
        """
        params: dict = {"q": query, "limit": limit}
        return await self._request("GET", "/v1/tokens/search", params=params)

    async def get_token(self, token_address: str | ChecksumAddress) -> dict:
        """Get token metadata by address.

        Args:
            token_address: EVM address of the token

        Returns:
            Dict: Token metadata information
        """
        return await self._request("GET", f"/v1/tokens/{token_address}")

    # Markets endpoints
    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        market_type: str | None = None,
        sort_by: str = "marketCap",
        token_address: str | None = None,
        newly_graduated: bool = False,
    ) -> dict:
        """Get list of markets.

        Args:
            limit: Range 1-1000
            offset: Min value 0
            market_type: Filter by market type (amm, launchpad)
            sort_by: Sort markets in descending order (marketCap, createdAt, volume)
            token_address: Filter markets by the specified token address
            newly_graduated: Returns newly graduated markets

        Returns:
            Dict: List of markets
        """
        params: dict = {"limit": limit, "offset": offset, "sortBy": sort_by}
        if market_type:
            params["marketType"] = market_type
        if token_address:
            params["tokenAddress"] = token_address
        if newly_graduated:
            params["newlyGraduated"] = newly_graduated
        return await self._request("GET", "/v1/markets", params=params)

    async def get_market(self, market_address: str | ChecksumAddress) -> dict:
        """Get market by address.

        Args:
            market_address: EVM address of the market

        Returns:
            Dict: Market information
        """
        return await self._request("GET", f"/v1/markets/{market_address}")

    async def get_candles(
        self,
        market_address: str | ChecksumAddress,
        interval: str,
        start_time: int,
        end_time: int | None = None,
        limit: int = 500,
    ) -> dict:
        """Get candles for a market.

        Args:
            market_address: EVM address of the market
            interval: Interval of the candle (1s, 15s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
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

    async def get_trades(
        self, market_address: str | ChecksumAddress, limit: int = 100, offset: int = 0
    ) -> dict:
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

    async def get_order_book(self, market_address: str | ChecksumAddress, limit: int = 10) -> dict:
        """Get order book snapshot for a market.

        Args:
            market_address: EVM address of the market
            limit: Number of price levels to include on each side, range 1-100

        Returns:
            Dict: Order book data with bids and asks
        """
        params = {"limit": limit}
        return await self._request("GET", f"/v1/markets/{market_address}/book", params=params)

    async def get_order_book_snapshot(
        self, market_address: str | ChecksumAddress, limit: int = 10
    ) -> OrderBookSnapshot:
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
            (float(bid["price"]), float(bid["size"]), bid.get("number", 0))
            for bid in response.get("bids", [])
        ]

        asks = [
            (float(ask["price"]), float(ask["size"]), ask.get("number", 0))
            for ask in response.get("asks", [])
        ]

        return OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=response.get("timestamp", 0),
            market_address=market_address,
        )

    # Users endpoints
    async def get_user_lp_positions(self, user_address: str | ChecksumAddress) -> dict:
        """Get LP positions for a user.

        Args:
            user_address: EVM address of the user

        Returns:
            Dict: List of LP positions
        """
        return await self._request("GET", f"/v1/users/{user_address}/lppositions")

    async def get_user_portfolio(self, user_address: str | ChecksumAddress) -> dict:
        """Get user's portfolio.

        Args:
            user_address: EVM address of the user

        Returns:
            Dict: User portfolio including token balances
        """
        return await self._request("GET", f"/v1/users/{user_address}/portfolio")

    async def get_user_trades(
        self,
        user_address: str | ChecksumAddress,
        market_address: str | ChecksumAddress | None = None,
    ) -> dict:
        """Get trades for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market (optional)

        Returns:
            Dict: List of user trades
        """
        params = {}
        if market_address:
            params["market_address"] = market_address
        return await self._request("GET", f"/v1/users/{user_address}/trades", params=params)

    async def get_user_open_orders(
        self, user_address: str | ChecksumAddress, market_address: str | ChecksumAddress
    ) -> dict:
        """Get open orders for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market

        Returns:
            Dict: List of user's open orders
        """
        params = {"market_address": market_address}
        return await self._request("GET", f"/v1/users/{user_address}/open_orders", params=params)

    async def get_user_filled_orders(
        self, user_address: str | ChecksumAddress, market_address: str | ChecksumAddress
    ) -> dict:
        """Get filled orders for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market

        Returns:
            Dict: List of user's filled orders
        """
        params = {"market_address": market_address}
        return await self._request("GET", f"/v1/users/{user_address}/filled_orders", params=params)

    async def get_user_order_history(
        self, user_address: str | ChecksumAddress, market_address: str | ChecksumAddress
    ) -> dict:
        """Get order history for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market

        Returns:
            Dict: List of user's order history
        """
        params = {"market_address": market_address}
        return await self._request("GET", f"/v1/users/{user_address}/order_history", params=params)
