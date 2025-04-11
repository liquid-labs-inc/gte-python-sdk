"""Market information service for GTE."""

import logging
from typing import Dict, List, Optional, Any, Set
from web3 import Web3

from .models import Market, MarketInfo
from .contracts.router import Router
from .contracts.factory import CLOBFactory

logger = logging.getLogger(__name__)


class MarketInfoService:
    """Service for retrieving market information from the blockchain."""
    
    def __init__(self, web3: Web3, router_address: str):
        """
        Initialize the market info service.
        
        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        self.router_address = web3.to_checksum_address(router_address)
        self.router = Router(web3=web3, contract_address=self.router_address)
        
        # Get and initialize CLOB factory
        self._clob_factory_address = self.router.get_clob_factory()
        self._clob_factory = CLOBFactory(web3=web3, contract_address=self._clob_factory_address)
        
        # Cache of discovered markets
        self._markets: Dict[str, MarketInfo] = {}
    
    @property
    def factory_address(self) -> str:
        """Get the CLOB factory address from the router."""
        return self._clob_factory_address
    
    def refresh_markets_from_chain(self) -> List[MarketInfo]:
        """
        Get all available markets registered with the router from chain.
        
        Returns:
            List of market information
        """
        markets = []
        clob_count = self._clob_factory.get_clob_count()
        
        for i in range(clob_count):
            clob_address = self._clob_factory.get_clob(i)
            if not clob_address:
                continue
            
            try:
                # Get market details directly from the CLOB contract
                from .contracts.iclob import ICLOB
                clob = ICLOB(web3=self._web3, contract_address=clob_address)
                
                base_token = clob.get_base_token()
                quote_token = clob.get_quote_token()
                
                # Get market config for additional details
                market_config = clob.get_market_config()
                token_config = clob.get_token_config()
                
                # Create a market info object
                market_info = MarketInfo(
                    address=f"market-{clob_address}",  # Generate a virtual market address
                    contract_address=clob_address,
                    base_token=base_token,
                    quote_token=quote_token,
                    base_decimals=token_config.get('baseDecimals', 18),
                    quote_decimals=token_config.get('quoteDecimals', 18),
                    tick_size=market_config.get('tickSize', 0.01),
                    base_atoms_per_lot=market_config.get('baseAtomsPerLot', 1),
                    tick_size_in_decimals=market_config.get('tickSizeInDecimals', 2)
                )
                
                self._markets[market_info.address] = market_info
                markets.append(market_info)
                
            except Exception as e:
                logger.error(f"Error getting details for CLOB {clob_address}: {e}")
                continue
                
        return markets
    
    def get_available_markets(self) -> List[MarketInfo]:
        """
        Get all available markets from cache or by querying the chain.
        
        Returns:
            List of market information
        """
        if not self._markets:
            return self.refresh_markets_from_chain()
        return list(self._markets.values())
    
    def add_market_info(self, market_info: MarketInfo) -> None:
        """
        Add market information to the cache.
        
        Args:
            market_info: Market information to add
        """
        self._markets[market_info.address] = market_info
    
    def get_market_info(self, market_address: str) -> Optional[MarketInfo]:
        """
        Get market information for a specific market.
        
        Args:
            market_address: Market address
        
        Returns:
            Market information or None if not found
        """
        # Try to get from cache
        if market_address in self._markets:
            return self._markets[market_address]
        
        # Not in cache, check for contract-based lookup
        if market_address.startswith("0x"):
            # Look up by contract address
            for market_info in self._markets.values():
                if market_info.contract_address.lower() == market_address.lower():
                    return market_info
        
        # Still not found - market might not be registered yet
        return None
    
    def update_market_cache(self, api_markets: List[Market]) -> None:
        """
        Update the market cache with information from API markets.
        
        Args:
            api_markets: List of markets from the API
        """
        for market in api_markets:
            # Only cache markets that have a contract address
            if market.contract_address:
                market_info = MarketInfo.from_market(market)
                self._markets[market_info.address] = market_info
