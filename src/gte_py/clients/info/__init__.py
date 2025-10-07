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
        """Health check endpoint."""
        return await self._rest._request("GET", "/health")

    # ===== Portfolio =====
    async def get_user_balance(self, user: str | ChecksumAddress) -> dict[str, Any]:
        return await self._rest._request("GET", f"/portfolio/{user}/balance")

    async def get_user_pnl_history(self, user: str | ChecksumAddress, from_ts: int, to_ts: int | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"from": from_ts}
        if to_ts is not None:
            params["to"] = to_ts
        return await self._rest._request("GET", f"/portfolio/{user}/pnl_history", params=params)

    async def get_user_balance_history(self, user: str | ChecksumAddress, from_ts: int, to_ts: int | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"from": from_ts}
        if to_ts is not None:
            params["to"] = to_ts
        return await self._rest._request("GET", f"/portfolio/{user}/balance_history", params=params)

    async def get_user_lp_positions(self, user: str | ChecksumAddress) -> dict[str, Any]:
        return await self._rest._request("GET", f"/portfolio/{user}/lp_positions")

    # ===== Spot CLOB =====
    async def get_spot_clob_open_orders(self, user: str | ChecksumAddress, market_id: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if market_id is not None:
            params["marketId"] = market_id
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/spot_clob/open_orders/{user}", params=params)

    async def get_spot_clob_order_history(self, user: str | ChecksumAddress, market_id: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if market_id is not None:
            params["marketId"] = market_id
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/spot_clob/order_history/{user}", params=params)

    async def get_spot_clob_book(self, market_id: str, limit: int = 20) -> dict[str, Any]:
        params = {"limit": limit}
        return await self._rest._request("GET", f"/spot_clob/{market_id}/book", params=params)

    async def get_spot_clob_trades(self, market_id: str, cursor: str | None = None, user: str | ChecksumAddress | None = None, limit: int = 25) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        if user is not None:
            params["user"] = str(user)
        return await self._rest._request("GET", f"/spot_clob/{market_id}/trades", params=params)

    async def get_spot_clob_candles(self, market_id: str, from_ts: int, interval: str, to_ts: int | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"from": from_ts, "interval": interval, "limit": limit}
        if to_ts is not None:
            params["to"] = to_ts
        return await self._rest._request("GET", f"/spot_clob/{market_id}/candles", params=params)

    # ===== Perps =====
    async def get_perp_markets(self) -> dict[str, Any]:
        return await self._rest._request("GET", "/perp/markets")

    async def get_perp_market_by_id(self, market_id: str) -> dict[str, Any]:
        return await self._rest._request("GET", f"/perp/markets/{market_id}")

    async def get_perp_positions(self, user: str | ChecksumAddress, market_id: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if market_id is not None:
            params["marketId"] = market_id
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/perp/positions/{user}", params=params)

    async def get_perp_open_orders(self, user: str | ChecksumAddress, market_id: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if market_id is not None:
            params["marketId"] = market_id
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/perp/open_orders/{user}", params=params)

    async def get_perp_order_history(self, user: str | ChecksumAddress, market_id: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if market_id is not None:
            params["marketId"] = market_id
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/perp/order_history/{user}", params=params)

    async def get_perp_funding_history(self, user: str | ChecksumAddress, market_id: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if market_id is not None:
            params["marketId"] = market_id
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/perp/funding_history/{user}", params=params)

    async def get_perp_book(self, market_id: str, limit: int = 20) -> dict[str, Any]:
        params = {"limit": limit}
        return await self._rest._request("GET", f"/perp/{market_id}/book", params=params)

    async def get_perp_trades(self, market_id: str, user: str | ChecksumAddress | None = None, cursor: str | None = None, limit: int = 25) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if user is not None:
            params["user"] = str(user)
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", f"/perp/{market_id}/trades", params=params)

    async def get_perp_candles(self, market_id: str, from_ts: int, interval: str, to_ts: int | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"from": from_ts, "interval": interval, "limit": limit}
        if to_ts is not None:
            params["to"] = to_ts
        return await self._rest._request("GET", f"/perp/{market_id}/candles", params=params)

    # ===== Tokens =====
    async def get_tokens(self, creator: str | None = None, market_type: str | None = None, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if creator is not None:
            params["creator"] = creator
        if market_type is not None:
            params["marketType"] = market_type
        if cursor is not None:
            params["cursor"] = cursor
        return await self._rest._request("GET", "/tokens", params=params)

    async def get_token_by_id(self, token_id: str) -> dict[str, Any]:
        return await self._rest._request("GET", f"/tokens/{token_id}")

    async def search_tokens(self, query: str, market_type: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"query": query}
        if market_type is not None:
            params["marketType"] = market_type
        return await self._rest._request("GET", "/tokens/search", params=params)

    # ===== Markets =====
    async def get_markets(self, cursor: str | None = None, limit: int = 100, market_type: str | None = None, sort_by: str = "marketCap", token_id: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "sortBy": sort_by}
        if cursor is not None:
            params["cursor"] = cursor
        if market_type is not None:
            params["marketType"] = market_type
        if token_id is not None:
            params["tokenId"] = token_id
        return await self._rest._request("GET", "/markets", params=params)

    async def get_market_by_id(self, market_id: str) -> dict[str, Any]:
        return await self._rest._request("GET", f"/markets/{market_id}")

    async def search_markets(self, query: str, market_type: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"query": query}
        if market_type is not None:
            params["marketType"] = market_type
        return await self._rest._request("GET", "/markets/search", params=params)

    async def get_dash_markets(self, dash_type: str, limit: int = 100) -> dict[str, Any]:
        params = {"limit": limit, "dashType": dash_type}
        return await self._rest._request("GET", "/markets/dash", params=params)

    async def get_market_candles(self, market_id: str, from_ts: int, interval: str, to_ts: int | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"from": from_ts, "interval": interval, "limit": limit}
        if to_ts is not None:
            params["to"] = to_ts
        return await self._rest._request("GET", f"/markets/{market_id}/candles", params=params)

    async def get_market_trades(self, market_id: str, cursor: str | None = None, user: str | ChecksumAddress | None = None, limit: int = 25) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        if user is not None:
            params["user"] = str(user)
        return await self._rest._request("GET", f"/markets/{market_id}/trades", params=params)
        
    # ================= WEBSOCKET API METHODS =================

    # ===== Perps =====
    async def subscribe_perp_trades(self, market_id: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to perp trades for a market.

        Args:
            market_id: Market ID (e.g., "BTC-USDC")
            callback: Function to call when a trade is received
        """
        subscription_key = f"perp_trades_{market_id}"
        await self._websocket.subscribe("perp_trades", {"marketId": market_id}, callback)
        self._subscriptions[subscription_key] = {
            "type": "perp_trades",
            "market_id": market_id,
            "params": {"marketId": market_id}
        }

    async def unsubscribe_perp_trades(self, market_id: str):
        """Unsubscribe from perp trades for a market.

        Args:
            market_id: Market ID
        """
        subscription_key = f"perp_trades_{market_id}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("perp_trades", {"marketId": market_id})
            del self._subscriptions[subscription_key]

    async def subscribe_perp_book(self, market_id: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to perp L2 orderbook for a market.

        Args:
            market_id: Market ID (e.g., "BTC-USDC")
            callback: Function to call when an orderbook update is received
        """
        subscription_key = f"perp_book_{market_id}"
        await self._websocket.subscribe("perp_book", {"marketId": market_id}, callback)
        self._subscriptions[subscription_key] = {
            "type": "perp_book",
            "market_id": market_id,
            "params": {"marketId": market_id}
        }

    async def unsubscribe_perp_book(self, market_id: str):
        """Unsubscribe from perp orderbook for a market.

        Args:
            market_id: Market ID
        """
        subscription_key = f"perp_book_{market_id}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("perp_book", {"marketId": market_id})
            del self._subscriptions[subscription_key]

    async def subscribe_perp_candles(self, market_id: str, interval: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to perp candles for a market.

        Args:
            market_id: Market ID (e.g., "BTC-USDC")
            interval: Candle interval (1s, 15s, 30s, 1m, 2m, 3m, 5m, 10m, 15m, 20m, 30m, 1h, 4h, 1d, 1w)
            callback: Function to call when a candle is received
        """
        subscription_key = f"perp_candles_{market_id}_{interval}"
        await self._websocket.subscribe("perp_candles", {"marketId": market_id, "interval": interval}, callback)
        self._subscriptions[subscription_key] = {
            "type": "perp_candles",
            "market_id": market_id,
            "interval": interval,
            "params": {"marketId": market_id, "interval": interval}
        }

    async def unsubscribe_perp_candles(self, market_id: str, interval: str):
        """Unsubscribe from perp candles for a market.
        
        Args:
            market_id: Market ID
            interval: Candle interval
        """
        subscription_key = f"perp_candles_{market_id}_{interval}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("perp_candles", {"marketId": market_id, "interval": interval})
            del self._subscriptions[subscription_key]

    async def subscribe_perp_positions(self, user: str | ChecksumAddress, market_id: str | None = None, callback: Callable[[dict[str, Any]], Any] | None = None):
        """Subscribe to perp positions for a user.

        Args:
            user: User address
            market_id: Optional market ID to filter by
            callback: Function to call when position updates are received
        """
        subscription_key = f"perp_positions_{user}_{market_id or 'all'}"
        params = {"user": str(user)}
        if market_id:
            params["marketId"] = market_id
        if callback:
            await self._websocket.subscribe("perp_positions", params, callback)
        self._subscriptions[subscription_key] = {
            "type": "perp_positions",
            "user": str(user),
            "market_id": market_id,
            "params": params
        }

    async def unsubscribe_perp_positions(self, user: str | ChecksumAddress, market_id: str | None = None):
        """Unsubscribe from perp positions for a user.
        
        Args:
            user: User address
            market_id: Optional market ID that was used for subscription
        """
        subscription_key = f"perp_positions_{user}_{market_id or 'all'}"
        if subscription_key in self._subscriptions:
            params = {"user": str(user)}
            if market_id:
                params["marketId"] = market_id
            await self._websocket.unsubscribe("perp_positions", params)
            del self._subscriptions[subscription_key]

    async def subscribe_perp_open_orders(self, user: str | ChecksumAddress, market_id: str | None = None, callback: Callable[[dict[str, Any]], Any] | None = None):
        """Subscribe to perp open orders for a user.

        Args:
            user: User address
            market_id: Optional market ID to filter by
            callback: Function to call when order updates are received
        """
        subscription_key = f"perp_open_orders_{user}_{market_id or 'all'}"
        params = {"user": str(user)}
        if market_id:
            params["marketId"] = market_id
        if callback:
            await self._websocket.subscribe("perp_open_orders", params, callback)
        self._subscriptions[subscription_key] = {
            "type": "perp_open_orders",
            "user": str(user),
            "market_id": market_id,
            "params": params
        }

    async def unsubscribe_perp_open_orders(self, user: str | ChecksumAddress, market_id: str | None = None):
        """Unsubscribe from perp open orders for a user.
        
        Args:
            user: User address
            market_id: Optional market ID that was used for subscription
        """
        subscription_key = f"perp_open_orders_{user}_{market_id or 'all'}"
        if subscription_key in self._subscriptions:
            params = {"user": str(user)}
            if market_id:
                params["marketId"] = market_id
            await self._websocket.unsubscribe("perp_open_orders", params)
            del self._subscriptions[subscription_key]

    # ===== Spot CLOB =====
    async def subscribe_spotclob_trades(self, market_id: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to spot CLOB trades for a market.
        
        Args:
            market_id: Market ID (e.g., "0x123...")
            callback: Function to call when a trade is received
        """
        subscription_key = f"spotclob_trades_{market_id}"
        await self._websocket.subscribe("spotclob_trades", {"marketId": market_id}, callback)
        self._subscriptions[subscription_key] = {
            "type": "spotclob_trades",
            "market_id": market_id,
            "params": {"marketId": market_id}
        }

    async def unsubscribe_spotclob_trades(self, market_id: str):
        """Unsubscribe from spot CLOB trades for a market.
        
        Args:
            market_id: Market ID
        """
        subscription_key = f"spotclob_trades_{market_id}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("spotclob_trades", {"marketId": market_id})
            del self._subscriptions[subscription_key]

    async def subscribe_spotclob_book(self, market_id: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to spot CLOB L2 orderbook for a market.

        Args:
            market_id: Market ID (e.g., "0x123...")
            callback: Function to call when an orderbook update is received
        """
        subscription_key = f"spotclob_book_{market_id}"
        await self._websocket.subscribe("spotclob_book", {"marketId": market_id}, callback)
        self._subscriptions[subscription_key] = {
            "type": "spotclob_book",
            "market_id": market_id,
            "params": {"marketId": market_id}
        }

    async def unsubscribe_spotclob_book(self, market_id: str):
        """Unsubscribe from spot CLOB orderbook for a market.

        Args:
            market_id: Market ID
        """
        subscription_key = f"spotclob_book_{market_id}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("spotclob_book", {"marketId": market_id})
            del self._subscriptions[subscription_key]

    async def subscribe_spotclob_candles(self, market_id: str, interval: str, callback: Callable[[dict[str, Any]], Any]):
        """Subscribe to spot CLOB candles for a market.

        Args:
            market_id: Market ID (e.g., "0x123...")
            interval: Candle interval (1s, 15s, 30s, 1m, 2m, 3m, 5m, 10m, 15m, 20m, 30m, 1h, 4h, 1d, 1w)
            callback: Function to call when a candle is received
        """
        subscription_key = f"spotclob_candles_{market_id}_{interval}"
        await self._websocket.subscribe("spotclob_candles", {"marketId": market_id, "interval": interval}, callback)
        self._subscriptions[subscription_key] = {
            "type": "spotclob_candles",
            "market_id": market_id,
            "interval": interval,
            "params": {"marketId": market_id, "interval": interval}
        }

    async def unsubscribe_spotclob_candles(self, market_id: str, interval: str):
        """Unsubscribe from spot CLOB candles for a market.

        Args:
            market_id: Market ID
            interval: Candle interval
        """
        subscription_key = f"spotclob_candles_{market_id}_{interval}"
        if subscription_key in self._subscriptions:
            await self._websocket.unsubscribe("spotclob_candles", {"marketId": market_id, "interval": interval})
            del self._subscriptions[subscription_key]

    async def subscribe_spotclob_open_orders(self, user: str | ChecksumAddress, market_id: str | None = None, callback: Callable[[dict[str, Any]], Any] | None = None):
        """Subscribe to spot CLOB open orders for a user.

        Args:
            user: User address
            market_id: Optional market ID to filter by
            callback: Function to call when order updates are received
        """
        subscription_key = f"spotclob_open_orders_{user}_{market_id or 'all'}"
        params = {"user": str(user)}
        if market_id:
            params["marketId"] = market_id
        if callback:
            await self._websocket.subscribe("spotclob_open_orders", params, callback)
        self._subscriptions[subscription_key] = {
            "type": "spotclob_open_orders",
            "user": str(user),
            "market_id": market_id,
            "params": params
        }

    async def unsubscribe_spotclob_open_orders(self, user: str | ChecksumAddress, market_id: str | None = None):
        """Unsubscribe from spot CLOB open orders for a user.

        Args:
            user: User address
            market_id: Optional market ID that was used for subscription
        """
        subscription_key = f"spotclob_open_orders_{user}_{market_id or 'all'}"
        if subscription_key in self._subscriptions:
            params = {"user": str(user)}
            if market_id:
                params["marketId"] = market_id
            await self._websocket.unsubscribe("spotclob_open_orders", params)
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

    def has_subscription(self, subscription_type: str, **kwargs) -> bool:
        """
        Check if a specific subscription exists.
        
        Args:
            subscription_type: Type of subscription (e.g., "perp_trades", "spotclob_book", etc.)
            **kwargs: Additional parameters (market_id, user, interval, etc.)
            
        Returns:
            True if subscription exists, False otherwise
        """
        if subscription_type.startswith("perp_"):
            market_id = kwargs.get("market_id")
            user = kwargs.get("user")
            interval = kwargs.get("interval")
            
            if subscription_type == "perp_trades":
                if not market_id:
                    return False
                subscription_key = f"perp_trades_{market_id}"
            elif subscription_type == "perp_book":
                if not market_id:
                    return False
                subscription_key = f"perp_book_{market_id}"
            elif subscription_type == "perp_candles":
                if not market_id or not interval:
                    return False
                subscription_key = f"perp_candles_{market_id}_{interval}"
            elif subscription_type == "perp_positions":
                if not user:
                    return False
                subscription_key = f"perp_positions_{user}_{market_id or 'all'}"
            elif subscription_type == "perp_open_orders":
                if not user:
                    return False
                subscription_key = f"perp_open_orders_{user}_{market_id or 'all'}"
            else:
                return False
                
        elif subscription_type.startswith("spotclob_"):
            market_id = kwargs.get("market_id")
            user = kwargs.get("user")
            interval = kwargs.get("interval")
            
            if subscription_type == "spotclob_trades":
                if not market_id:
                    return False
                subscription_key = f"spotclob_trades_{market_id}"
            elif subscription_type == "spotclob_book":
                if not market_id:
                    return False
                subscription_key = f"spotclob_book_{market_id}"
            elif subscription_type == "spotclob_candles":
                if not market_id or not interval:
                    return False
                subscription_key = f"spotclob_candles_{market_id}_{interval}"
            elif subscription_type == "spotclob_open_orders":
                if not user:
                    return False
                subscription_key = f"spotclob_open_orders_{user}_{market_id or 'all'}"
            else:
                return False
        else:
            return False
            
        return subscription_key in self._subscriptions

    async def unsubscribe_all(self) -> None:
        """
        Unsubscribe from all active subscriptions and clear the cache.
        """
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            try:
                sub_type = subscription_data["type"]
                
                if sub_type == "perp_trades":
                    await self.unsubscribe_perp_trades(subscription_data["market_id"])
                elif sub_type == "perp_book":
                    await self.unsubscribe_perp_book(subscription_data["market_id"])
                elif sub_type == "perp_candles":
                    await self.unsubscribe_perp_candles(subscription_data["market_id"], subscription_data["interval"])
                elif sub_type == "perp_positions":
                    await self.unsubscribe_perp_positions(subscription_data["user"], subscription_data.get("market_id"))
                elif sub_type == "perp_open_orders":
                    await self.unsubscribe_perp_open_orders(subscription_data["user"], subscription_data.get("market_id"))
                elif sub_type == "spotclob_trades":
                    await self.unsubscribe_spotclob_trades(subscription_data["market_id"])
                elif sub_type == "spotclob_book":
                    await self.unsubscribe_spotclob_book(subscription_data["market_id"])
                elif sub_type == "spotclob_candles":
                    await self.unsubscribe_spotclob_candles(subscription_data["market_id"], subscription_data["interval"])
                elif sub_type == "spotclob_open_orders":
                    await self.unsubscribe_spotclob_open_orders(subscription_data["user"], subscription_data.get("market_id"))
            except Exception as e:
                logger.error(f"Error unsubscribing from {subscription_key}: {e}")
        
        self._subscriptions.clear()

    async def unsubscribe_all_perp_trades(self) -> None:
        """Unsubscribe from all perp trade subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "perp_trades":
                await self.unsubscribe_perp_trades(subscription_data["market_id"])

    async def unsubscribe_all_perp_candles(self) -> None:
        """Unsubscribe from all perp candle subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "perp_candles":
                await self.unsubscribe_perp_candles(subscription_data["market_id"], subscription_data["interval"])

    async def unsubscribe_all_perp_books(self) -> None:
        """Unsubscribe from all perp orderbook subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "perp_book":
                await self.unsubscribe_perp_book(subscription_data["market_id"])

    async def unsubscribe_all_spotclob_trades(self) -> None:
        """Unsubscribe from all spot CLOB trade subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "spotclob_trades":
                await self.unsubscribe_spotclob_trades(subscription_data["market_id"])

    async def unsubscribe_all_spotclob_candles(self) -> None:
        """Unsubscribe from all spot CLOB candle subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "spotclob_candles":
                await self.unsubscribe_spotclob_candles(subscription_data["market_id"], subscription_data["interval"])

    async def unsubscribe_all_spotclob_books(self) -> None:
        """Unsubscribe from all spot CLOB orderbook subscriptions."""
        for subscription_key, subscription_data in list(self._subscriptions.items()):
            if subscription_data["type"] == "spotclob_book":
                await self.unsubscribe_spotclob_book(subscription_data["market_id"])
