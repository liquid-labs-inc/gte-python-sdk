"""High-level GTE client."""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional, Callable, Tuple, Dict, Union

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
from .contracts.utils import TypedContractFunction

logger = logging.getLogger(__name__)


class Client:
    """User-friendly client for interacting with GTE."""

    def __init__(
            self,
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

        # Initialize market service for fetching market information
        self._market_info = MarketService(web3=self._web3, router_address=config.router_address)

        if not sender_address:
            self._execution_client = None
        else:
            # Initialize execution client for trading operations
            self._execution_client = ExecutionClient(
                web3=self._web3,
                sender_address=sender_address,
                factory_address=config.clob_manager_address,
            )

        self._sender_address = sender_address

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

        return markets

    def get_market(self, address: ChecksumAddress) -> Market:
        """
        Get market by address.

        Args:
            address: Market address

        Returns:
            Market
        """
        return self._market_info.get_market_info_by_address(address)

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
    async def get_order(self, market: Market, order_id: int) -> Order | None:
        """
        Get order details by ID.

        Args:
            market: Market where the order was placed
            order_id: Order ID

        Returns:
            Order object or None if not found
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.get_order(market=market, order_id=order_id)

    async def place_limit_order(
            self,
            market: Market,
            side: OrderSide,
            amount: float,
            price: float,
            time_in_force: TimeInForce = TimeInForce.GTC,
            client_order_id: int = 0,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Place a limit order on the market.

        Args:
            market: Market to place order on
            side: Order side (buy, sell)
            amount: Order amount in base tokens
            price: Order price
            time_in_force: Time in force (GTC, IOC, FOK)
            client_order_id: Optional client-side order ID
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized or parameters are invalid
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.place_limit_order(
            market=market,
            side=side,
            amount=amount,
            price_in_quote=price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            **kwargs,
        )

    async def place_market_order(
            self,
            market: Market,
            side: OrderSide,
            amount: float,
            amount_is_base: bool = True,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Place a market order on the market.

        Args:
            market: Market to place order on
            side: Order side (buy, sell)
            amount: Order amount in base tokens (if amount_is_base=True) or quote tokens
            amount_is_base: Whether the amount is in base tokens
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.place_market_order(
            market=market,
            side=side,
            amount=amount,
            amount_is_base=amount_is_base,
            **kwargs,
        )

    async def cancel_order(
            self,
            market: Market,
            order_id: int,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Cancel an order.

        Args:
            market: Market where the order was placed
            order_id: ID of the order to cancel
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.cancel_order(
            market=market,
            order_id=order_id,
            **kwargs,
        )

    async def cancel_all_orders(
            self,
            market: Market,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Cancel all open orders on a market.

        Args:
            market: Market where the orders were placed
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.cancel_all_orders(
            market=market,
            **kwargs,
        )

    async def amend_order(
            self,
            market: Market,
            order_id: int,
            new_amount: Optional[float] = None,
            new_price: Optional[float] = None,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Amend an existing order.

        Args:
            market: Market where the order was placed
            order_id: ID of the order to amend
            new_amount: New amount for the order (None to keep current)
            new_price: New price for the order (None to keep current)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.amend_order(
            market=market,
            order_id=order_id,
            new_amount=new_amount,
            new_price=new_price,
            **kwargs,
        )

    async def deposit_to_market(
            self,
            token_address: ChecksumAddress,
            amount: float,
            **kwargs,
    ) -> List[TypedContractFunction]:
        """
        Deposit tokens to the exchange for trading.

        Args:
            token_address: Address of token to deposit
            amount: Amount to deposit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            List of TypedContractFunction objects (approve and deposit)

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.deposit_to_market(
            token_address=token_address,
            amount=amount,
            **kwargs,
        )

    async def withdraw_from_market(
            self,
            token_address: ChecksumAddress,
            amount: float,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Withdraw tokens from the exchange.

        Args:
            token_address: Address of token to withdraw
            amount: Amount to withdraw
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction for the withdraw transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.withdraw_from_market(
            token_address=token_address,
            amount=amount,
            **kwargs,
        )

    async def get_balance(
            self,
            token_address: ChecksumAddress,
            account: Optional[ChecksumAddress] = None,
    ) -> Tuple[float, float]:
        """
        Get token balance for an account both on-chain and in the exchange.

        Args:
            token_address: Address of token to check
            account: Account to check (defaults to sender address)

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.get_balance(
            token_address=token_address,
            account=account or self._sender_address,
        )

    async def wrap_eth(
            self,
            weth_address: ChecksumAddress,
            amount_eth: float,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Wrap ETH to get WETH.

        Args:
            weth_address: Address of the WETH contract
            amount_eth: Amount of ETH to wrap (as a float, e.g., 1.5 ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.wrap_eth(
            weth_address=weth_address,
            amount_eth=amount_eth,
            **kwargs,
        )

    async def unwrap_eth(
            self,
            weth_address: ChecksumAddress,
            amount_eth: float,
            **kwargs,
    ) -> TypedContractFunction:
        """
        Unwrap WETH to get ETH.

        Args:
            weth_address: Address of the WETH contract
            amount_eth: Amount of WETH to unwrap (as a float, e.g., 1.5 ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.unwrap_eth(
            weth_address=weth_address,
            amount_eth=amount_eth,
            **kwargs,
        )

    # Streaming methods
    async def stream_user_orders(
            self,
            user_address: Optional[ChecksumAddress] = None,
            market_address: Optional[ChecksumAddress] = None,
            callback: Callable[[Order, str], None] = None,
    ) -> str:
        """
        Stream order updates for a specific user.

        Args:
            user_address: Address of the user (defaults to sender address)
            market_address: Optional market address to filter by
            callback: Function to call with each order update and event type

        Returns:
            Subscription ID that can be used to unsubscribe

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.stream_user_orders(
            user_address=user_address or self._sender_address,
            market_address=market_address,
            callback=callback,
        )

    async def stream_market_trades(
            self,
            market: Market,
            callback: Callable[[Trade], None],
    ) -> str:
        """
        Stream trades for a specific market.

        Args:
            market: Market to get trades for
            callback: Function to call with each trade

        Returns:
            Subscription ID that can be used to unsubscribe

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.stream_market_trades(
            market_address=market.address,
            callback=callback,
        )

    async def stream_user_trades(
            self,
            user_address: Optional[ChecksumAddress] = None,
            market: Optional[Market] = None,
            callback: Callable[[Trade], None] = None,
    ) -> str:
        """
        Stream trades for a specific user.

        Args:
            user_address: Address of the user (defaults to sender address)
            market: Optional market to filter by
            callback: Function to call with each trade

        Returns:
            Subscription ID that can be used to unsubscribe

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        market_address = market.address if market else None
        return await self._execution_client.stream_user_trades(
            user_address=user_address or self._sender_address,
            market_address=market_address,
            callback=callback,
        )

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from a streaming subscription.

        Args:
            subscription_id: ID of the subscription to cancel

        Raises:
            ValueError: If execution client is not initialized
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        await self._execution_client.unsubscribe(subscription_id)

    async def get_order_book_snapshot(
            self,
            market: Market,
            depth: int = 10
    ) -> dict[str, Any]:
        """
        Get current order book snapshot from the chain.

        Args:
            market: Market to get order book for
            depth: Number of price levels to fetch on each side

        Returns:
            Dictionary with bids and asks arrays
        """
        if not self._execution_client:
            raise ValueError("Execution client not initialized. Sender address is required.")

        return await self._execution_client.get_order_book_snapshot(market=market, depth=depth)
