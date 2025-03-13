"""High-level GTE client."""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import time

from .raw import GTERestClient
from .market import GteMarketClient
from .models import Asset, Market, Position, Trade, Candle, Order

logger = logging.getLogger(__name__)


class GteClient:
    """User-friendly client for interacting with GTE."""

    def __init__(self, api_url: str = "https://api.gte.io", ws_url: str = "wss://ws.gte.io/v1"):
        """Initialize the client.

        Args:
            api_url: Base URL for the REST API
            ws_url: URL for the WebSocket API
        """
        self._rest_client = GTERestClient(base_url=api_url)
        self._ws_url = ws_url
        self._market_clients = {}  # Cache for market clients

    async def __aenter__(self):
        """Enter async context."""
        await self._rest_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit async context."""
        await self._rest_client.__aexit__(exc_type, exc_value, traceback)
        # Close any open market clients
        for client in self._market_clients.values():
            await client.close()

    async def close(self):
        """Close the client and release resources."""
        await self.__aexit__(None, None, None)

    # Asset methods
    async def get_assets(self, creator: Optional[str] = None, 
                         limit: int = 100, offset: int = 0) -> List[Asset]:
        """Get list of assets.

        Args:
            creator: Filter by creator address
            limit: Maximum number of assets to return
            offset: Offset for pagination

        Returns:
            List of assets
        """
        response = await self._rest_client.get_assets(creator=creator, limit=limit, offset=offset)
        return [Asset.from_api(asset_data) for asset_data in response.get('assets', [])]

    async def get_asset(self, address: str) -> Asset:
        """Get asset by address.

        Args:
            address: Asset address

        Returns:
            Asset
        """
        response = await self._rest_client.get_asset(address)
        return Asset.from_api(response)

    # Market methods
    async def get_markets(self, limit: int = 100, offset: int = 0,
                          market_type: Optional[str] = None,
                          asset_address: Optional[str] = None,
                          max_price: Optional[float] = None) -> List[Market]:
        """Get list of markets.

        Args:
            limit: Maximum number of markets to return
            offset: Offset for pagination
            market_type: Filter by market type (amm, launchpad)
            asset_address: Filter by base asset address
            max_price: Maximum price filter

        Returns:
            List of markets
        """
        response = await self._rest_client.get_markets(
            limit=limit, offset=offset, market_type=market_type, 
            asset=asset_address, price=max_price
        )
        return [Market.from_api(market_data) for market_data in response.get('markets', [])]

    async def get_market(self, address: str) -> Market:
        """Get market by address.

        Args:
            address: Market address

        Returns:
            Market
        """
        response = await self._rest_client.get_market(address)
        return Market.from_api(response)

    async def get_market_client(self, market_address: str) -> "GteMarketClient":
        """Get a dedicated client for a specific market.

        Creates or reuses a WebSocket-based market client for real-time data.

        Args:
            market_address: Market address

        Returns:
            GteMarketClient instance
        """
        if (market_address not in self._market_clients):
            # Get market details first to ensure it's valid
            market = await self.get_market(market_address)
            self._market_clients[market_address] = GteMarketClient(
                market=market,
                ws_url=self._ws_url
            )
            await self._market_clients[market_address].connect()
        
        return self._market_clients[market_address]

    # Historical data methods
    async def get_candles(self, market_address: str, interval: str = "1h",
                          start_time: Optional[Union[int, datetime]] = None,
                          end_time: Optional[Union[int, datetime]] = None,
                          limit: int = 500) -> List[Candle]:
        """Get historical candles for a market.

        Args:
            market_address: Market address
            interval: Candlestick interval (1s, 30s, 1m, 3m, etc.)
            start_time: Start time (timestamp in ms or datetime)
            end_time: End time (timestamp in ms or datetime)
            limit: Maximum number of candles to return

        Returns:
            List of candles
        """
        # Default to last 24 hours if no start time provided
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        
        # Convert datetime to timestamp if needed
        if isinstance(start_time, datetime):
            start_time = int(start_time.timestamp() * 1000)
        
        if end_time is not None and isinstance(end_time, datetime):
            end_time = int(end_time.timestamp() * 1000)
        
        response = await self._rest_client.get_candles(
            market_address=market_address,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return [Candle.from_api(candle_data) for candle_data in response.get('candles', [])]

    async def get_recent_trades(self, market_address: str, limit: int = 50) -> List[Trade]:
        """Get recent trades for a market.

        Args:
            market_address: Market address
            limit: Maximum number of trades to return

        Returns:
            List of trades
        """
        response = await self._rest_client.get_trades(
            market_address=market_address,
            limit=limit
        )
        
        return [Trade.from_api(trade_data) for trade_data in response.get('trades', [])]

    # User-specific methods
    async def get_positions(self, user_address: str) -> List[Position]:
        """Get LP positions for a user.

        Args:
            user_address: User address

        Returns:
            List of positions
        """
        response = await self._rest_client.get_user_positions(user_address)
        return [Position.from_api(pos_data) for pos_data in response.get('positions', [])]

    async def get_user_assets(self, user_address: str, limit: int = 100) -> List[Asset]:
        """Get assets held by a user.

        Args:
            user_address: User address
            limit: Maximum number of assets to return

        Returns:
            List of assets with balances
        """
        response = await self._rest_client.get_user_assets(user_address, limit=limit)
        return [Asset.from_api(asset_data, with_balance=True) 
                for asset_data in response.get('assets', [])]

    # Trading methods - Note: These are placeholders as the API doesn't specify trading endpoints
    # In a real implementation, these would call the appropriate REST endpoints
    async def create_order(self, market_address: str, side: str, order_type: str, 
                          amount: float, price: Optional[float] = None, 
                          time_in_force: str = "GTC") -> Order:
        """Create a new order.

        Args:
            market_address: Market address
            side: Order side (buy, sell)
            order_type: Order type (limit, market)
            amount: Order amount
            price: Order price (required for limit orders)
            time_in_force: Time in force (GTC, IOC, FOK)

        Returns:
            Created order
        """
        # This would normally call a REST endpoint
        # For now, we'll just create a placeholder Order object
        logger.info(f"Creating {order_type} {side} order for {amount} at price {price}")
        
        # In a real implementation, we would call the API and get order details
        order_data = {
            "id": f"placeholder-{int(time.time())}",
            "marketAddress": market_address,
            "side": side,
            "type": order_type,
            "amount": amount,
            "price": price,
            "timeInForce": time_in_force,
            "status": "open",
            "filledAmount": 0.0,
            "filledPrice": 0.0,
            "createdAt": int(time.time() * 1000),
        }
        
        return Order.from_api(order_data)
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order.

        Args:
            order_id: Order ID

        Returns:
            True if cancelled successfully
        """
        # This would normally call a REST endpoint
        logger.info(f"Cancelling order {order_id}")
        return True
    
    async def get_orders(self, market_address: Optional[str] = None, 
                        status: Optional[str] = None) -> List[Order]:
        """Get orders for the authenticated user.

        Args:
            market_address: Filter by market address
            status: Filter by status (open, closed, cancelled)

        Returns:
            List of orders
        """
        # This would normally call a REST endpoint
        logger.info(f"Getting orders for market {market_address} with status {status}")
        return []
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order or None if not found
        """
        # This would normally call a REST endpoint
        logger.info(f"Getting order {order_id}")
        return None
    
    # Helper methods for common trading operations
    async def buy_limit(self, market_address: str, amount: float, price: float) -> Order:
        """Create a limit buy order.

        Args:
            market_address: Market address
            amount: Amount to buy
            price: Limit price

        Returns:
            Created order
        """
        return await self.create_order(
            market_address=market_address,
            side="buy",
            order_type="limit",
            amount=amount,
            price=price
        )
    
    async def sell_limit(self, market_address: str, amount: float, price: float) -> Order:
        """Create a limit sell order.

        Args:
            market_address: Market address
            amount: Amount to sell
            price: Limit price

        Returns:
            Created order
        """
        return await self.create_order(
            market_address=market_address,
            side="sell",
            order_type="limit",
            amount=amount,
            price=price
        )
    
    async def buy_market(self, market_address: str, amount: float) -> Order:
        """Create a market buy order.

        Args:
            market_address: Market address
            amount: Amount to buy

        Returns:
            Created order
        """
        return await self.create_order(
            market_address=market_address,
            side="buy",
            order_type="market",
            amount=amount
        )
    
    async def sell_market(self, market_address: str, amount: float) -> Order:
        """Create a market sell order.

        Args:
            market_address: Market address
            amount: Amount to sell

        Returns:
            Created order
        """
        return await self.create_order(
            market_address=market_address,
            side="sell",
            order_type="market",
            amount=amount
        )
    
    # Liquidity pool methods (these would connect to AMM functions)
    async def add_liquidity(self, market_address: str, 
                           token0_amount: float, 
                           token1_amount: float) -> Dict:
        """Add liquidity to a market.

        Args:
            market_address: Market address
            token0_amount: Amount of first token
            token1_amount: Amount of second token

        Returns:
            Transaction details
        """
        # This would normally call a REST endpoint to submit a transaction
        logger.info(f"Adding liquidity: {token0_amount}/{token1_amount} to market {market_address}")
        return {
            "success": True,
            "txHash": f"0x{'0'*64}",
            "marketAddress": market_address,
            "token0Amount": token0_amount,
            "token1Amount": token1_amount
        }
    
    async def remove_liquidity(self, market_address: str, percentage: float = 100.0) -> Dict:
        """Remove liquidity from a market.

        Args:
            market_address: Market address
            percentage: Percentage of liquidity to remove (1-100)

        Returns:
            Transaction details
        """
        # This would normally call a REST endpoint to submit a transaction
        logger.info(f"Removing {percentage}% liquidity from market {market_address}")
        return {
            "success": True,
            "txHash": f"0x{'0'*64}",
            "marketAddress": market_address,
            "percentage": percentage
        }
