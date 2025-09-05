"""Market data access client for GTE."""

import logging
from typing import Any, Callable
from eth_typing import ChecksumAddress
import requests

from gte_py.api.rest import RestApi
from gte_py.api.ws import WebSocketApi
from gte_py.models import (
    Token, Market, Candle, Trade, Position, OrderBookSnapshot
)

logger = logging.getLogger(__name__)


class InfoClient:
    """
    Retrieves and caches market and token data from chain or REST API.
    
    This client provides methods to fetch token and market information,
    with intelligent caching to minimize redundant requests.
    """

    def __init__(
        self,
        rest: RestApi,
        websocket: WebSocketApi,
    ):
        """
        Initialize the InfoClient.
        
        Args:
            rest: REST API client for fetching data
            websocket: WebSocket API client for real-time data
        """
        self._rest: RestApi = rest
        self._websocket: WebSocketApi = websocket
        self._subscriptions: dict[str, dict[str, Any]] = {}

    def __getattr__(self, name: str) -> Any:
        """
        Delegate unknown attributes to the REST API or WebSocket client.
        
        This allows direct access to all REST API and WebSocket methods without explicit wrappers.
        """
        # Check REST API first
        if hasattr(self._rest, name):
            return getattr(self._rest, name)
        
        # Check WebSocket API
        if hasattr(self._websocket, name):
            return getattr(self._websocket, name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    # ================= REST API METHODS =================

    async def get_health(self) -> dict[str, Any]:
        """Get API health status.

        Returns:
            Health status information
        """
        return await self._rest._request("GET", "/health")

    async def get_info(self) -> dict[str, Any]:
        """Get GTE info.

        Returns:
            GTE information including stats
        """
        return await self._rest._request("GET", "/info")

    # Token methods
    async def get_tokens(
        self,
        creator: str | None = None,
        market_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Token]:
        """Get list of tokens supported on GTE.

        Args:
            creator: Returns assets created by the given user address
            market_type: Filters assets by the given market type (amm, bonding-curve, clob-spot)
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            List of Token objects
        """
        params = {"limit": limit, "offset": offset}
        if creator:
            params["creator"] = creator
        if market_type:
            params["marketType"] = market_type
        response = await self._rest._request("GET", "/tokens", params=params)
        return [Token.from_api(token_data) for token_data in response]

    async def search_tokens(self, query: str, market_type: str | None = None) -> list[Token]:
        """Search tokens based on name or symbol.

        Args:
            query: Search query
            market_type: Filters assets by the given market type (amm, bonding-curve, clob-spot)

        Returns:
            List of matching Token objects
        """
        params = {"q": query}
        if market_type:
            params["marketType"] = market_type
        response = await self._rest._request("GET", "/tokens/search", params=params)
        return [Token.from_api(token_data) for token_data in response]

    async def get_token(self, token_address: str | ChecksumAddress) -> Token:
        """Get token metadata by address.

        Args:
            token_address: EVM address of the token

        Returns:
            Token object with metadata information
        """
        response = await self._rest._request("GET", f"/tokens/{token_address}")
        return Token.from_api(response)

    # Market methods
    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        market_type: str | None = None,
        sort_by: str = "marketCap",
        token_address: str | None = None,
    ) -> list[Market]:
        """Get list of markets.

        Args:
            limit: Range 1-1000
            offset: Min value 0
            market_type: Filter by market type (amm, launchpad)
            sort_by: Sort markets in descending order (marketCap, createdAt, volume)
            token_address: Filter markets by the specified token address
            newly_graduated: Returns newly graduated markets

        Returns:
            List of Market objects
        """
        params = {"limit": limit, "offset": offset, "sortBy": sort_by}
        if market_type:
            params["marketType"] = market_type
        if token_address:
            params["tokenAddress"] = token_address
        response = await self._rest._request("GET", "/markets", params=params)
        return [Market.from_api(market_data) for market_data in response]
    
    async def search_markets(self, query: str, market_type: str | None = None) -> list[Market]:
        """Search markets based on name or symbol.

        Args:
            query: Search query
            market_type: Filters assets by the given market type (amm, bonding-curve, clob-spot)

        Returns:
            List of matching Market objects
        """
        params = {"q": query}
        if market_type:
            params["marketType"] = market_type
        response = await self._rest._request("GET", "/markets/search", params=params)
        return [Market.from_api(market_data) for market_data in response]

    async def get_market(self, market_address: str | ChecksumAddress) -> Market:
        """Get market by address.

        Args:
            market_address: EVM address of the market

        Returns:
            Market object with market information
        """
        response = await self._rest._request("GET", f"/markets/{market_address}")
        return Market.from_api(response)
    
    async def get_dash_markets(self, dash_type: str, limit: int = 100) -> list[Market]:
        """Get dash markets.
        
        Args:
            limit: Range 1-1000
            dash_type: Filters assets by the given dash type (new, about-to-graduate, graduated)
        Returns:
            List of Market objects
        """
        params = {"limit": limit, "dashType": dash_type}
        response = await self._rest._request("GET", "/markets/dash", params=params)
        return [Market.from_api(market_data) for market_data in response]

    async def get_candles(
        self,
        market_address: str | ChecksumAddress,
        interval: str,
        start_time: int,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[Candle]:
        """Get candles for a market.

        Args:
            market_address: EVM address of the market
            interval: Interval of the candle (1s, 15s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds, if not provided, the current time will be used
            limit: Range 1-1000 (default 500)

        Returns:
            List of Candle objects
        """
        params = {"interval": interval, "startTime": start_time, "limit": limit}
        if end_time:
            params["endTime"] = end_time
        response = await self._rest._request("GET", f"/markets/{market_address}/candles", params=params)
        return [Candle.from_api(candle_data) for candle_data in response]

    async def get_trades(
        self, market_address: str | ChecksumAddress, limit: int = 100, offset: int = 0
    ) -> list[Trade]:
        """Get trades for a market.

        Args:
            market_address: EVM address of the market
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            List of Trade objects
        """
        params = {"limit": limit, "offset": offset}
        response = await self._rest._request("GET", f"/markets/{market_address}/trades", params=params)
        return [Trade.from_api(trade_data) for trade_data in response]

    async def get_order_book(self, market_address: str | ChecksumAddress, limit: int = 20) -> OrderBookSnapshot:
        """Get order book snapshot for a market.

        Args:
            market_address: EVM address of the market
            limit: Number of price levels to include on each side, range 1-20 (default 20)

        Returns:
            OrderBookSnapshot object with bids and asks
        """
        params = {"limit": limit}
        response = await self._rest._request("GET", f"/markets/{market_address}/book", params=params)
        return OrderBookSnapshot.from_api(response)

    # User methods
    async def get_user_lp_positions(self, user_address: str | ChecksumAddress) -> list[Position]:
        """Get LP positions for a user.

        Args:
            user_address: EVM address of the user

        Returns:
            List of Position objects
        """
        response = await self._rest._request("GET", f"/users/{user_address}/lppositions")
        return [Position.from_api(position_data) for position_data in response]

    async def get_user_portfolio(self, user_address: str | ChecksumAddress) -> dict[str, Any]:
        """Get user's portfolio.

        Args:
            user_address: EVM address of the user

        Returns:
            User portfolio including token balances
        """
        return await self._rest._request("GET", f"/users/{user_address}/portfolio")

    async def get_user_trades(
        self,
        user_address: str | ChecksumAddress,
        market_address: str | ChecksumAddress | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Trade]:
        """Get trades for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market (optional)
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            List of Trade objects
        """
        params = {"limit": limit, "offset": offset}
        if market_address:
            params["market_address"] = str(market_address)
        response = await self._rest._request("GET", f"/users/{user_address}/trades", params=params)
        return [Trade.from_api(trade_data) for trade_data in response]

    async def get_user_open_orders(
        self, user_address: ChecksumAddress, market_address: ChecksumAddress,
        limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get open orders for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            List of Orders
        """
        params = {"limit": limit, "offset": offset, "market_address": str(market_address)}
        response = await self._rest._request("GET", f"/users/{user_address}/open_orders", params=params)
        return response

    async def get_user_filled_orders(
        self, user_address: ChecksumAddress, market_address: ChecksumAddress,
        limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get filled orders for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market
            limit: Range 1-1000
            offset: Min value 0

        Returns:
            List of Orders
        """
        params = {"limit": limit, "offset": offset, "market_address": str(market_address)}
        response = await self._rest._request("GET", f"/users/{user_address}/filled_orders", params=params)
        return response

    async def get_user_order_history(
        self, user_address: ChecksumAddress, market_address: ChecksumAddress,
    ) -> list[dict[str, Any]]:
        """Get order history for a user.

        Args:
            user_address: EVM address of the user
            market_address: EVM address of the market

        Returns:
            List of Orders
        """
        params = {"market_address": str(market_address)}
        response = await self._rest._request("GET", f"/users/{user_address}/order_history", params=params)
        return response

    def get_perp_markets(self) -> dict[str, Any]:
        """Get perps markets.
        
        Returns:
            List of Markets
        """
        response = requests.get("https://perps-api.gte.xyz/v1/perps/markets")
        return response.json()
    
    def get_perp_book(self, market_id: str) -> dict[str, Any]:
        """Get perps book for a market.
        
        Args:
            market_id: Market ID
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/{market_id}/book")
        return response.json()
    
    def get_perp_open_orders(self, market_id: str, account_address: ChecksumAddress) -> dict[str, Any]:
        """Get perps open orders for a market.
        
        Args:
            market_id: Market ID
            account_address: Account address
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/orders/{account_address}/open_orders")
        return response.json()
    
    def get_perp_position(self, account_address: ChecksumAddress) -> dict[str, Any]:
        """Get perps position for a market.
        
        Args:
            market_id: Market ID (optional)
            account_address: Account address
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/orders/{account_address}/positions")
        return response.json()
    
    def get_perp_order_history(self, account_address: ChecksumAddress) -> dict[str, Any]:
        """Get perps order history for a market.
        
        Args:
            account_address: Account address
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/orders/{account_address}/order_history")
        return response.json()
    
    def get_perp_funding_history(self, account_address: ChecksumAddress) -> dict[str, Any]:
        """Get perps funding history for a market.
        
        Args:
            account_address: Account address
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/orders/{account_address}/funding_history")
        return response.json()
    
    def get_perp_trades(self, market_id: str) -> dict[str, Any]:
        """Get perps trades for a market.
        
        Args:
            market_id: Market ID
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/{market_id}/trades")
        return response.json()
    
    def get_perp_candles(self, market_id: str, from_time: int, to_time: int, interval: str) -> dict[str, Any]:
        """Get perps candles for a market.
        
        Args:
            market_id: Market ID
            from_time: From time
            to_time: To time
            interval: Interval
        """
        response = requests.get(f"https://perps-api.gte.xyz/v1/perps/{market_id}/candles?from={from_time}&to={to_time}&interval={interval}")
        return response.json()
        
    # ================= WEBSOCKET API METHODS =================

    async def subscribe_trades(self, market: ChecksumAddress, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to trades for a market.

        Args:
            market: Market address
            callback: Function to call when a trade is received
        """
        subscription_key = f"trades_{market}"
        await self._websocket.subscribe("trades.subscribe", {"market": market}, callback)
        self._subscriptions[subscription_key] = {
            "type": "trades",
            "market": market,
            "params": {"market": market}
        }

    async def unsubscribe_trades(self, market: ChecksumAddress):
        """Unsubscribe from trades for a market.

        Args:
            market: Market address
        """
        subscription_key = f"trades_{market}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("trades.unsubscribe", {"market": market})
            del self._subscriptions[subscription_key]

    async def subscribe_candles(self, market: ChecksumAddress, interval: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to candles for a market.

        Args:
            market: Market address
            interval: Candle interval (1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
            callback: Function to call when a candle is received
        """
        subscription_key = f"candles_{market}_{interval}"
        await self._websocket.subscribe(
            "candles.subscribe", {"market": market, "interval": interval}, callback
        )
        self._subscriptions[subscription_key] = {
            "type": "candles",
            "market": market,
            "interval": interval,
            "interval": interval,
            "params": {"market": market, "interval": interval}
        }

    async def unsubscribe_candles(self, market: ChecksumAddress, interval: str):
        """Unsubscribe from candles for a market.

        Args:
            market: Market address
            interval: Candle interval
        """
        subscription_key = f"candles_{market}_{interval}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("candles.unsubscribe", {"market": market, "interval": interval})
            del self._subscriptions[subscription_key]

    async def subscribe_orderbook(
            self, market: ChecksumAddress, callback: Callable[[dict[str, Any]], Any], limit: int = 10):
        """Subscribe to orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels to include (defaults to 10)
            callback: Function to call when an orderbook update is received
        """
        subscription_key = f"orderbook_{market}_{limit}"
        await self._websocket.subscribe('book.subscribe', {"market": market, "limit": limit}, callback)
        self._subscriptions[subscription_key] = {
            "type": "orderbook",
            "market": market,
            "limit": limit,
            "params": {"market": market, "limit": limit}
        }

    async def unsubscribe_orderbook(self, market: ChecksumAddress, limit: int = 10):
        """Unsubscribe from orderbook for a market.

        Args:
            market: Market address
            limit: Number of levels that was used for subscription
        """
        subscription_key = f"orderbook_{market}_{limit}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe('book.unsubscribe', {"market": market, "limit": limit})
            del self._subscriptions[subscription_key]

    # Subscription management methods
    def get_subscriptions(self) -> list[dict[str, Any]]:
        """
        Get list of active subscriptions.
        
        Returns:
            List of subscription details
        """
        return list(self._subscriptions.values())

    def get_subscription_count(self) -> int:
        """
        Get the number of active subscriptions.
        
        Returns:
            Number of active subscriptions
        """
        return len(self._subscriptions)

    def has_subscription(self, market: ChecksumAddress, subscription_type: str, **kwargs) -> bool:
        """
        Check if a specific subscription exists.
        
        Args:
            market: Market address
            subscription_type: Type of subscription ("trades", "candles", "orderbook")
            **kwargs: Additional parameters (interval for candles, limit for orderbook)
            
        Returns:
            True if subscription exists, False otherwise
        """
        if subscription_type == "trades":
            subscription_key = f"trades_{market}"
        elif subscription_type == "candles":
            interval = kwargs.get("interval")
            if not interval:
                return False
            subscription_key = f"candles_{market}_{interval}"
        elif subscription_type == "orderbook":
            limit = kwargs.get("limit", 10)
            subscription_key = f"orderbook_{market}_{limit}"
        else:
            return False
            
        return subscription_key in self._subscriptions

    async def unsubscribe_all(self) -> None:
        """
        Unsubscribe from all active subscriptions and clear the cache.
        """
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            try:
                if subscription_data["type"] == "trades":
                    await self.unsubscribe_trades(subscription_data["market"])
                elif subscription_data["type"] == "candles":
                    await self.unsubscribe_candles(subscription_data["market"], subscription_data["interval"])
                elif subscription_data["type"] == "orderbook":
                    await self.unsubscribe_orderbook(subscription_data["market"], subscription_data["limit"])
            except Exception as e:
                logger.error(f"Error unsubscribing from {subscription_key}: {e}")
        
        self._subscriptions.clear()

    async def unsubscribe_all_trades(self) -> None:
        """Unsubscribe from all trade subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "trades":
                await self.unsubscribe_trades(subscription_data["market"])

    async def unsubscribe_all_candles(self) -> None:
        """Unsubscribe from all candle subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "candles":
                await self.unsubscribe_candles(subscription_data["market"], subscription_data["interval"])

    async def unsubscribe_all_orderbooks(self) -> None:
        """Unsubscribe from all orderbook subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "orderbook":
                await self.unsubscribe_orderbook(subscription_data["market"], subscription_data["limit"])
