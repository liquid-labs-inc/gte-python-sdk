"""Python wrapper for WETH (Wrapped Ether) token contracts."""

from typing import TypeVar

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

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
        web3: AsyncWeb3,
        contract_address: ChecksumAddress,
    ):
        """
        Initialize the WETH wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the WETH token contract
        """
        super().__init__(web3, contract_address)
        
        # Override the ABI with WETH-specific ABI
        loaded_abi = load_abi("weth")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

    def deposit(
        self, 
        amount: int, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Deposit ETH to get WETH.
        
        Args:
            amount: Amount of ETH to wrap (in wei)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.deposit()
        params = {
            "value": amount,
            **kwargs,
        }
        return TypedContractFunction(func, params)
        
    def withdraw(
        self, 
        amount: int, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Withdraw ETH by unwrapping WETH.
        
        Args:
            amount: Amount of WETH to unwrap (in wei)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.withdraw(amount)
        

        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)
    
    def deposit_eth(
        self, 
        amount_eth: float, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Deposit ETH to get WETH, using ETH amount as float.
        
        Args:
            amount_eth: Amount of ETH to wrap (as a float, e.g., 1.5 ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Convert ETH amount to wei
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        return self.deposit(amount_wei, **kwargs)
    
    def withdraw_eth(
        self, 
        amount_eth: float, 
        **kwargs
    ) -> TypedContractFunction[None]:
        """
        Withdraw ETH by unwrapping WETH, using ETH amount as float.
        
        Args:
            amount_eth: Amount of WETH to unwrap (as a float, e.g., 1.5 ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        # Convert ETH amount to wei
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        return self.withdraw(amount_wei, **kwargs)
    
    async def deposit_eth_async(self, amount_eth: float, **kwargs) -> TypedContractFunction:
        """
        Wrap native ETH to WETH using async call.
        
        Args:
            amount_eth: Amount of ETH to wrap (as a float, e.g., 1.5 ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction for sending the transaction
        """
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        # Deposit() function is payable, so we need to send ETH with it
        func = self.contract.functions.deposit()
        params = {
            'value': amount_wei,
            **kwargs,
        }
        return TypedContractFunction(func, params)
        
    async def withdraw_eth_async(self, amount_eth: float, **kwargs) -> TypedContractFunction:
        """
        Unwrap WETH to native ETH using async call.
        
        Args:
            amount_eth: Amount of WETH to unwrap (as a float, e.g., 1.5 WETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            TypedContractFunction for sending the transaction
        """
        amount_wei = self.web3.to_wei(amount_eth, 'ether')
        func = self.contract.functions.withdraw(amount_wei)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)
