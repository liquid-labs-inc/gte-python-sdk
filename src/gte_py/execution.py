"""Order execution functionality for the GTE client."""

import logging
import time
from typing import Dict, Optional, Union, Any

from web3 import Web3
from .models import Market, Order
from .contracts.iclob import ICLOB, Side, LimitOrderType, FillOrderType, Settlement

logger = logging.getLogger(__name__)

class ExecutionClient:
    """Client for executing orders on the GTE exchange."""
    
    def __init__(self, web3: Optional[Web3] = None):
        """Initialize the execution client.
        
        Args:
            web3: Web3 instance for on-chain interactions
        """
        self._web3 = web3
        self._clob_clients = {}  # Cache for CLOB contract clients
    
    def set_web3(self, web3: Web3):
        """Set or update the Web3 provider.
        
        Args:
            web3: Web3 instance
        """
        self._web3 = web3
    
    def _get_clob(self, market_address: str, contract_address: str) -> ICLOB:
        """Get or create an ICLOB contract instance.
        
        Args:
            market_address: Market address (used as cache key)
            contract_address: CLOB contract address
            
        Returns:
            ICLOB contract instance
        
        Raises:
            ValueError: If Web3 is not configured
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot interact with contracts.")
            
        if market_address not in self._clob_clients:
            self._clob_clients[market_address] = ICLOB(
                web3=self._web3, 
                contract_address=contract_address
            )
        
        return self._clob_clients[market_address]
    
    async def create_order(
        self, 
        market: Market,
        side: str, 
        order_type: str, 
        amount: float, 
        price: Optional[float] = None, 
        time_in_force: str = "GTC", 
        sender_address: str = None,
        use_contract: bool = False, 
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
                
            # Get the CLOB contract for this market
            if not market.contract_address:
                raise ValueError(f"Market {market.address} has no contract address")
                
            clob = self._get_clob(market.address, market.contract_address)
            
            # Convert high-level parameters to contract-specific values
            side_value = Side.BUY if side.lower() == 'buy' else Side.SELL
            
            # Convert amount to base lots
            base_atoms_per_lot = market.base_atoms_per_lot
            amount_in_base_lots = int(amount * (10**market.base_decimals) / base_atoms_per_lot)
            
            # Convert price to ticks
            price_in_ticks = int(price * (10**market.tick_size_in_decimals))
            
            # Create the appropriate order based on type
            if order_type.lower() == 'limit':
                # Map time_in_force to LimitOrderType
                limit_type = LimitOrderType.GOOD_TILL_CANCELLED  # Default
                if time_in_force == 'IOC':
                    limit_type = LimitOrderType.IMMEDIATE_OR_CANCEL
                elif time_in_force == 'FOK':
                    limit_type = LimitOrderType.FILL_OR_KILL
                
                # Create limit order arguments
                limit_args = clob.create_post_limit_order_args(
                    amount_in_base_lots=amount_in_base_lots,
                    price_in_ticks=price_in_ticks,
                    side=side_value,
                    limit_order_type=limit_type
                )
                
                # Create and return transaction
                return clob.post_limit_order(
                    args=limit_args,
                    sender_address=sender_address,
                    **tx_kwargs
                )
            else:  # Market order
                # Create fill order arguments
                fill_args = clob.create_post_fill_order_args(
                    amount_in_base_lots=amount_in_base_lots,
                    price_in_ticks=price_in_ticks,  # Limit price for market orders
                    side=side_value,
                    fill_order_type=FillOrderType.IMMEDIATE_OR_CANCEL
                )
                
                # Create and return transaction
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
                "marketAddress": market.address,
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
            
    def cancel_order(
        self, 
        market: Market, 
        order_id: int, 
        sender_address: str, 
        **tx_kwargs
    ) -> Dict[str, Any]:
        """Cancel an order.
        
        Args:
            market: Market object with details
            order_id: ID of the order to cancel
            sender_address: Address to send transaction from
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction data
            
        Raises:
            ValueError: If Web3 is not configured or parameters are invalid
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot cancel on-chain orders.")
        
        if not market.contract_address:
            raise ValueError(f"Market {market.address} has no contract address")
        
        clob = self._get_clob(market.address, market.contract_address)
        
        cancel_args = clob.create_cancel_args(
            order_ids=[order_id],
            settlement=Settlement.INSTANT
        )
        
        return clob.cancel(
            args=cancel_args,
            sender_address=sender_address,
            **tx_kwargs
        )
        
    def modify_order(
        self, 
        market: Market, 
        order_id: int,
        new_amount: float, 
        sender_address: str, 
        **tx_kwargs
    ) -> Dict[str, Any]:
        """Modify an existing order's amount (reduce only).
        
        Args:
            market: Market object with details
            order_id: ID of the order to modify
            new_amount: New amount for the order (must be less than current)
            sender_address: Address to send transaction from
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction data
            
        Raises:
            ValueError: If Web3 is not configured or parameters are invalid
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot modify on-chain orders.")
        
        if not market.contract_address:
            raise ValueError(f"Market {market.address} has no contract address")
        
        clob = self._get_clob(market.address, market.contract_address)
        
        # Convert amount to base lots
        base_atoms_per_lot = market.base_atoms_per_lot
        amount_in_base_lots = int(new_amount * (10**market.base_decimals) / base_atoms_per_lot)
        
        reduce_args = clob.create_reduce_args(
            order_id=order_id,
            amount_in_base_lots=amount_in_base_lots
        )
        
        return clob.reduce(
            args=reduce_args,
            sender_address=sender_address,
            **tx_kwargs
        )
