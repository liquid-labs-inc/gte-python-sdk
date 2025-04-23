"""Python wrapper for WETH (Wrapped Ether) token contracts."""

from typing import TypeVar, Optional, Dict, Any

from eth_typing import ChecksumAddress
from web3 import Web3

from .erc20 import ERC20
from .utils import TypedContractFunction, load_abi

T = TypeVar("T")


class WETH(ERC20):
    """
    Python wrapper for WETH (Wrapped Ether) token contracts.
    Extends the ERC20 wrapper to add WETH-specific functionality:
    - deposit: Convert ETH to WETH
    - withdraw: Convert WETH back to ETH
    """

    def __init__(
        self,
        web3: Web3,
        contract_address: ChecksumAddress,
    ):
        """
        Initialize the WETH wrapper.

        Args:
            web3: Web3 instance connected to a provider
            contract_address: Address of the WETH token contract
        """
        super().__init__(web3, contract_address)
        
        # Override the ABI with WETH-specific ABI
        loaded_abi = load_abi("weth")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

    def deposit(
        self, 
        amount: int, 
        sender_address: ChecksumAddress, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Deposit ETH to get WETH.
        
        Args:
            amount: Amount of ETH to wrap (in wei)
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.deposit()
        params = {
            "from": sender_address,
            "value": amount,
            **kwargs,
        }
        return TypedContractFunction(func, params)
        
    def withdraw(
        self, 
        amount: int, 
        sender_address: ChecksumAddress, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Withdraw ETH by unwrapping WETH.
        
        Args:
            amount: Amount of WETH to unwrap (in wei)
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.withdraw(amount)
        
        # Ensure we have a nonce
        if 'nonce' not in kwargs:
            kwargs['nonce'] = self.web3.eth.get_transaction_count(sender_address)
            
        params = {
            "from": sender_address,
            **kwargs,
        }
        return TypedContractFunction(func, params)
    
    def deposit_eth(
        self, 
        amount_eth: float, 
        sender_address: ChecksumAddress, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Deposit ETH to get WETH, using ETH amount as float.
        
        Args:
            amount_eth: Amount of ETH to wrap (as a float, e.g., 1.5 ETH)
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Convert ETH amount to wei
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        return self.deposit(amount_wei, sender_address, **kwargs)
    
    def withdraw_eth(
        self, 
        amount_eth: float, 
        sender_address: ChecksumAddress, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Withdraw ETH by unwrapping WETH, using ETH amount as float.
        
        Args:
            amount_eth: Amount of WETH to unwrap (as a float, e.g., 1.5 ETH)
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Convert ETH amount to wei
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        return self.withdraw(amount_wei, sender_address, **kwargs)
