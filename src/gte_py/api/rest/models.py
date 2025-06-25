"""TypedDict models for REST API responses."""

from typing import Any


class TokenDetail:
    """Token details returned by the API."""

    def __init__(
        self,
        address: str,
        decimals: int,
        name: str,
        symbol: str,
        totalSupply: int,
        logoUri: str,
        priceUsd: float,
        volume1HrUsd: float,
        volume24HrUsd: float,
        marketCapUsd: float,
        marketType: str,
    ):
        self.address = address
        self.decimals = decimals
        self.name = name
        self.symbol = symbol
        self.totalSupply = totalSupply
        self.logoUri = logoUri
        self.priceUsd = priceUsd
        self.volume1HrUsd = volume1HrUsd
        self.volume24HrUsd = volume24HrUsd
        self.marketCapUsd = marketCapUsd
        self.marketType = marketType

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "TokenDetail":
        """
        Create a TokenDetail from API response data.
        
        Args:
            data: Raw API response dictionary
            
        Returns:
            TokenDetail object
        """
        return cls(
            address=data["address"],
            decimals=data["decimals"],
            name=data["name"],
            symbol=data["symbol"],
            totalSupply=data["totalSupply"],
            logoUri=data["logoUri"],
            priceUsd=data["priceUsd"],
            volume1HrUsd=data["volume1HrUsd"],
            volume24HrUsd=data["volume24HrUsd"],
            marketCapUsd=data["marketCapUsd"],
            marketType=data["marketType"],
        )


class MarketDetail:
    """Market details returned by the API."""

    def __init__(
        self,
        marketType: str,
        address: str,
        baseToken: TokenDetail,
        quoteToken: TokenDetail,
        price: float,
        priceUsd: float,
        volume24HrUsd: float,
        priceUsdChange24Hr: float,
        priceUsdChange1Hr: float,
        volume1HrUsd: float,
        marketCapUsd: float,
        createdAt: int,
        tvlUsd: float,
        liquidityUsd: float,
    ):
        self.marketType = marketType
        self.address = address
        self.baseToken = baseToken
        self.quoteToken = quoteToken
        self.price = price
        self.priceUsd = priceUsd
        self.volume24HrUsd = volume24HrUsd
        self.priceUsdChange24Hr = priceUsdChange24Hr
        self.priceUsdChange1Hr = priceUsdChange1Hr
        self.volume1HrUsd = volume1HrUsd
        self.marketCapUsd = marketCapUsd
        self.createdAt = createdAt
        self.tvlUsd = tvlUsd
        self.liquidityUsd = liquidityUsd

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "MarketDetail":
        """
        Create a MarketDetail from API response data.
        
        Args:
            data: Raw API response dictionary
            
        Returns:
            MarketDetail object
        """
        return cls(
            marketType=data["marketType"],
            address=data["address"],
            baseToken=TokenDetail.from_api(data["baseToken"]),
            quoteToken=TokenDetail.from_api(data["quoteToken"]),
            price=data["price"],
            priceUsd=data["priceUsd"],
            volume24HrUsd=data["volume24HrUsd"],
            priceUsdChange24Hr=data["priceUsdChange24Hr"],
            priceUsdChange1Hr=data["priceUsdChange1Hr"],
            volume1HrUsd=data["volume1HrUsd"],
            marketCapUsd=data["marketCapUsd"],
            createdAt=data["createdAt"],
            tvlUsd=data["tvlUsd"],
            liquidityUsd=data["liquidityUsd"],
        )
