"""Perp order execution functionality for the GTE client."""

import logging
from typing import Optional, Any

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.chain.token_client import TokenClient

logger = logging.getLogger(__name__)

from gte_py.api.chain.perp_manager import PerpManager, PostLimitOrderArgs, PostFillOrderArgs

class PerpExecutionClient:
    """Client for executing perp orders and managing deposits/withdrawals on the GTE exchange."""

    def __init__(self, web3: AsyncWeb3, main_account: ChecksumAddress, perp_manager_address: Optional[ChecksumAddress] = None):
        self._web3 = web3
        self.main_account = main_account
        self._perp_manager_address = perp_manager_address
        self._perp_manager = PerpManager(web3, perp_manager_address) if perp_manager_address else None
        self._token_client = TokenClient(web3)

    async def init(self):
        """Initialize the perp manager if needed."""
        pass  # No initialization needed for now

    # ================= COLLATERAL OPERATIONS =================

    async def deposit_collateral(self, amount: int, **kwargs) -> Any:
        """
        Deposit collateral into the perp system for margin trading.
        
        Args:
            amount: Amount to deposit in base units
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction result from the deposit operation
        """
        if not self._perp_manager:
            raise ValueError("Perp manager address is required for perp operations")
        
        tx = self._perp_manager.deposit_collateral(
            account=self.main_account, 
            amount=amount, 
            **kwargs
        )
        return await tx.send_wait()
    
    async def withdraw_collateral(self, amount: int, **kwargs) -> Any:
        """
        Withdraw collateral from the perp system.
        
        Args:
            amount: Amount to withdraw in base units
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction result from the withdrawal operation
        """
        if not self._perp_manager:
            raise ValueError("Perp manager address is required for perp operations")
        
        tx = self._perp_manager.withdraw_collateral(
            account=self.main_account, 
            amount=amount, 
            **kwargs
        )
        return await tx.send_wait()

    # ================= ORDER OPERATIONS =================

    async def place_limit_order(self, asset: str, args: PostLimitOrderArgs, settlement: int = 0, **kwargs) -> Any:
        """
        Place a perp limit order.
        
        Args:
            asset: Asset to trade
            args: Order arguments 
            settlement: Settlement type
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction result with the order details
        """
        if not self._perp_manager:
            raise ValueError("Perp manager address is required for perp operations")
        tx = self._perp_manager.post_limit_order(self.main_account, args, settlement, **kwargs)
        return await tx.send_wait()

    async def place_fill_order(self, asset: str, args: PostFillOrderArgs, settlement: int = 0, **kwargs) -> Any:
        """
        Place a perp fill order (market order).
        
        Args:
            asset: Asset to trade
            args: Order arguments
            settlement: Settlement type
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction result with the order details
        """
        if not self._perp_manager:
            raise ValueError("Perp manager address is required for perp operations")
        tx = self._perp_manager.post_fill_order(self.main_account, args, settlement, **kwargs)
        return await tx.send_wait()

    async def cancel_orders(self, asset: str, subaccount: int, order_ids: list[int], settlement: int = 0, **kwargs) -> Any:
        """
        Cancel perp orders by order_ids.
        
        Args:
            asset: Asset the orders belong to
            subaccount: Subaccount ID
            order_ids: List of order IDs to cancel
            settlement: Settlement type
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction result from the cancellation operation
        """
        if not self._perp_manager:
            raise ValueError("Perp manager address is required for perp operations")
        tx = self._perp_manager.cancel_limit_orders(asset, self.main_account, subaccount, order_ids, settlement, **kwargs)
        return await tx.send_wait()
