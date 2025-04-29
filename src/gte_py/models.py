"""Data models for GTE API."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Tuple

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncWeb3
from gte_py.api.chain import Side as ContractSide


class MarketType(Enum):
    """Market types supported by GTE."""

    AMM = "amm"
    LAUNCHPAD = "launchpad"
    CLOB = "clob"


Side = ContractSide


class OrderType(Enum):
    """Order type - limit or market."""

    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(Enum):
    """Time in force for orders."""

    GTC = "GTC"  # Good till cancelled
    GTT = "GTT"  # Good till time
    PostOnly = "PostOnly"  # Post only
    IOC = "IOC"  # Immediate or cancel
    FOK = "FOK"  # Fill or kill


class OrderStatus(Enum):
    """Order status."""

    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


@dataclass
class Asset:
    """Asset model."""

    address: ChecksumAddress
    decimals: int
    name: str
    symbol: str
    creator: ChecksumAddress | None = None
    total_supply: float | None = None
    media_uri: str | None = None
    balance: float | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any], with_balance: bool = False) -> "Asset":
        """Create an Asset object from API response data."""
        address = data.get("address", "")
        creator = data.get("creator")

        # Convert address strings to ChecksumAddress
        if address and isinstance(address, str):
            address = AsyncWeb3.to_checksum_address(address)
        if creator and isinstance(creator, str):
            creator = AsyncWeb3.to_checksum_address(creator)

        return cls(
            address=address,
            decimals=data.get("decimals", 18),
            name=data.get("name", ""),
            symbol=data.get("symbol", ""),
            creator=creator,
            total_supply=data.get("totalSupply"),
            media_uri=data.get("mediaUri"),
            balance=data.get("balance") if with_balance else None,
        )


@dataclass
class Market:
    """Market model."""

    address: ChecksumAddress
    market_type: MarketType
    base_asset: Asset
    quote_asset: Asset
    tick_size_in_quote: int
    tick_size: float
    lot_size_in_base: int
    lot_size: float
    base_decimals: int = 18
    quote_decimals: int = 18
    price: float | None = None
    volume_24h: float | None = None
    base_token_address: ChecksumAddress | None = None
    quote_token_address: ChecksumAddress | None = None

    def round_quote_to_ticks_int(self, price: float) -> int:
        """Convert price to integer based on tick size."""
        ticks_in_float = price / self.tick_size
        ticks_in_int = round(ticks_in_float)
        price_in_quote = ticks_in_int * self.tick_size_in_quote
        return price_in_quote

    def round_base_to_lots_int(self, amount: float) -> int:
        """Convert amount to integer based on lot size."""
        amount_in_float = amount / self.lot_size
        amount_in_int = round(amount_in_float)
        amount_in_base = amount_in_int * self.lot_size_in_base
        return amount_in_base

    def check_tick_size(self, price: int) -> bool:
        return price % self.tick_size_in_quote == 0

    def check_lot_size(self, amount: int) -> bool:
        return amount % self.lot_size_in_base == 0

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Market":
        """Create a Market object from API response data."""
        contract_address = data["contractAddress"]
        base_token_address = data["baseTokenAddress"]
        quote_token_address = data["quoteTokenAddress"]

        return cls(
            address=contract_address,
            market_type=MarketType(data.get("marketType", "amm")),
            base_asset=Asset.from_api(data.get("baseAsset", {})),
            quote_asset=Asset.from_api(data.get("quoteAsset", {})),
            base_token_address=base_token_address,
            quote_token_address=quote_token_address,
            base_decimals=data.get("baseDecimals", 18),
            quote_decimals=data.get("quoteDecimals", 18),
            tick_size_in_quote=data.get("tickSize", 0.01),
            lot_size_in_base=data.get("baseAtomsPerLot", 1),
            price=data.get("price"),
            volume_24h=data.get("volume24hr"),
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
    market_address: str | None = None
    interval: str | None = None
    num_trades: int | None = None

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the candle."""
        return datetime.fromtimestamp(self.timestamp / 1000)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Candle":
        """Create a Candle object from API response data."""
        return cls(
            timestamp=data.get("timestamp") or data.get("t", 0),
            open=float(data.get("open") or data.get("o", 0)),
            high=float(data.get("high") or data.get("h", 0)),
            low=float(data.get("low") or data.get("l", 0)),
            close=float(data.get("close") or data.get("c", 0)),
            volume=float(data.get("volume") or data.get("v", 0)),
            market_address=data.get("m"),
            interval=data.get("i"),
            num_trades=data.get("n"),
        )


