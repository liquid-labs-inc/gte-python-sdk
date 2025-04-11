"""Python wrapper for the GTE CLOB Factory contract."""

import logging
from typing import List, Dict, Any, Optional
from web3 import Web3
from eth_typing import ChecksumAddress

from .utils import load_abi

logger = logging.getLogger(__name__)


class CLOBFactory:
    """
    Python wrapper for the GTE CLOB Factory contract.
    This contract manages the creation and registry of CLOB markets on the GTE platform.
    """
    
    def __init__(self, web3: Web3, contract_address: str, abi_path: Optional[str] = None, abi: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the CLOBFactory wrapper.
        
        Args:
            web3: Web3 instance connected to a provider
            contract_address: Address of the CLOBFactory contract
            abi_path: Path to the ABI JSON file (optional)
            abi: The contract ABI as a Python dictionary (optional)
        """
        self.web3 = web3
        self.address = web3.to_checksum_address(contract_address)
        
        # Use the provided ABI if given, otherwise load from path or use default
        if abi is not None:
            loaded_abi = abi
        elif abi_path is not None:
            loaded_abi = load_abi(abi_path)
        else:
            loaded_abi = load_abi('factory')
            
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)
    
    def get_owner(self) -> ChecksumAddress:
        """Get the owner of the factory."""
        return self.contract.functions.owner().call()
    
    def get_clob_count(self) -> int:
        """Get the total number of CLOB markets registered in the factory."""
        return self.contract.functions.getClobCount().call()
    
    def get_clob(self, index: int) -> ChecksumAddress:
        """
        Get the address of a CLOB market by index.
        
        Args:
            index: Index of the CLOB market
            
        Returns:
            Address of the CLOB market
        """
        return self.contract.functions.getClob(index).call()
    
    def get_all_clobs(self) -> List[ChecksumAddress]:
        """
        Get all CLOB market addresses registered in the factory.
        
        Returns:
            List of CLOB market addresses
        """
        count = self.get_clob_count()
        return [self.get_clob(i) for i in range(count)]
    
    def is_clob(self, address: str) -> bool:
        """
        Check if an address is a registered CLOB market.
        
        Args:
            address: Address to check
            
        Returns:
            True if the address is a registered CLOB market, False otherwise
        """
        address = self.web3.to_checksum_address(address)
        return self.contract.functions.isClob(address).call()
    
    def get_fee_recipient(self) -> ChecksumAddress:
        """Get the address that receives fees from CLOB markets."""
        return self.contract.functions.getFeeRecipient().call()
    
    def get_deployment_parameters(self) -> Dict[str, Any]:
        """
        Get the deployment parameters used for creating new CLOB markets.
        
        Returns:
            Dictionary containing deployment parameters
        """
        return self.contract.functions.getDeploymentParameters().call()
    
    def get_clob_implementation(self) -> ChecksumAddress:
        """Get the address of the CLOB implementation contract used for clones."""
        return self.contract.functions.getClobImplementation().call()
    
    # Admin functions that require owner privileges
    
    def create_clob(
        self, 
        base_token: str, 
        quote_token: str, 
        tick_size: int,
        step_size: int,
        maker_fee_rate: int,
        taker_fee_rate: int,
        sender_address: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new CLOB market.
        
        Args:
            base_token: Address of the base token
            quote_token: Address of the quote token
            tick_size: Minimum price movement in ticks
            step_size: Minimum size movement in base token atoms
            maker_fee_rate: Fee rate for makers in basis points (1% = 100)
            taker_fee_rate: Fee rate for takers in basis points (1% = 100)
            sender_address: Address of the transaction sender (must be factory owner)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction object
        """
        base_token = self.web3.to_checksum_address(base_token)
        quote_token = self.web3.to_checksum_address(quote_token)
        
        tx = self.contract.functions.createClob(
            base_token, 
            quote_token, 
            tick_size,
            step_size,
            maker_fee_rate,
            taker_fee_rate
        ).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def set_fee_recipient(self, new_recipient: str, sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Set the fee recipient address.
        
        Args:
            new_recipient: Address of the new fee recipient
            sender_address: Address of the transaction sender (must be factory owner)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction object
        """
        new_recipient = self.web3.to_checksum_address(new_recipient)
        
        tx = self.contract.functions.setFeeRecipient(new_recipient).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def transfer_ownership(self, new_owner: str, sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Transfer ownership of the factory to a new address.
        
        Args:
            new_owner: Address of the new owner
            sender_address: Address of the transaction sender (must be current factory owner)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction object
        """
        new_owner = self.web3.to_checksum_address(new_owner)
        
        tx = self.contract.functions.transferOwnership(new_owner).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def get_clob_by_tokens(self, base_token: str, quote_token: str) -> Optional[ChecksumAddress]:
        """
        Get the address of a CLOB market by its tokens.
        
        Args:
            base_token: Address of the base token
            quote_token: Address of the quote token
            
        Returns:
            Address of the CLOB market or None if not found
        """
        base_token = self.web3.to_checksum_address(base_token)
        quote_token = self.web3.to_checksum_address(quote_token)
        
        try:
            # This function may not exist in all factory implementations
            result = self.contract.functions.getClobByTokens(base_token, quote_token).call()
            return result if result != "0x0000000000000000000000000000000000000000" else None
        except Exception:
            # Fall back to scanning all CLOBs if the direct lookup function isn't available
            from .iclob import ICLOB
            
            for clob_address in self.get_all_clobs():
                try:
                    clob = ICLOB(web3=self.web3, contract_address=clob_address)
                    if (clob.get_base_token().lower() == base_token.lower() and
                        clob.get_quote_token().lower() == quote_token.lower()):
                        return clob_address
                except Exception as e:
                    logger.warning(f"Error checking CLOB {clob_address}: {str(e)}")
                    continue
            
            return None
