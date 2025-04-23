"""Market information service for GTE."""

import logging

from eth_typing import ChecksumAddress
from web3 import Web3

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
        base_token_address: ChecksumAddress = clob.get_base_token()
        quote_token_address: ChecksumAddress = clob.get_quote_token()

        # Get market config for additional details
        factory, mask, quote, base, tick_size, lot_size = clob.get_market_config()

        # TODO: use ERC20 to get decimals, name, symbol
        # Create basic asset objects with addresses
        base_asset = Asset(
            address=base,
            decimals=18,
            name="",  # To be filled later
            symbol="",  # To be filled later
        )

        quote_asset = Asset(
            address=quote,
            decimals=18,
            name="",  # To be filled later
            symbol="",  # To be filled later
        )

        # Create a market info object
        market_info = Market(
            address=clob.address,
            market_type=MarketType.CLOB,
            base_asset=base_asset,
            quote_asset=quote_asset,
            base_token_address=base_token_address,
            quote_token_address=quote_token_address,
            base_decimals=18,
            quote_decimals=18,
            tick_size=tick_size,
            lot_size=lot_size,
        )

        return market_info

    def get_market_info_by_address(self, address: ChecksumAddress) -> Market:
        """Get market info by address."""
        iclob = ICLOB(self._web3, address)
        return self.get_market_info(iclob)
