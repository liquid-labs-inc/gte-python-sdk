"""Order execution functionality for the GTE client."""

import logging
import time
from typing import Dict, Optional, Union, Any

from web3 import Web3
from .models import Market, MarketInfo, Order, OrderSide, OrderType, TimeInForce
from .contracts.iclob import ICLOB
from .contracts.router import Router
from .contracts.structs import Side, LimitOrderType, FillOrderType, Settlement
from .contracts.structs import ICLOBPostLimitOrderArgs, ICLOBPostFillOrderArgs, ICLOBCancelArgs, ICLOBReduceArgs
from .info import MarketInfoService

logger = logging.getLogger(__name__)


class ExecutionClient:
    """Client for executing orders on the GTE exchange."""
    
    def __init__(self, web3: Optional[Web3] = None, router_address: Optional[str] = None):
        """
        Initialize the execution client.
        
        Args:
            web3: Web3 instance for on-chain interactions
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        self._clob_clients: Dict[str, ICLOB] = {}
        self._router: Optional[Router] = None
        self._market_info: Optional[MarketInfoService] = None
        
        if web3 and router_address:
            self.setup_contracts(web3, router_address)
    
    def setup_contracts(self, web3: Web3, router_address: str) -> None:
        """
        Set up the contracts.
        
        Args:
            web3: Web3 instance
            router_address: Address of the GTE Router contract
        """
        self._web3 = web3
        router_address = web3.to_checksum_address(router_address)
        
        # Create router and market info service
        self._router = Router(web3=web3, contract_address=router_address)
        self._market_info = MarketInfoService(web3=web3, router_address=router_address)
    
    def _get_clob(self, contract_address: str) -> ICLOB:
        """
        Get or create an ICLOB contract instance.
        
        Args:
            contract_address: CLOB contract address
            
        Returns:
            ICLOB contract instance
        
        Raises:
            ValueError: If Web3 is not configured
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot interact with contracts.")
            
        contract_address = self._web3.to_checksum_address(contract_address)
        
        if contract_address not in self._clob_clients:
            self._clob_clients[contract_address] = ICLOB(
                web3=self._web3, 
                contract_address=contract_address
            )
        
        return self._clob_clients[contract_address]
    
    def _map_order_params_to_contract_args(
        self, 
        market: Union[Market, MarketInfo],
        side: OrderSide, 
        order_type: OrderType,
        amount: float,
        price: float,
        time_in_force: TimeInForce
    ) -> Dict[str, Any]:
        """
        Map order parameters to contract arguments.
        
        Args:
            market: Market or MarketInfo object
            side: Order side
            order_type: Order type
            amount: Order amount
            price: Order price
            time_in_force: Time in force
            
        Returns:
            Dictionary with contract arguments
        """
        # Get market parameters
        base_decimals = getattr(market, 'base_decimals', 18)
        tick_size_in_decimals = getattr(market, 'tick_size_in_decimals', 6)
        base_atoms_per_lot = getattr(market, 'base_atoms_per_lot', 1)
        
        # Map order side
        side_value = Side.BUY if side == OrderSide.BUY else Side.SELL
        
        # Convert amount to base lots
        amount_in_base_lots = int(amount * (10**base_decimals) / base_atoms_per_lot)
        
        # Convert price to ticks
        price_in_ticks = int(price * (10**tick_size_in_decimals))
        
        # Map time in force
        if order_type == OrderType.LIMIT:
            # Map time_in_force to LimitOrderType
            limit_type = LimitOrderType.GOOD_TILL_CANCELLED  # Default
            if time_in_force == TimeInForce.IOC:
                limit_type = LimitOrderType.IMMEDIATE_OR_CANCEL
            elif time_in_force == TimeInForce.FOK:
                limit_type = LimitOrderType.FILL_OR_KILL
                
            return {
                "amount_in_base_lots": amount_in_base_lots,
                "price_in_ticks": price_in_ticks,
                "side_value": side_value,
                "limit_type": limit_type
            }
        else:  # Market order
            return {
                "amount_in_base_lots": amount_in_base_lots,
                "price_in_ticks": price_in_ticks,
                "side_value": side_value,
                "fill_type": FillOrderType.IMMEDIATE_OR_CANCEL
            }
    
    async def create_order(
        self, 
        market: Union[Market, MarketInfo],
        side: OrderSide, 
        order_type: OrderType, 
        amount: float, 
        price: Optional[float] = None, 
        time_in_force: TimeInForce = TimeInForce.GTC, 
        sender_address: Optional[str] = None,
        use_contract: bool = False,
        use_router: bool = True,
        **tx_kwargs
    ) -> Union[Order, Dict[str, Any]]:
        """
        Create a new order.

        Args:
            market: Market object with details
            side: Order side
            order_type: Order type
            amount: Order amount
            price: Order price (required for limit orders)
            time_in_force: Time in force
            sender_address: Address to send transaction from (required for on-chain orders)
            use_contract: Whether to create the order on-chain using contracts
            use_router: Whether to use the router for creating orders (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Created order information or transaction data when using contracts
            
        Raises:
            ValueError: For missing required parameters or invalid input
        """
        logger.info(f"Creating {order_type.value} {side.value} order for {amount} at price {price}")
        
        # Handle on-chain order creation via contract
        if use_contract:
            if not self._web3:
                raise ValueError("Web3 provider not configured. Cannot create on-chain orders.")
                
            if not sender_address:
                raise ValueError("sender_address is required for on-chain orders")
                
            if not price and order_type == OrderType.LIMIT:
                raise ValueError("Price is required for limit orders")
                
            if not price:
                raise ValueError("Price is required for on-chain orders")
            
            # Get contract address
            contract_address = getattr(market, 'contract_address', None)
            if not contract_address:
                raise ValueError(f"Market has no contract address")
                
            # Get mapped contract parameters
            params = self._map_order_params_to_contract_args(
                market=market,
                side=side,
                order_type=order_type,
                amount=amount,
                price=price,
                time_in_force=time_in_force
            )
            
            # Create the appropriate order based on type and use router or direct contract
            if order_type == OrderType.LIMIT:
                # Create limit order arguments
                limit_args = ICLOBPostLimitOrderArgs(
                    amountInBaseLots=params["amount_in_base_lots"],
                    priceInTicks=params["price_in_ticks"],
                    cancelTimestamp=0,
                    side=params["side_value"],
                    limitOrderType=params["limit_type"],
                    settlement=Settlement.INSTANT
                )
                
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
                fill_args = ICLOBPostFillOrderArgs(
                    amountInBaseLots=params["amount_in_base_lots"],
                    priceInTicks=params["price_in_ticks"],
                    side=params["side_value"],
                    fillOrderType=params["fill_type"],
                    settlement=Settlement.INSTANT
                )
                
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
            market_address = getattr(market, 'address', str(market))
            
            return Order.from_api({
                "id": f"placeholder-{int(time.time())}",
                "marketAddress": market_address,
                "side": side.value,
                "type": order_type.value,
                "amount": amount,
                "price": price,
                "timeInForce": time_in_force.value,
                "status": "open",
                "filledAmount": 0.0,
                "filledPrice": 0.0,
                "createdAt": int(time.time() * 1000),
            })
    
    def cancel_order(
        self, 
        market: Union[Market, MarketInfo], 
        order_id: int, 
        sender_address: str,
        use_router: bool = True,
        **tx_kwargs
    ) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            market: Market object with details
            order_id: ID of the order to cancel
            sender_address: Address to send transaction from
            use_router: Whether to use the router for cancellation (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction data
            
        Raises:
            ValueError: If Web3 is not configured or parameters are invalid
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot cancel on-chain orders.")
        
        contract_address = getattr(market, 'contract_address', None)
        if not contract_address:
            raise ValueError(f"Market has no contract address")
        
        # Create cancel arguments
        cancel_args = ICLOBCancelArgs(
            orderIds=[order_id],
            settlement=Settlement.INSTANT
        )
        
        # Use router or direct contract
        if use_router and self._router:
            return self._router.clob_cancel(
                clob_address=contract_address,
                args=cancel_args,
                sender_address=sender_address,
                **tx_kwargs
            )
        else:
            clob = self._get_clob(contract_address)
            return clob.cancel(
                args=cancel_args,
                sender_address=sender_address,
                **tx_kwargs
            )
        
    def modify_order(
        self, 
        market: Union[Market, MarketInfo], 
        order_id: int,
        new_amount: float, 
        sender_address: str,
        use_router: bool = True,
        **tx_kwargs
    ) -> Dict[str, Any]:
        """
        Modify an existing order's amount (reduce only).
        
        Args:
            market: Market object with details
            order_id: ID of the order to modify
            new_amount: New amount for the order (must be less than current)
            sender_address: Address to send transaction from
            use_router: Whether to use the router for modification (safer)
            **tx_kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction data
            
        Raises:
            ValueError: If Web3 is not configured or parameters are invalid
        """
        if not self._web3:
            raise ValueError("Web3 provider not configured. Cannot modify on-chain orders.")
        
        contract_address = getattr(market, 'contract_address', None)
        if not contract_address:
            raise ValueError(f"Market has no contract address")
        
        # Convert amount to base lots
        base_decimals = getattr(market, 'base_decimals', 18)
        base_atoms_per_lot = getattr(market, 'base_atoms_per_lot', 1)
        amount_in_base_lots = int(new_amount * (10**base_decimals) / base_atoms_per_lot)
        
        # Create reduce arguments
        reduce_args = ICLOBReduceArgs(
            orderId=order_id,
            amountInBaseLots=amount_in_base_lots,
            settlement=Settlement.INSTANT
        )
        
        # Use direct contract - router doesn't support reduce
        clob = self._get_clob(contract_address)
        return clob.reduce(
            args=reduce_args,
            sender_address=sender_address,
            **tx_kwargs
        )
