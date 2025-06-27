"""Market information service for GTE."""

import logging

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.chain.clob import ICLOB
from gte_py.api.rest import RestApi
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.rest.models import market_detail_to_model, token_detail_to_model
from gte_py.models import Token, Market, MarketType

logger = logging.getLogger(__name__)


class InfoClient:
    """Service for retrieving market information from the blockchain."""

    def __init__(
        self,
        rest: RestApi,
        web3: AsyncWeb3,
        clob_client: CLOBClient,
        token_client: TokenClient,
    ):
        """
        Initialize the market info service.

        Args:
            rest: RestApi instance
            web3: AsyncWeb3 instance
            clob_client: ICLOBClient instance
        """
        self._rest = rest
        self._web3 = web3
        self._token_client = token_client
        self._clob_client = clob_client
        self._markets: dict[ChecksumAddress, Market] = {}
        self._assets: dict[ChecksumAddress, Token] = {}

    async def init(self):
        # Get and initialize CLOB factory
        await self._clob_client.init()

    async def get_tokens(
        self, creator: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[Token]:
        """
        Get list of assets.

        Args:
            creator: Filter by creator address
            limit: Maximum number of assets to return
            offset: Offset for pagination

        Returns:
            List of assets
        """
        response = await self._rest.get_tokens(
            creator=creator, limit=limit, offset=offset
        )
        return [token_detail_to_model(asset_data) for asset_data in response.get("assets", [])]

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        market_type: str | None = None,
        token_address: str | None = None,
    ) -> list[Market]:
        """
        Get list of markets.

        Args:
            limit: Maximum number of markets to return
            offset: Offset for pagination
            market_type: Filter by market type (amm, launchpad, clob)
            token_address: Filter by base asset address

        Returns:
            List of markets
        """
        response = await self._rest.get_markets(
            limit=limit,
            offset=offset,
            market_type=market_type,
            token_address=token_address,
        )

        markets = [market_detail_to_model(market_data) for market_data in response]

        return markets

    async def get_market(self, address: ChecksumAddress) -> Market:
        """
        Get market information by address.

        Args:
            address: Market address

        Returns:
            Market object with details
        """
        if address in self._markets:
            return self._markets[address]

        resp = await self._rest.get_market(address)
        market = market_detail_to_model(resp)
        self._markets[address] = market
        return market

    async def get_market_from_chain(
        self, address_or_clob: ChecksumAddress | ICLOB
    ) -> Market:
        # Get market config for additional details
        if not isinstance(address_or_clob, ICLOB):
            clob = self._clob_client.get_clob(address_or_clob)
        else:
            clob = address_or_clob
        if clob.address in self._markets:
            return self._markets[clob.address]
        factory, mask, quote, base, quote_size, base_size = (
            await clob.get_market_config()
        )

        base_contract = self._token_client.get_erc20(base)
        quote_contract = self._token_client.get_erc20(quote)

        base_asset = Token(
            address=base,
            decimals=await base_contract.decimals(),
            name=await base_contract.name(),
            symbol=await base_contract.symbol(),
        )

        quote_asset = Token(
            address=quote,
            decimals=await quote_contract.decimals(),
            name=await quote_contract.name(),
            symbol=await quote_contract.symbol(),
        )

        # Create a market info object
        market_info = Market(
            address=clob.address,
            market_type=MarketType.CLOB_SPOT,
            base=base_asset,
            quote=quote_asset,
        )
        self._markets[clob.address] = market_info

        return market_info
