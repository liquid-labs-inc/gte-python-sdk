"""Data models for GTE API."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import floor, log10
from typing import Any, List, Optional, Tuple

from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address
from gte_py.api.rest.models import MarketDetail, TokenDetail
from hexbytes import HexBytes
from web3 import AsyncWeb3

from gte_py.api.chain.events import LimitOrderProcessedEvent, FillOrderProcessedEvent
from gte_py.api.chain.structs import OrderSide as ContractOrderSide, CLOBOrder
from gte_py.api.chain.utils import get_current_timestamp


class MarketType(Enum):
    """Market types supported by GTE."""

    AMM = "amm"
    LAUNCHPAD = "bonding-curve"
    CLOB_SPOT = "clob-spot"
    CLOB_PERP = "perps"


OrderSide = ContractOrderSide


class MarketSide(str, Enum):
    BID = "bid"
    ASK = "ask"

    @classmethod
    def from_string(cls, s: str) -> "MarketSide":
        """Convert a string to a MarketSide enum."""
        if s.lower() == "bid":
            return cls.BID
        elif s.lower() == "ask":
            return cls.ASK
        else:
            raise ValueError(f"Invalid market side: {s}. Must be 'bid' or 'ask'.")


class OrderType(Enum):
    """Order type - limit or market."""

    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(Enum):
    """Time in force for orders."""

    GTC = "GTC"  # Good till cancelled
    GTT = "GTT"  # Good till time
    POST_ONLY = "POST_ONLY"  # Post only
    IOC = "IOC"  # Immediate or cancel
    FOK = "FOK"  # Fill or kill


class OrderStatus(Enum):
    """Order status."""

    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


def round_decimals_int(n: float, sig: int) -> int:
    """Round a number to a specified number of significant digits."""
    n_int = round(n)
    if n_int == 0:
        return 0
    else:
        d = sig - int(floor(log10(abs(n_int)))) - 1
        return round(n_int, d)


@dataclass
class Token:
    """Asset model."""

    address: ChecksumAddress
    decimals: int
    name: str
    symbol: str
    total_supply: float | None = None

    def convert_amount_to_quantity(self, amount: int) -> float:
        """Convert amount in base units to float."""
        assert isinstance(amount, int), f"amount {amount} is not an integer"
        return amount / (10 ** self.decimals)

    def convert_quantity_to_amount(self, quantity: float) -> int:
        """Convert amount in float to base units."""
        assert isinstance(quantity, float), f"quantity {quantity} is not a float"
        scaled = quantity * (10 ** self.decimals)
        rounded = round_decimals_int(scaled, sig=8)
        return rounded

    @classmethod
    def from_api(cls, data: TokenDetail) -> "Token":
        """Create an Asset object from API response data."""
        address = to_checksum_address(data["address"])

        return cls(
            address=address,
            decimals=data["decimals"],
            name=data["name"],
            symbol=data["symbol"],
            total_supply=data["totalSupply"],
        )


@dataclass
class Market:
    """Market model."""

    address: ChecksumAddress
    market_type: MarketType
    base: Token
    quote: Token
    price: float | None = None
    volume_24hr_usd: float | None = None

    @classmethod
    def from_api(cls, data: MarketDetail) -> "Market":
        """Create a Market object from API response data."""
        contract_address = data["address"]

        return cls(
            address=to_checksum_address(contract_address),
            market_type=MarketType(data["marketType"]),
            base=Token.from_api(data["baseToken"]),
            quote=Token.from_api(data["quoteToken"]),
            price=data.get("price"),
            volume_24hr_usd=data.get("volume24HrUsd"),
        )

    @property
    def pair(self) -> str:
        """Get the trading pair symbol."""
        return f"{self.base.symbol}/{self.quote.symbol}"


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

    market_address: ChecksumAddress
    timestamp: int  # e.g. 1748406437000
    price: float
    size: float
    side: OrderSide
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
        if "side" not in data or not isinstance(data["side"], str):
            raise ValueError("Missing or invalid 'side' in trade data")
        if "timestamp" not in data:
            raise ValueError("Missing 'timestamp' in trade data")

        side = OrderSide.from_str(data["side"])
        tx_hash = HexBytes(data["txnHash"])
        maker = data["maker"] and to_checksum_address(data["maker"]) or None
        taker = data["taker"] and to_checksum_address(data["taker"]) or None

        return cls(
            market_address=to_checksum_address(data['marketAddress']),
            timestamp=data["timestamp"],
            price=float(data["price"]),
            size=float(data["size"]),
            side=side,
            tx_hash=tx_hash,
            maker=maker,
            taker=taker,
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
    side: OrderSide
    order_type: OrderType
    price: int | None
    time_in_force: TimeInForce
    status: OrderStatus
    remaining_amount: int | None = None  # remaining amount in base units
    placed_at: int | None = None  # Timestamp when the order was created
    filled_at: int | None = None  # Timestamp when the order was filled
    original_amount: int | None = None  # Original amount before any fills
    filled_amount: int | None = None  # Amount filled so far
    owner: ChecksumAddress | None = None
    txn_hash: HexBytes | None = None

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the order."""
        return datetime.fromtimestamp(self.placed_at / 1000)

    @classmethod
    def from_clob_order(cls, clob: CLOBOrder, market: Market) -> "Order":
        status = OrderStatus.OPEN
        if clob.amount == 0:
            status = OrderStatus.FILLED
        elif (
                clob.cancelTimestamp > 0 and clob.cancelTimestamp < get_current_timestamp()
        ):
            status = OrderStatus.EXPIRED

        # Create Order model
        return Order(
            order_id=clob.id,
            market_address=market.address,
            side=clob.side,
            order_type=OrderType.LIMIT,
            remaining_amount=clob.amount,
            price=clob.price,
            time_in_force=TimeInForce.GTC,  # Default
            status=status,
            owner=clob.owner,
            placed_at=0,  # Need to be retrieved from event timestamp
        )

    @classmethod
    def from_clob_limit_order_processed(
            cls, event: LimitOrderProcessedEvent, amount: int, side: OrderSide, price: int
    ) -> "Order":
        """Create an Order object from a CLOB limit order."""
        status = OrderStatus.OPEN
        if event.base_token_amount_traded == amount:
            status = OrderStatus.FILLED

        # Create Order model
        return cls(
            order_id=event.order_id,
            market_address=event.address,
            side=side,
            order_type=OrderType.LIMIT,
            remaining_amount=amount,
            price=price,
            time_in_force=TimeInForce.GTC,  # Default
            status=status,
            owner=event.account,
            placed_at=0,  # Need to be retrieved from event timestamp
        )

    @classmethod
    def from_clob_fill_order_processed(
            cls, event: FillOrderProcessedEvent, amount: int, side: OrderSide, price: int
    ) -> "Order":
        """Create an Order object from a CLOB limit order."""
        status = OrderStatus.OPEN
        if event.base_token_amount_traded == amount:
            status = OrderStatus.FILLED

        # Create Order model
        return cls(
            order_id=event.order_id,
            market_address=event.address,
            side=side,
            order_type=OrderType.LIMIT,
            remaining_amount=amount,
            price=price,
            time_in_force=TimeInForce.GTC,  # Default
            status=status,
            owner=event.account,
            placed_at=0,  # Need to be retrieved from event timestamp
        )


@dataclass
class OrderBookSnapshot:
    """Snapshot of the orderbook at a point in time."""

    bids: List[Tuple[float, float, int]]  # (price, size, count)
    asks: List[Tuple[float, float, int]]  # (price, size, count)
    timestamp: int
    market_address: Optional[str] = None