@dataclass
class Trade:
    """Trade model."""

    market_address: str  # Virtual market address
    timestamp: int
    price: float
    size: float
    side: Side
    tx_hash: HexBytes | None = None  # Transaction hash is an Ethereum address
    maker: ChecksumAddress | None = None
    taker: ChecksumAddress | None = None
    trade_id: int | None = None

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the trade."""
        return datetime.fromtimestamp(self.timestamp / 1000)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Trade":
        """Create a Trade object from API response data."""
        side_str = data.get("side") or data.get("sd", "buy")
        tx_hash = data.get("transactionHash") or data.get("h")
        maker = data.get("maker")
        taker = data.get("taker")

        # Convert address strings to ChecksumAddress when present
        if tx_hash and isinstance(tx_hash, str):
            tx_hash = AsyncWeb3.to_checksum_address(tx_hash)
        if maker and isinstance(maker, str):
            maker = AsyncWeb3.to_checksum_address(maker)
        if taker and isinstance(taker, str):
            taker = AsyncWeb3.to_checksum_address(taker)

        return cls(
            market_address=data.get("m", ""),
            timestamp=data.get("timestamp") or data.get("t", 0),
            price=float(data.get("price") or data.get("px", 0)),
            size=float(data.get("size") or data.get("sz", 0)),
            side=Side(side_str),
            tx_hash=tx_hash,
            maker=maker,
            taker=taker,
            trade_id=data.get("id"),
        )


@dataclass
class Position:
    """LP position model."""

    market: Market
    user: ChecksumAddress
    token0_amount: float
    token1_amount: float

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Position":
        """Create a Position object from API response data."""
        user = data.get("user", "")
        if user and isinstance(user, str):
            user = AsyncWeb3.to_checksum_address(user)

        return cls(
            market=Market.from_api(data.get("market", {})),
            user=user,
            token0_amount=data.get("token0Amount", 0.0),
            token1_amount=data.get("token1Amount", 0.0),
        )


@dataclass
class PriceLevel:
    """Price level in orderbook."""

    price: int
    size: int
    count: int


@dataclass
class OrderbookUpdate:
    """Orderbook update model."""

    market_address: str
    timestamp: int
    bids: list[PriceLevel]
    asks: list[PriceLevel]

    @property
    def best_bid(self) -> PriceLevel | None:
        """Get the best bid."""
        if not self.bids:
            return None
        return max(self.bids, key=lambda x: x.price)

    @property
    def best_ask(self) -> PriceLevel | None:
        """Get the best ask."""
        if not self.asks:
            return None
        return min(self.asks, key=lambda x: x.price)

    @property
    def spread(self) -> float | None:
        """Get the bid-ask spread."""
        if not self.best_bid or not self.best_ask:
            return None
        return self.best_ask.price - self.best_bid.price

    @property
    def mid_price(self) -> float | None:
        """Get the mid price."""
        if not self.best_bid or not self.best_ask:
            return None
        return (self.best_ask.price + self.best_bid.price) / 2

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the update."""
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class Order:
    """Order model."""

    order_id: int
    market_address: str
    side: Side
    order_type: OrderType
    amount: float
    price: float | None
    time_in_force: TimeInForce
    status: OrderStatus
    created_at: int
    owner: ChecksumAddress | None = None

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the order."""
        return datetime.fromtimestamp(self.created_at / 1000)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Order":
        """Create an Order object from API response data."""
        side_str = data.get("side", "buy")
        type_str = data.get("type", "limit")
        tif_str = data.get("timeInForce", "GTC")
        status_str = data.get("status", "open")

        return cls(
            order_id=data.get("id", ""),
            market_address=data.get("marketAddress", ""),
            side=Side(side_str),
            order_type=OrderType(type_str),
            amount=data.get("amount", 0.0),
            price=data.get("price"),
            time_in_force=TimeInForce(tif_str),
            status=OrderStatus(status_str),
            filled_amount=data.get("filledAmount", 0.0),
            filled_price=data.get("filledPrice", 0.0),
            created_at=data.get("createdAt", int(datetime.now().timestamp() * 1000)),
        )


@dataclass
class OrderBookSnapshot:
    """Snapshot of the orderbook at a point in time."""
    bids: List[Tuple[float, float, int]]  # (price, size, count)
    asks: List[Tuple[float, float, int]]  # (price, size, count)
    timestamp: int
    market_address: Optional[str] = None
