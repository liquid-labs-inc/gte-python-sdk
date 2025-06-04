"""TypedDict models for REST API responses."""

from typing import TypedDict, Optional, Literal


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
