"""Data models for GTE API."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Asset:
    """Asset model."""

    address: str
    decimals: int
    name: str
    symbol: str
    creator: Optional[str] = None
    total_supply: Optional[float] = None
    media_uri: Optional[str] = None
    balance: Optional[float] = None

    @classmethod
    def from_api(cls, data: Dict, with_balance: bool = False) -> 'Asset':
        """Create an Asset object from API response data.

        Args:
            data: API response data
            with_balance: Whether the data includes balance information

        Returns:
            Asset object
        """
        return cls(
            address=data.get('address'),
            decimals=data.get('decimals'),
            name=data.get('name'),
            symbol=data.get('symbol'),
            creator=data.get('creator'),
            total_supply=data.get('totalSupply'),
            media_uri=data.get('mediaUri'),
            balance=data.get('balance') if with_balance else None
        )


@dataclass
class Market:
    """Market model."""

    address: str
    market_type: str
    base_asset: Asset
    quote_asset: Asset
    price: Optional[float] = None
    volume_24h: Optional[float] = None

    @classmethod
    def from_api(cls, data: Dict) -> 'Market':
        """Create a Market object from API response data.

        Args:
            data: API response data

        Returns:
            Market object
        """
        return cls(
            address=data.get('address'),
            market_type=data.get('marketType'),
            base_asset=Asset.from_api(data.get('baseAsset', {})),
            quote_asset=Asset.from_api(data.get('quoteAsset', {})),
            price=data.get('price'),
            volume_24h=data.get('volume24hr')
        )

    @property
    def pair(self) -> str:
        """Get the trading pair symbol."""
        return f"{self.base_asset.symbol}/{self.quote_asset.symbol}"


@dataclass
class Candle:
    """Candlestick model."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_address: Optional[str] = None
    interval: Optional[str] = None
    num_trades: Optional[int] = None

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the candle."""
        return datetime.fromtimestamp(self.timestamp / 1000)

    @classmethod
    def from_api(cls, data: Dict) -> 'Candle':
        """Create a Candle object from API response data.

        Args:
            data: API response data

        Returns:
            Candle object
        """
        return cls(
            timestamp=data.get('timestamp') or data.get('t'),
            open=float(data.get('open') or data.get('o', 0)),
            high=float(data.get('high') or data.get('h', 0)),
            low=float(data.get('low') or data.get('l', 0)),
            close=float(data.get('close') or data.get('c', 0)),
            volume=float(data.get('volume') or data.get('v', 0)),
            market_address=data.get('m'),
            interval=data.get('i'),
            num_trades=data.get('n')
        )


@dataclass
class Trade:
    """Trade model."""

    market_address: str
    timestamp: int
    price: float
    size: float
    side: str  # "buy" or "sell"
    tx_hash: Optional[str] = None
    maker: Optional[str] = None
    taker: Optional[str] = None
    trade_id: Optional[int] = None

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the trade."""
        return datetime.fromtimestamp(self.timestamp / 1000)

    @classmethod
    def from_api(cls, data: Dict) -> 'Trade':
        """Create a Trade object from API response data.

        Args:
            data: API response data

        Returns:
            Trade object
        """
        return cls(
            market_address=data.get('m', None),
            timestamp=data.get('timestamp') or data.get('t'),
            price=float(data.get('price') or data.get('px', 0)),
            size=float(data.get('size') or data.get('sz', 0)),
            side=data.get('side') or data.get('sd', ''),
            tx_hash=data.get('transactionHash') or data.get('h'),
            maker=data.get('maker'),
            taker=data.get('taker'),
            trade_id=data.get('id')
        )


@dataclass
class Position:
    """LP position model."""

    market: Market
    user: str
    token0_amount: float
    token1_amount: float

    @classmethod
    def from_api(cls, data: Dict) -> 'Position':
        """Create a Position object from API response data.

        Args:
            data: API response data

        Returns:
            Position object
        """
        return cls(
            market=Market.from_api(data.get('market', {})),
            user=data.get('user'),
            token0_amount=data.get('token0Amount'),
            token1_amount=data.get('token1Amount')
        )


@dataclass
class OrderbookUpdate:
    """Orderbook update model."""

    market_address: str
    timestamp: int
    bids: List[Dict[str, Any]]  # [{"price": float, "size": float, "count": int}, ...]
    asks: List[Dict[str, Any]]  # [{"price": float, "size": float, "count": int}, ...]

    @property
    def best_bid(self) -> Optional[Dict[str, float]]:
        """Get the best bid."""
        if not self.bids:
            return None
        return max(self.bids, key=lambda x: x['price'])

    @property
    def best_ask(self) -> Optional[Dict[str, float]]:
        """Get the best ask."""
        if not self.asks:
            return None
        return min(self.asks, key=lambda x: x['price'])

    @property
    def spread(self) -> Optional[float]:
        """Get the bid-ask spread."""
        if not self.best_bid or not self.best_ask:
            return None
        return self.best_ask['price'] - self.best_bid['price']

    @property
    def mid_price(self) -> Optional[float]:
        """Get the mid price."""
        if not self.best_bid or not self.best_ask:
            return None
        return (self.best_ask['price'] + self.best_bid['price']) / 2

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the update."""
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class Order:
    """Order model."""

    id: str
    market_address: str
    side: str  # "buy" or "sell"
    type: str  # "limit" or "market"
    amount: float
    price: Optional[float]
    time_in_force: str  # "GTC", "IOC", "FOK"
    status: str  # "open", "filled", "cancelled"
    filled_amount: float
    filled_price: float
    created_at: int
    
    @property
    def datetime(self) -> datetime:
        """Get the datetime of the order."""
        return datetime.fromtimestamp(self.created_at / 1000)
    
    @property
    def filled_percentage(self) -> float:
        """Get the filled percentage of the order."""
        if self.amount == 0:
            return 0
        return (self.filled_amount / self.amount) * 100
    
    @classmethod
    def from_api(cls, data: Dict) -> 'Order':
        """Create an Order object from API response data.

        Args:
            data: API response data

        Returns:
            Order object
        """
        return cls(
            id=data.get('id'),
            market_address=data.get('marketAddress'),
            side=data.get('side'),
            type=data.get('type'),
            amount=data.get('amount'),
            price=data.get('price'),
            time_in_force=data.get('timeInForce', 'GTC'),
            status=data.get('status'),
            filled_amount=data.get('filledAmount', 0),
            filled_price=data.get('filledPrice', 0),
            created_at=data.get('createdAt')
        )
