"""Order execution functionality for the GTE client."""

import logging
import time
from typing import Dict, Optional, Union, Any

from web3 import Web3
from .models import Market, MarketInfo, Order
from .contracts.iclob import ICLOB, Side, LimitOrderType, FillOrderType, Settlement
from .contracts.router import GTERouter
from .info import MarketInfoService

logger = logging.getLogger(__name__)

class ExecutionClient:
    """Client for executing orders on the GTE exchange."""
    
    def __init__(self, web3: Optional[Web3] = None, router_address: Optional[str] = None):
        """Initialize the execution client.
        
        Args:
            web3: Web3 instance for on-chain interactions
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        self._clob_clients = {}  # Cache for CLOB contract clients
        self._router = None
        self._market_info = None
        
        if web3 and router_address:
            self.setup_contracts(web3, router_address)
    
    def setup_contracts(self, web3: Web3, router_address: str):
        """Set up the contracts.
        
        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        router_address = web3.to_checksum_address(router_address)
        
        # Create router and market info service
        self._router = GTERouter(web3=web3, contract_address=router_address)
        self._market_info = MarketInfoService(web3=web3, router_address=router_address)
    
    def set_web3(self, web3: Web3, router_address: Optional[str] = None):
        """Set or update the Web3 provider.
        
        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract (optional)
        """
        self._web3 = web3
        
        # If router address provided, update the router and market info service
        if router_address:
            self.setup_contracts(web3, router_address)
    
    def _get_clob(self, contract_address: str) -> ICLOB:
        """Get or create an ICLOB contract instance.
        
        Args:
            contract_address: CLOB contract address
            
        Returns:
            ICLOB contract instance
        
        Raises:
            ValueError: If Web3 is not configured
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot interact with contracts.")
            
        if contract_address not in self._clob_clients:
            self._clob_clients[contract_address] = ICLOB(
                web3=self._web3, 
                contract_address=contract_address
            )
        
        return self._clob_clients[contract_address]
    
    def update_market_info(self, market: Market):
        """Update market info cache with data from a market.
        
        Args:
            market: Market object with details
        """
        if self._market_info and market.contract_address:
            market_info = MarketInfo.from_market(market)
            self._market_info.add_market_info(market_info)
    
    async def create_order(
        self, 
        market: Union[Market, MarketInfo],
        side: str, 
        order_type: str, 
        amount: float, 
        price: Optional[float] = None, 
        time_in_force: str = "GTC", 
        sender_address: str = None,
        use_contract: bool = False,
        use_router: bool = False,
        **tx_kwargs
    ) -> Union[Order, Dict[str, Any]]:
        """Create a new order.

        Args:
            market: Market object with details
            side: Order side (buy, sell)
            order_type: Order type (limit, market)
            amount: Order amount
            price: Order price (required for limit orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            sender_address: Address to send transaction from (required for on-chain orders)
            use_contract: Whether to create the order on-chain using contracts
            use_router: Whether to use the router for creating orders (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Created order information or transaction data when using contracts
            
        Raises:
            ValueError: For missing required parameters or invalid input
        """
        logger.info(f"Creating {order_type} {side} order for {amount} at price {price}")
        
        # Handle on-chain order creation via contract
        if use_contract:
            if not self._web3:
                raise ValueError("Web3 provider not configured. Cannot create on-chain orders.")
                
            if not sender_address:
                raise ValueError("sender_address is required for on-chain orders")
                
            if not price and order_type.lower() == 'limit':
                raise ValueError("Price is required for limit orders")
            
            # Get contract address
            contract_address = getattr(market, 'contract_address', None)
            if not contract_address:
                raise ValueError(f"Market has no contract address")
                
            # Update market info cache if this is a Market object
            if isinstance(market, Market):
                self.update_market_info(market)
            
            # Convert values from market
            base_decimals = getattr(market, 'base_decimals', 18)
            tick_size_in_decimals = getattr(market, 'tick_size_in_decimals', 6)
            base_atoms_per_lot = getattr(market, 'base_atoms_per_lot', 1)
            
            # Convert high-level parameters to contract-specific values
            side_value = Side.BUY if side.lower() == 'buy' else Side.SELL
            
            # Convert amount to base lots
            amount_in_base_lots = int(amount * (10**base_decimals) / base_atoms_per_lot)
            
            # Convert price to ticks
            price_in_ticks = int(price * (10**tick_size_in_decimals))
            
            # Create the appropriate order based on type and use router or direct contract
            if order_type.lower() == 'limit':
                # Map time_in_force to LimitOrderType
                limit_type = LimitOrderType.GOOD_TILL_CANCELLED  # Default
                if time_in_force == 'IOC':
                    limit_type = LimitOrderType.IMMEDIATE_OR_CANCEL
                elif time_in_force == 'FOK':
                    limit_type = LimitOrderType.FILL_OR_KILL
                
                # Create limit order arguments
                limit_args = {
                    'amountInBaseLots': amount_in_base_lots,
                    'priceInTicks': price_in_ticks,
                    'cancelTimestamp': 0,
                    'side': side_value,
                    'limitOrderType': limit_type,
                    'settlement': Settlement.INSTANT
                }
                
                # Use router or direct CLOB contract
                if use_router and self._router:
                    return self._router.clob_post_limit_order(
                        clob_address=contract_address,
                        args=limit_args,
                        sender_address=sender_address,
                        **tx_kwargs
                    )
                else:
                    # Use direct CLOB contract
                    clob = self._get_clob(contract_address)
                    return clob.post_limit_order(
                        args=limit_args,
                        sender_address=sender_address,
                        **tx_kwargs
                    )
            else:  # Market order
                # Create fill order arguments
                fill_args = {
                    'amountInBaseLots': amount_in_base_lots,
                    'priceInTicks': price_in_ticks,  # Limit price for market orders
                    'side': side_value,
                    'fillOrderType': FillOrderType.IMMEDIATE_OR_CANCEL,
                    'settlement': Settlement.INSTANT
                }
                
                # Use router or direct CLOB contract
                if use_router and self._router:
                    return self._router.execute_clob_post_fill_order(
                        clob_address=contract_address,
                        args=fill_args,
                        sender_address=sender_address,
                        **tx_kwargs
                    )
                else:
                    # Use direct CLOB contract
                    clob = self._get_clob(contract_address)
                    return clob.post_fill_order(
                        args=fill_args,
                        sender_address=sender_address,
                        **tx_kwargs
                    )
        else:
            # This is just a placeholder response for the REST API implementation
            # In a real implementation, we would call the API and get order details
            order_data = {
                "id": f"placeholder-{int(time.time())}",
                "marketAddress": getattr(market, 'address', str(market)),
                "side": side,
                "type": order_type,
                "amount": amount,
                "price": price,
                "timeInForce": time_in_force,
                "status": "open",
                "filledAmount": 0.0,
                "filledPrice": 0.0,
                "createdAt": int(time.time() * 1000),
            }
            
            return Order.from_api(order_data)
    
    # ...existing methods with similar router/direct contract logic...
