"""High-level GTE client."""

import logging
from datetime import datetime, timedelta
from typing import Any

from eth_typing import ChecksumAddress
from web3 import Web3

from .api.rest_api import RestApi
from .config import NetworkConfig
from .execution import ExecutionClient
from .info import MarketService
from .market import MarketClient
from .models import (
    Asset,
    Candle,
    Market,
    Order,
    OrderSide,
    OrderType,
    Position,
    TimeInForce,
    Trade,
)

logger = logging.getLogger(__name__)


class Client:
    """User-friendly client for interacting with GTE."""

    def __init__(
            self,
            # TODO: Do we favor async Web3?
            web3: Web3,
            config: NetworkConfig,
            sender_address: ChecksumAddress | None = None,
    ):
        """
        Initialize the client.

        Args:
            web3: Web3 instance
            config: Network configuration
            sender_address: Address to send transactions from (optional)
        """
        self._rest_client = RestApi(base_url=config.api_url)
        self._ws_url = config.ws_url
        self._market_clients: dict[str, MarketClient] = {}

        self._web3 = web3

        self._market_info = MarketService(web3=self._web3, router_address=config.router_address)
        if sender_address:
            # Initialize execution client for trading operations
            self._execution_client = ExecutionClient(
                web3=self._web3,
                router_address=config.router_address,
                sender_address=sender_address,
            )
        else:
            self._execution_client = None

    async def __aenter__(self):
        """Enter async context."""
        await self._rest_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self._rest_client.__aexit__(exc_type, exc_val, exc_tb)
        # Close any open market clients
        for client in self._market_clients.values():
            await client.close()

    async def close(self):
        """Close the client and release resources."""
        await self.__aexit__(None, None, None)

    # Asset methods
    async def get_assets(
            self, creator: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[Asset]:
        """
        Get list of assets.

        Args:
            creator: Filter by creator address
            limit: Maximum number of assets to return
            offset: Offset for pagination

        Returns:
            List of assets
        """
        response = await self._rest_client.get_assets(creator=creator, limit=limit, offset=offset)
        return [Asset.from_api(asset_data) for asset_data in response.get("assets", [])]

    async def get_asset(self, address: str) -> Asset:
        """
        Get asset by address.

        Args:
            address: Asset address

        Returns:
            Asset
        """
        response = await self._rest_client.get_asset(address)
        return Asset.from_api(response)

    # Market methods
    async def get_markets(
            self,
            limit: int = 100,
            offset: int = 0,
            market_type: str | None = None,
            asset_address: str | None = None,
            max_price: float | None = None,
    ) -> list[Market]:
        """
        Get list of markets.

        Args:
            limit: Maximum number of markets to return
            offset: Offset for pagination
            market_type: Filter by market type (amm, launchpad, clob)
            asset_address: Filter by base asset address
            max_price: Maximum price filter

        Returns:
            List of markets
        """
        response = await self._rest_client.get_markets(
            limit=limit,
            offset=offset,
            market_type=market_type,
            asset=asset_address,
            price=max_price,
        )

        markets = [Market.from_api(market_data) for market_data in response.get("markets", [])]

        # Update market info cache with discovered markets
        if self._market_info:
            self._market_info.update_market_cache(markets)

        return markets

    async def get_market(self, address: str) -> Market:
        """
        Get market by address.

        Args:
            address: Market address

        Returns:
            Market
        """
        response = await self._rest_client.get_market(address)
        return Market.from_api(response)

    async def get_market_client(self, market_address: ChecksumAddress) -> MarketClient:
        """
        Get a dedicated client for a specific market.

        Creates or reuses a WebSocket-based market client for real-time data.

        Args:
            market_address: Market address

        Returns:
            MarketClient instance
        """
        if market_address not in self._market_clients:
            # Get market details first to ensure it's valid
            market = await self.get_market(market_address)
            self._market_clients[market_address] = MarketClient(market=market, ws_url=self._ws_url)
            await self._market_clients[market_address].connect()

        return self._market_clients[market_address]

    # Historical data methods
    async def get_candles(
            self,
            market_address: ChecksumAddress,
            interval: str = "1h",
            start_time: int | datetime | None = None,
            end_time: int | datetime | None = None,
            limit: int = 500,
    ) -> list[Candle]:
        """
        Get historical candles for a market.

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
            limit=limit,
        )

        return [Candle.from_api(candle_data) for candle_data in response.get("candles", [])]

    async def get_recent_trades(
            self, market_address: ChecksumAddress, limit: int = 50
    ) -> list[Trade]:
        """
        Get recent trades for a market.

        Args:
            market_address: Market address
            limit: Maximum number of trades to return

        Returns:
            List of trades
        """
        response = await self._rest_client.get_trades(market_address=market_address, limit=limit)

        return [Trade.from_api(trade_data) for trade_data in response.get("trades", [])]

    # User-specific methods
    async def get_positions(self, user_address: ChecksumAddress) -> list[Position]:
        """
        Get LP positions for a user.

        Args:
            user_address: User address

        Returns:
            List of positions
        """
        response = await self._rest_client.get_user_positions(user_address)
        return [Position.from_api(pos_data) for pos_data in response.get("positions", [])]

    async def get_user_assets(
            self, user_address: ChecksumAddress, limit: int = 100
    ) -> list[Asset]:
        """
        Get assets held by a user.

        Args:
            user_address: User address
            limit: Maximum number of assets to return

        Returns:
            List of assets with balances
        """
        response = await self._rest_client.get_user_assets(user_address, limit=limit)
        return [
            Asset.from_api(asset_data, with_balance=True)
            for asset_data in response.get("assets", [])
        ]

    # Trading methods
    async def create_order(
            self,
            market_address: ChecksumAddress,
            side: OrderSide | str,
            order_type: OrderType | str,
            amount: float,
            price: float | None = None,
            time_in_force: TimeInForce | str = TimeInForce.GTC,
            sender_address: str | None = None,
            use_contract: bool = False,
            use_router: bool = True,
            **tx_kwargs,
    ) -> Order | dict[str, Any]:
        """
        Create a new order.

        Args:
            market_address: Market address
            side: Order side (buy, sell)
            order_type: Order type (limit, market)
            amount: Order amount
            price: Order price (required for limit orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            sender_address: Address to send transaction from (required for on-chain orders)
            use_contract: Whether to create the order on-chain using contracts
            use_router: Whether to use the router for creating orders (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Created order information or transaction data when using contracts

        Raises:
            ValueError: For missing required parameters or invalid input
        """
        # Convert string enums to proper enum types if needed
        if isinstance(side, str):
            side = OrderSide(side)

        if isinstance(order_type, str):
            order_type = OrderType(order_type)

        if isinstance(time_in_force, str):
            time_in_force = TimeInForce(time_in_force)

        # Try to get from market info service first
        market_info = None
        if self._market_info:
            market_info = self._market_info.get_market(market_address)

        # If not found in market info service, fetch from API
        if not market_info:
            # Get market details from API
            market = await self.get_market(market_address)

            # Update market info cache
            if self._market_info and market.address:
                self._market_info.add_market(market)
        else:
            # Use market_info directly
            market = market_info

        # Delegate to execution client
        return await self._execution_client.create_order(
            market=market,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            time_in_force=time_in_force,
            sender_address=sender_address,
            use_contract=use_contract,
            use_router=use_router,
            **tx_kwargs,
        )

    async def cancel_order(
            self,
            market_address: ChecksumAddress,
            order_id: int,
            sender_address: str,
            use_router: bool = True,
            **tx_kwargs,
    ) -> Order:
        """
        Cancel an order.

        Args:
            market_address: Market address
            order_id: ID of the order to cancel
            sender_address: Address to send transaction from
            use_router: Whether to use the router for canceling orders (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction data

        Raises:
            ValueError: If Web3 is not configured or parameters are invalid
        """
        # Get market details first
        market_info = None
        if self._market_info:
            market_info = self._market_info.get_market(market_address)

        if not market_info:
            market = await self.get_market(market_address)
        else:
            market = market_info

        # Delegate to execution client
        return self._execution_client.cancel_order(
            market=market,
            order_id=order_id,
            sender_address=sender_address,
            use_router=use_router,
            **tx_kwargs,
        )

    # async def modify_order(
    #     self,
    #     market_address: ChecksumAddress,
    #     order_id: int,
    #     new_amount: float,
    #     sender_address: str,
    #     **tx_kwargs,
    # ) -> dict[str, Any]:
    #     """
    #     Modify an existing order's amount (reduce only).
    #
    #     Args:
    #         market_address: Market address
    #         order_id: ID of the order to modify
    #         new_amount: New amount for the order (must be less than current)
    #         sender_address: Address to send transaction from
    #         **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)
    #
    #     Returns:
    #         Transaction data
    #
    #     Raises:
    #         ValueError: If Web3 is not configured or parameters are invalid
    #     """
    #     # Get market details first
    #     market_info = None
    #     if self._market_info:
    #         market_info = self._market_info.get_market_info(market_address)
    #
    #     if not market_info:
    #         market = await self.get_market(market_address)
    #     else:
    #         market = market_info
    #
    #     # Delegate to execution client
    #     return self._execution_client.modify_order(
    #         market=market,
    #         order_id=order_id,
    #         new_amount=new_amount,
    #         sender_address=sender_address,
    #         **tx_kwargs,
    #     )

    def get_available_onchain_markets(self) -> list[Market]:
        """
        Get available on-chain markets.

        Returns:
            List of market information from the blockchain

        Raises:
            ValueError: If Web3 or router not configured
        """
        if not self._market_info:
            raise ValueError(
                "Market info service not configured. "
                + "Initialize with web3_provider and router_address."
            )

        return self._market_info.get_available_markets()

    # User order and trade methods
    async def get_user_orders(
            self,
            user_address: ChecksumAddress,
            market_address: ChecksumAddress | None = None,
            status: str | None = None,
            limit: int = 100,
            offset: int = 0,
    ) -> list[Order]:
        """
        Fetch orders for a specific user.

        Args:
            user_address: Address of the user
            market_address: Optional market address to filter by
            status: Optional status to filter by (open, filled, cancelled)
            limit: Maximum number of orders to return
            offset: Offset for pagination

        Returns:
            List of user orders
        """
        return await self._execution_client.get_user_orders(
            user_address=user_address,
            market_address=market_address,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_user_trades(
            self,
            user_address: ChecksumAddress,
            market_address: ChecksumAddress | None = None,
            limit: int = 100,
            offset: int = 0,
    ) -> list[Trade]:
        """
        Fetch historical trades for a specific user.

        Args:
            user_address: Address of the user
            market_address: Optional market address to filter by
            limit: Maximum number of trades to return
            offset: Offset for pagination

        Returns:
            List of user trades
        """
        return await self._execution_client.get_user_trades(
            user_address=user_address, market_address=market_address, limit=limit, offset=offset
        )

    async def get_order_book_snapshot(
            self, market_address: ChecksumAddress, depth: int = 10
    ) -> dict[str, Any]:
        """
        Get current order book snapshot from the chain.

        Args:
            market_address: Market address
            depth: Number of price levels to fetch on each side

        Returns:
            Dictionary with bids and asks arrays
        """
        # Get market details first
        market_info = None
        if self._market_info:
            market_info = self._market_info.get_market(market_address)

        if not market_info:
            market = await self.get_market(market_address)
        else:
            market = market_info

        return await self._execution_client.get_order_book_snapshot(market=market, depth=depth)

    async def get_user_balances(
            self, user_address: ChecksumAddress, market_address: ChecksumAddress
    ) -> dict[str, int]:
        """
        Get user token balances in the CLOB.

        Args:
            user_address: Address of the user
            market_address: Market address

        Returns:
            Dictionary with base and quote token balances
        """
        # Get market details first
        market_info = None
        if self._market_info:
            market_info = self._market_info.get_market(market_address)

        if not market_info:
            market = await self.get_market(market_address)
        else:
            market = market_info

        return await self._execution_client.get_user_balances(
            user_address=user_address, market=market
        )
