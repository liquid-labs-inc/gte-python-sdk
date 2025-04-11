"""Market information service for GTE."""

import logging
from typing import Dict, List, Optional, Any, Set
from web3 import Web3

from .models import Market, MarketInfo
from .contracts.router import GTERouter

logger = logging.getLogger(__name__)

class MarketInfoService:
    """Service for retrieving market information from the blockchain."""
    
    def __init__(self, web3: Web3, router_address: str):
        """Initialize the market info service.
        
        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        self.router_address = self._web3.to_checksum_address(router_address)
        self.router = GTERouter(web3=web3, contract_address=self.router_address)
        
        # Cache of discovered markets
        self._markets: Dict[str, MarketInfo] = {}
        self._clob_factory_address = None
    
    def get_factory_address(self) -> str:
        """Get the CLOB factory address from the router.
        
        Returns:
            The CLOB factory address
        """
        if not self._clob_factory_address:
            self._clob_factory_address = self.router.get_clob_factory()
        return self._clob_factory_address
    
    def get_available_markets(self) -> List[MarketInfo]:
        """Get all available markets registered with the router.
        
        This would typically query the factory to get all registered CLOBs
        and their associated markets.
        
        Returns:
            List of market information
        """
        # In a full implementation, we would:
        # 1. Query the CLOB factory for all registered CLOBs
        # 2. For each CLOB, get base/quote tokens and other market info
        # 3. Format into MarketInfo objects
        
        # For now, returning cached markets or empty list
        return list(self._markets.values())
    
    def add_market_info(self, market_info: MarketInfo):
        """Add market information to the cache.
        
        Args:
            market_info: Market information to add
        """
        self._markets[market_info.address] = market_info
    
    def get_market_info(self, market_address: str) -> Optional[MarketInfo]:
        """Get market information for a specific market.
        
        Args:
            market_address: Market address
        
        Returns:
            Market information or None if not found
        """
        # Try to get from cache
        if market_address in self._markets:
            return self._markets[market_address]
        
        # Not in cache, would need to query on-chain
        # In a full implementation, we would query the contract here
        return None
    
    def update_market_cache(self, api_markets: List[Market]):
        """Update the market cache with information from API markets.
        
        Args:
            api_markets: List of markets from the API
        """
        for market in api_markets:
            # Only cache markets that have a contract address
            if market.contract_address:
                market_info = MarketInfo(
                    address=market.address,
                    contract_address=market.contract_address,
                    base_token=market.base_token_address,
                    quote_token=market.quote_token_address,
                    base_decimals=market.base_decimals,
                    quote_decimals=market.quote_decimals,
                    tick_size=market.tick_size, 
                    base_atoms_per_lot=market.base_atoms_per_lot,
                    tick_size_in_decimals=market.tick_size_in_decimals
                )
                self._markets[market.address] = market_info
