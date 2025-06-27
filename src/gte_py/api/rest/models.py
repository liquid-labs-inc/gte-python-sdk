"""TypedDict models for REST API responses."""

from typing import TypedDict, Any

from eth_utils import to_checksum_address
from hexbytes import HexBytes

from gte_py.models import Market, MarketType, Token, Position, Trade, OrderSide


class TokenDetail(TypedDict):
    """Token details returned by the API."""

    address: str
    decimals: int
    name: str
    symbol: str
    totalSupply: int
    logoUri: str
    priceUsd: float
    volume1HrUsd: float
    volume24HrUsd: float
    marketCapUsd: float
    marketType: str


def token_detail_to_model(data: TokenDetail) -> Token:
    """Create an Asset object from API response data."""
    address = to_checksum_address(data["address"])

    return Token(
        address=address,
        decimals=data["decimals"],
        name=data["name"],
        symbol=data["symbol"],
        total_supply=data["totalSupply"],
    )


class MarketDetail(TypedDict):
    """Market details returned by the API."""

    marketType: str
    address: str
    baseToken: TokenDetail
    quoteToken: TokenDetail
    price: float
    priceUsd: float
    volume24HrUsd: float
    priceUsdChange24Hr: float
    priceUsdChange1Hr: float
    volume1HrUsd: float
    marketCapUsd: float
    createdAt: int
    tvlUsd: float
    liquidityUsd: float


def market_detail_to_model(data: MarketDetail) -> Market:
    """Create a Market object from API response data."""
    contract_address = data["address"]

    return Market(
        address=to_checksum_address(contract_address),
        market_type=MarketType(data["marketType"]),
        base=token_detail_to_model(data["baseToken"]),
        quote=token_detail_to_model(data["quoteToken"]),
        price=data.get("price"),
        volume_24hr_usd=data.get("volume24HrUsd"),
    )


def position_to_model(data: dict[str, Any]) -> Position:
    """Create a Position object from API response data."""
    return Position(
        market=market_detail_to_model(data["market"]),
        user=to_checksum_address(data["user"]),
        token0_amount=data.get("token0Amount", 0.0),
        token1_amount=data.get("token1Amount", 0.0),
    )


def trade_to_model(cls, data: dict[str, Any]) -> Trade:
    """Create a Trade object from API response data."""

    side = OrderSide.from_str(data["side"])
    tx_hash = HexBytes(data["txnHash"])
    maker = data["maker"] and to_checksum_address(data["maker"]) or None
    taker = data["taker"] and to_checksum_address(data["taker"]) or None

    return cls(
        market_address=to_checksum_address(data['marketAddress']),
        timestamp=data["timestamp"],
        price=int(data["price"]),
        size=int(data["size"]),
        side=side,
        tx_hash=tx_hash,
        maker=maker,
        taker=taker,
    )
