"""Market information service for GTE."""

import logging

from eth_typing import ChecksumAddress
from web3 import Web3

from .contracts.erc20 import ERC20
from .contracts.factory import CLOBFactory
from .contracts.iclob import ICLOB
from .contracts.router import Router
from .models import Asset, Market, MarketType

logger = logging.getLogger(__name__)


class MarketService:
    """Service for retrieving market information from the blockchain."""

    def __init__(self, web3: Web3, router_address: ChecksumAddress):
        """
        Initialize the market info service.

        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        self.router_address = router_address
        self.router = Router(web3=web3, contract_address=self.router_address)

        # Get and initialize CLOB factory
        self._clob_factory_address: ChecksumAddress = self.router.get_clob_factory()
        self._clob_factory = CLOBFactory(web3=web3, contract_address=self._clob_factory_address)

        # Cache of discovered markets
        self._markets: dict[ChecksumAddress, Market] = {}

    @property
    def factory_address(self) -> ChecksumAddress:
        """Get the CLOB factory address from the router."""
        return self._clob_factory_address

    def get_market_info(self, clob: ICLOB) -> Market:
        # Get market config for additional details
        factory, mask, quote, base, tick_size, lot_size = clob.get_market_config()

        base_contract = ERC20(self._web3, base)
        quote_contract = ERC20(self._web3, quote)


        base_asset = Asset(
            address=base,
            decimals=base_contract.decimals(),
            name=base_contract.name(),
            symbol=base_contract.symbol(),
        )

        quote_asset = Asset(
            address=quote,
            decimals=quote_contract.decimals(),
            name=quote_contract.name(),
            symbol=quote_contract.symbol(),
        )

        # Create a market info object
        market_info = Market(
            address=clob.address,
            market_type=MarketType.CLOB,
            base_asset=base_asset,
            quote_asset=quote_asset,
            base_token_address=base,
            quote_token_address=quote,
            base_decimals=base_asset.decimals,
            quote_decimals=quote_asset.decimals,
            tick_size_in_quote=tick_size,
            tick_size=quote_contract.convert_amount_to_float(tick_size),
            lot_size_in_base=lot_size,
            lot_size=base_contract.convert_amount_to_float(lot_size),
        )

        return market_info

    def get_market_info_by_address(self, address: ChecksumAddress) -> Market:
        """Get market info by address."""
        iclob = ICLOB(self._web3, address)
        return self.get_market_info(iclob)
