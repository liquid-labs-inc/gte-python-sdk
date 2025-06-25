"""Market data access client for GTE."""

import logging
from typing import cast, Any, Callable
from eth_typing import ChecksumAddress

from gte_py.api.rest import RestApi
from gte_py.api.ws import WebSocketApi
from gte_py.api.ws import TradeData, CandleData, OrderBookData
from gte_py.api.rest.models import TokenDetail, MarketDetail
from gte_py.models import MarketType, OrderBookSnapshot

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
            web3: Web3 instance for blockchain interactions
            clob: CLOB client for market data
            token: Token client for ERC20 interactions
        """
        self._rest: RestApi = rest
        self._websocket: WebSocketApi = websocket
        self._token_cache: dict[ChecksumAddress, TokenDetail] = {}
        self._market_cache: dict[ChecksumAddress, MarketDetail] = {}
        self._subscriptions: set[tuple[str, dict[str, Any]]] = set()

    # ================= TOKEN METHODS =================

    async def get_token(self, address: ChecksumAddress) -> TokenDetail:
        """
        Get token information from the REST API (default source).
        
        Args:
            address: Token contract address
            
        Returns:
            TokenDetail object with metadata
        """
        if address in self._token_cache:
            return self._token_cache[address]
        
        data = await self._rest.get_token(address)
        token = TokenDetail.from_api(data)
        self._token_cache[address] = token
        return token

    async def search_tokens(
        self, 
        query: str, 
        *, 
        limit: int = 100
    ) -> list[TokenDetail]:
        """
        Search for tokens by name or symbol.
        
        Args:
            query: Search term (token name or symbol)
            limit: Maximum number of results to return
            
        Returns:
            List of matching TokenDetail objects
        """
        raw_data = await self._rest.search_tokens(
            query=query,
            limit=limit,
        )
        
        tokens = []
        for data in raw_data:
            token = TokenDetail.from_api(data)
            self._token_cache[token.address] = token
            tokens.append(token)
        return tokens

    async def get_tokens(
        self,
        *,
        creator: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TokenDetail]:
        """
        Get a list of tokens, optionally filtered by creator.
        
        Args:
            creator: Optional creator address to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of TokenDetail objects
        """
        raw_data = await self._rest.get_tokens(
            creator=creator,
            limit=limit,
            offset=offset,
        )
        
        tokens = []
        for data in raw_data:
            token = TokenDetail.from_api(data)
            self._token_cache[token.address] = token
            tokens.append(token)
        return tokens

    # ================= MARKET METHODS =================

    async def get_market(self, address: ChecksumAddress) -> MarketDetail:
        """
        Get market information from the REST API (default source).
        
        Args:
            address: Market contract address
            
        Returns:
            MarketDetail object with metadata
        """
        if address in self._market_cache:
            return self._market_cache[address]
        
        data = await self._rest.get_market(address)
        market = MarketDetail.from_api(data)
        self._market_cache[address] = market
        return market

    async def get_markets(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        market_type: MarketType | str | None = None,
        token_address: str | None = None,
    ) -> list[MarketDetail]:
        """
        Get a list of markets with optional filtering.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            market_type: Filter by market type (CLOB_SPOT, AMM, etc.)
            token_address: Filter by token address
            
        Returns:
            List of MarketDetail objects
        """
        # Convert MarketType enum to string if needed
        mtype = market_type.value if isinstance(market_type, MarketType) else market_type
        
        raw_data = await self._rest.get_markets(
            limit=limit,
            offset=offset,
            market_type=mtype,
            token_address=token_address,
        )
        
        markets = []
        for data in raw_data:
            market = MarketDetail.from_api(data)
            self._market_cache[market.address] = market
            markets.append(market)
        return markets
    
    # ================= REST API WRAPPERS =================

    async def get_health(self) -> dict[str, Any]:
        """
        Get API health status.
        
        Returns:
            Health status information
        """
        return await self._rest.get_health()

    async def get_info(self) -> dict[str, Any]:
        """
        Get GTE info.
        
        Returns:
            GTE information including stats
        """
        return await self._rest.get_info()

    async def get_candles(
        self,
        market_address: ChecksumAddress,
        interval: str,
        start_time: int,
        end_time: int | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """
        Get candles for a market.
        
        Args:
            market_address: Market contract address
            interval: Interval of the candle (1s, 15s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Range 1-1000
            
        Returns:
            List of candles
        """
        return await self._rest.get_candles(
            market_address=market_address,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    async def get_trades(
        self,
        market_address: ChecksumAddress,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get trades for a market.
        
        Args:
            market_address: Market contract address
            limit: Range 1-1000
            offset: Min value 0
            
        Returns:
            List of trades
        """
        return await self._rest.get_trades(
            market_address=market_address,
            limit=limit,
            offset=offset,
        )

    async def get_order_book(
        self,
        market_address: ChecksumAddress,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get order book snapshot for a market.
        
        Args:
            market_address: Market contract address
            limit: Number of price levels to include on each side, range 1-100
            
        Returns:
            Order book data with bids and asks
        """
        return await self._rest.get_order_book(
            market_address=market_address,
            limit=limit,
        )

    async def get_order_book_snapshot(
        self,
        market_address: ChecksumAddress,
        limit: int = 10,
    ) -> OrderBookSnapshot:
        """
        Get typed order book snapshot for a market.
        
        Args:
            market_address: Market contract address
            limit: Number of price levels to include on each side, range 1-100
            
        Returns:
            Typed order book data with bids and asks
        """
        return await self._rest.get_order_book_snapshot(
            market_address=market_address,
            limit=limit,
        )

    async def get_user_lp_positions(
        self,
        user_address: ChecksumAddress,
    ) -> dict[str, Any]:
        """
        Get LP positions for a user.
        
        Args:
            user_address: User address
            
        Returns:
            List of LP positions
        """
        return await self._rest.get_user_lp_positions(user_address=user_address)

    async def get_user_portfolio(
        self,
        user_address: ChecksumAddress,
    ) -> dict[str, Any]:
        """
        Get user's portfolio.
        
        Args:
            user_address: User address
            
        Returns:
            User portfolio including token balances
        """
        return await self._rest.get_user_portfolio(user_address=user_address)

    async def get_user_trades(
        self,
        user_address: ChecksumAddress,
        market_address: ChecksumAddress | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get trades for a user.
        
        Args:
            user_address: User address
            market_address: Market address (optional)
            limit: Range 1-1000
            offset: Min value 0
            
        Returns:
            List of user trades
        """
        return await self._rest.get_user_trades(
            user_address=user_address,
            market_address=market_address,
            limit=limit,
            offset=offset,
        )

    async def get_user_open_orders(
        self,
        user_address: ChecksumAddress,
        market_address: ChecksumAddress | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get open orders for a user.
        
        Args:
            user_address: User address
            market_address: Market address (optional)
            limit: Range 1-1000
            offset: Min value 0
            
        Returns:
            List of user's open orders
        """
        return await self._rest.get_user_open_orders(
            user_address=user_address,
            market_address=market_address,
            limit=limit,
            offset=offset,
        )

    async def get_user_filled_orders(
        self,
        user_address: ChecksumAddress,
        market_address: ChecksumAddress | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get filled orders for a user.
        
        Args:
            user_address: User address
            market_address: Market address (optional)
            limit: Range 1-1000
            offset: Min value 0
            
        Returns:
            List of user's filled orders
        """
        return await self._rest.get_user_filled_orders(
            user_address=user_address,
            market_address=market_address,
            limit=limit,
            offset=offset,
        )

    async def get_user_order_history(
        self,
        user_address: ChecksumAddress,
        market_address: ChecksumAddress | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get order history for a user.
        
        Args:
            user_address: User address
            market_address: Market address (optional)
            limit: Range 1-1000
            offset: Min value 0
            
        Returns:
            List of user's order history
        """
        return await self._rest.get_user_order_history(
            user_address=user_address,
            market_address=market_address,
            limit=limit,
            offset=offset,
        )

    # ================= WEBSOCKET API WRAPPERS =================

    async def subscribe_trades(
        self,
        market: ChecksumAddress,
        callback: Callable[[TradeData], Any],
    ) -> None:
        """
        Subscribe to trades for a market.
        
        Args:
            market: Market address
            callback: Function to call when a trade is received
        """
        params = {
            "market": market,
        }
        await self._websocket.subscribe_trades(market, callback)
        self._subscriptions.add(("trades", params))

    async def subscribe_candles(
        self,
        market: ChecksumAddress,
        interval: str,
        callback: Callable[[CandleData], Any],
    ) -> None:
        """
        Subscribe to candles for a market.
        
        Args:
            market: Market address
            interval: Candle interval (1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w)
            callback: Function to call when a candle is received
        """
        params = {
            "market": market,
            "interval": interval,
        }
        await self._websocket.subscribe_candles(market, interval, callback)
        self._subscriptions.add(("candles", params))

    async def subscribe_orderbook(
        self,
        market: ChecksumAddress,
        callback: Callable[[OrderBookData], Any],
        limit: int = 10,
    ) -> None:
        """
        Subscribe to orderbook for a market.
        
        Args:
            market: Market address
            callback: Function to call when an orderbook update is received
            limit: Number of levels to include (defaults to 10)
        """
        params = {
            "market": market,
            "limit": limit,
        }
        await self._websocket.subscribe_orderbook(market, callback, limit)
        self._subscriptions.add(("orderbook", params))

    def get_subscriptions(self) -> list[tuple[str, dict[str, Any]]]:
        """
        Get list of active subscriptions.
        
        Returns:
            List of (stream_type, market) tuples for active subscriptions
        """
        return list(self._subscriptions)

    def clear_subscriptions(self) -> None:
        """
        Clear the subscription cache (does not unsubscribe from WebSocket).
        Use this when you want to reset the subscription tracking.
        """
        self._subscriptions.clear()
