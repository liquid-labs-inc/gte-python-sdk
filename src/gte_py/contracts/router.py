from typing import List, Dict, Any, Optional

from eth_typing import ChecksumAddress
from web3 import Web3

from .utils import load_abi


class Settlement:
    """Enum for CLOB settlement options"""
    NONE = 0
    WRAP = 1
    UNWRAP = 2

class Router:
    """
    Python wrapper for the GTERouter smart contract.
    Provides methods to interact with the GTERouter functionality including:
    - CLOB interactions
    - Launchpad operations
    - Route execution
    - UniV2 swaps
    """
    
    def __init__(self, web3: Web3, contract_address: str, abi_path: Optional[str] = None, abi: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the GTERouter wrapper.
        
        Args:
            web3: Web3 instance connected to a provider
            contract_address: Address of the GTERouter contract
            abi_path: Path to the ABI JSON file (optional)
            abi: The contract ABI as a Python dictionary (optional)
        """
        self.web3 = web3
        self.address = web3.to_checksum_address(contract_address)
        
        # Use the ABI provided directly, or load it from the path, or use the default name
        if abi is not None:
            loaded_abi = abi
        elif abi_path is not None:
            loaded_abi = load_abi(abi_path)
        else:
            loaded_abi = load_abi('router')
            
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)
    
    # ================= READ METHODS =================
    
    def get_weth(self) -> ChecksumAddress:
        """Get the WETH contract address."""
        return self.contract.functions.weth().call()
    
    def get_launchpad(self) -> ChecksumAddress:
        """Get the Launchpad contract address."""
        return self.contract.functions.launchpad().call()
    
    def get_clob_factory(self) -> ChecksumAddress:
        """Get the CLOB factory contract address."""
        return self.contract.functions.clobFactory().call()
    
    def get_univ2_router(self) -> ChecksumAddress:
        """Get the UniswapV2 Router contract address."""
        return self.contract.functions.uniV2Router().call()
    
    def get_permit2(self) -> ChecksumAddress:
        """Get the Permit2 contract address."""
        return self.contract.functions.permit2().call()
    
    # ================= WRITE METHODS =================
    
    def clob_cancel(self, clob_address: str, args: Dict[str, Any], sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Cancel a CLOB order.
        
        Args:
            clob_address: Address of the CLOB contract
            args: CancelArgs struct from the CLOB interface
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        clob_address = self.web3.to_checksum_address(clob_address)
        tx = self.contract.functions.clobCancel(clob_address, args).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def clob_deposit(self, token_address: str, amount: int, from_router: bool, sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Deposit tokens into a CLOB.
        
        Args:
            token_address: Address of the token to deposit
            amount: Amount of tokens to deposit
            from_router: Whether the deposit is from the router
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        token_address = self.web3.to_checksum_address(token_address)
        tx = self.contract.functions.clobDeposit(token_address, amount, from_router).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def clob_post_limit_order(self, clob_address: str, args: Dict[str, Any], sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Post a limit order to a CLOB.
        
        Args:
            clob_address: Address of the CLOB contract
            args: PostLimitOrderArgs struct from the CLOB interface
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        clob_address = self.web3.to_checksum_address(clob_address)
        tx = self.contract.functions.clobPostLimitOrder(clob_address, args).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def clob_withdraw(self, token_address: str, amount: int, sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Withdraw tokens from a CLOB.
        
        Args:
            token_address: Address of the token to withdraw
            amount: Amount of tokens to withdraw
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        token_address = self.web3.to_checksum_address(token_address)
        tx = self.contract.functions.clobWithdraw(token_address, amount).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def execute_clob_post_fill_order(self, clob_address: str, args: Dict[str, Any], sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a fill order on a CLOB.
        
        Args:
            clob_address: Address of the CLOB contract
            args: PostFillOrderArgs struct from the CLOB interface
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        clob_address = self.web3.to_checksum_address(clob_address)
        tx = self.contract.functions.executeClobPostFillOrder(clob_address, args).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def execute_route(self, token_in: str, amount_in: int, amount_out_min: int, deadline: int, 
                      hops: List[bytes], settlement: int, sender_address: str, value: int = 0, **kwargs) -> Dict[str, Any]:
        """
        Execute a multi-hop route.
        
        Args:
            token_in: Address of the input token
            amount_in: Amount of input tokens
            amount_out_min: Minimum amount of output tokens expected
            deadline: Transaction deadline timestamp
            hops: Array of encoded hop data
            settlement: Settlement type (NONE=0, WRAP=1, UNWRAP=2)
            sender_address: Address of the transaction sender
            value: ETH value to send with the transaction (for wrapping)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        token_in = self.web3.to_checksum_address(token_in)
        tx = self.contract.functions.executeRoute(
            token_in, amount_in, amount_out_min, deadline, hops, settlement
        ).build_transaction({
            'from': sender_address,
            'value': value,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def execute_univ2_swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, 
                                                  path: List[str], sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a UniswapV2 swap.
        
        Args:
            amount_in: Amount of input tokens
            amount_out_min: Minimum amount of output tokens expected
            path: Array of token addresses in the swap path
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        path = [self.web3.to_checksum_address(addr) for addr in path]
        tx = self.contract.functions.executeUniV2SwapExactTokensForTokens(
            amount_in, amount_out_min, path
        ).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def launchpad_buy(self, launch_token: str, amount_out_base: int, quote_token: str, 
                     worst_amount_in_quote: int, sender_address: str, value: int = 0, **kwargs) -> Dict[str, Any]:
        """
        Buy tokens from a launchpad.
        
        Args:
            launch_token: Address of the launch token
            amount_out_base: Amount of base tokens to receive
            quote_token: Address of the quote token
            worst_amount_in_quote: Maximum amount of quote tokens to spend
            sender_address: Address of the transaction sender
            value: ETH value to send with the transaction (if using ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        launch_token = self.web3.to_checksum_address(launch_token)
        quote_token = self.web3.to_checksum_address(quote_token)
        tx = self.contract.functions.launchpadBuy(
            launch_token, amount_out_base, quote_token, worst_amount_in_quote
        ).build_transaction({
            'from': sender_address,
            'value': value,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def launchpad_buy_permit2(self, launch_token: str, amount_out_base: int, quote_token: str, 
                             worst_amount_in_quote: int, permit_single: Dict[str, Any], signature: bytes,
                             sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Buy tokens from a launchpad using Permit2.
        
        Args:
            launch_token: Address of the launch token
            amount_out_base: Amount of base tokens to receive
            quote_token: Address of the quote token
            worst_amount_in_quote: Maximum amount of quote tokens to spend
            permit_single: PermitSingle struct from the IAllowanceTransfer interface
            signature: Signature bytes for the permit
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        launch_token = self.web3.to_checksum_address(launch_token)
        quote_token = self.web3.to_checksum_address(quote_token)
        tx = self.contract.functions.launchpadBuyPermit2(
            launch_token, amount_out_base, quote_token, worst_amount_in_quote, permit_single, signature
        ).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def launchpad_sell(self, launch_token: str, amount_in_base: int, worst_amount_out_quote: int, 
                      unwrap_eth: bool, sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Sell tokens on a launchpad.
        
        Args:
            launch_token: Address of the launch token
            amount_in_base: Amount of base tokens to sell
            worst_amount_out_quote: Minimum amount of quote tokens to receive
            unwrap_eth: Whether to unwrap WETH to ETH
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        launch_token = self.web3.to_checksum_address(launch_token)
        tx = self.contract.functions.launchpadSell(
            launch_token, amount_in_base, worst_amount_out_quote, unwrap_eth
        ).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
    
    def launchpad_sell_permit2(self, token: str, amount_in_base: int, worst_amount_out_quote: int, 
                             permit_single: Dict[str, Any], signature: bytes, sender_address: str, **kwargs) -> Dict[str, Any]:
        """
        Sell tokens on a launchpad using Permit2.
        
        Args:
            token: Address of the token to sell
            amount_in_base: Amount of base tokens to sell
            worst_amount_out_quote: Minimum amount of quote tokens to receive
            permit_single: PermitSingle struct from the IAllowanceTransfer interface
            signature: Signature bytes for the permit
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
            
        Returns:
            Transaction receipt
        """
        token = self.web3.to_checksum_address(token)
        tx = self.contract.functions.launchpadSellPermit2(
            token, amount_in_base, worst_amount_out_quote, permit_single, signature
        ).build_transaction({
            'from': sender_address,
            'nonce': self.web3.eth.get_transaction_count(sender_address),
            **kwargs
        })
        return tx
