"""Market data access client for GTE."""

import logging

import asyncio
from typing import cast
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.rest import RestApi
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.clob import ICLOB
from gte_py.models import Token, TokenDetail, Market, MarketType

logger = logging.getLogger(__name__)


class InfoClient:
    """Retrieves and caches market and token data from chain or REST."""

    def __init__(
        self,
        rest: RestApi,
        web3: AsyncWeb3,
        clob: CLOBClient,
        token: TokenClient,
    ):
        self._rest = rest
        self._web3 = web3
        self._clob = clob
        self._token = token
        self._token_cache: dict[ChecksumAddress, Token] = {}
        self._market_cache: dict[ChecksumAddress, Market] = {}

    async def init(self):
        await self._clob.init()

    async def get_token_from_api(self, address: ChecksumAddress) -> Token:
        if address in self._token_cache:
            return self._token_cache[address]
        data = await self._rest.get_token(address)
        token = Token.from_api(cast(TokenDetail, data))
        self._token_cache[address] = token
        return token

    async def get_token_from_chain(self, address: ChecksumAddress) -> Token:
        if address in self._token_cache:
            return self._token_cache[address]
        contract = self._token.get_erc20(address)
        decimals, name, symbol = await asyncio.gather(
            contract.decimals(),
            contract.name(),
            contract.symbol(),
        )
        token = Token(address=address, decimals=decimals, name=name, symbol=symbol)
        self._token_cache[address] = token
        return token

    async def get_token(self, address: ChecksumAddress, *, use_chain: bool = False) -> Token:
        if address in self._token_cache:
            return self._token_cache[address]
        return await (
            self.get_token_from_chain(address)
            if use_chain
            else self.get_token_from_api(address)
        )
    
    async def get_tokens(
        self,
        *,
        creator: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Token]:
        response = await self._rest.get_tokens(
            creator=creator,
            limit=limit,
            offset=offset,
        )
        tokens = [Token.from_api(data) for data in response]
        for token in tokens:
            self._token_cache[token.address] = token
        return tokens


    async def get_market_from_api(self, address: ChecksumAddress) -> Market:
        if address in self._market_cache:
            return self._market_cache[address]
        data = await self._rest.get_market(address)
        market = Market.from_api(data)
        self._market_cache[address] = market
        return market

    async def get_market_from_chain(
        self,
        *,
        address: ChecksumAddress | None = None,
        clob: ICLOB | None = None,
    ) -> Market:
        if not address and not clob:
            raise ValueError("Must provide either 'address' or 'clob'")

        clob_instance = clob or self._clob.get_clob(cast(ChecksumAddress, address))

        if clob_instance.address in self._market_cache:
            return self._market_cache[clob_instance.address]

        _, _, quote, base, _, _ = await clob_instance.get_market_config()

        base_token, quote_token = await asyncio.gather(
            self.get_token(base, use_chain=True),
            self.get_token(quote, use_chain=True),
        )

        market = Market(
            address=clob_instance.address,
            market_type=MarketType.CLOB_SPOT,
            base=base_token,
            quote=quote_token,
        )
        self._market_cache[clob_instance.address] = market
        return market

    async def get_market(self, address: ChecksumAddress, *, use_chain: bool = False) -> Market:
        if address in self._market_cache:
            return self._market_cache[address]
        return await (
            self.get_market_from_chain(address=address)
            if use_chain
            else self.get_market_from_api(address)
        )

    async def get_markets(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        market_type: MarketType | str | None = None,
        token_address: str | None = None,
    ) -> list[Market]:
        mtype = market_type.value if isinstance(market_type, MarketType) else market_type
        data = await self._rest.get_markets(
            limit=limit,
            offset=offset,
            market_type=mtype,
            token_address=token_address,
        )
        markets = []
        for d in data:
            market = Market.from_api(d)
            self._market_cache[market.address] = market
            markets.append(market)
        return markets
