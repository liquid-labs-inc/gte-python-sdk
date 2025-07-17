from typing import Any

from eth_typing import Address, ChecksumAddress
from hexbytes import HexBytes
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from .structs import ICLOBCancelArgs, ICLOBPostLimitOrderArgs, ICLOBPostFillOrderArgs
from .utils import TypedContractFunction, load_abi


class Router:
    """
    Python wrapper for the GTERouter smart contract.
    Provides methods to interact with the GTERouter functionality including:
    - CLOB interactions
    - Launchpad operations
    - Route execution
    - UniV2 swaps
    """

    def __init__(
        self,
        web3: AsyncWeb3,
        contract_address: ChecksumAddress,
    ):
        """
        Initialize the GTERouter wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the GTERouter contract
        """
        self.web3 = web3
        self.address = contract_address
        loaded_abi = load_abi("router")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

    # ================= READ METHODS =================

    async def get_weth(self) -> ChecksumAddress:
        """Get the WETH contract address."""
        return await self.contract.functions.weth().call()

    async def get_launchpad(self) -> ChecksumAddress:
        """Get the Launchpad contract address."""
        return await self.contract.functions.launchpad().call()

    async def get_clob_factory(self) -> ChecksumAddress:
        """Get the CLOB factory contract address."""
        return await self.contract.functions.clobFactory().call()

    async def get_univ2_router(self) -> ChecksumAddress:
        """Get the UniswapV2 Router contract address."""
        return await self.contract.functions.uniV2Router().call()

    async def get_permit2(self) -> ChecksumAddress:
        """Get the Permit2 contract address."""
        return await self.contract.functions.permit2().call()

    # ================= WRITE METHODS =================

    def clob_cancel(
        self,
        clob: str,
        args: ICLOBCancelArgs,
        isUnwrapping: bool,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Cancel a CLOB order.
        Args:
            clob: Address of the CLOB contract
            args: ICLOBCancelArgs NamedTuple with orderIds and settlement
            isUnwrapping: Whether to unwrap WETH to ETH at the end
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        clob = self.web3.to_checksum_address(clob)
        tx_params = {**kwargs}
        
        # Convert NamedTuple to regular tuple for web3.py ABI encoding
        func = self.contract.functions.clobCancel(clob, tuple(args), isUnwrapping)
        return TypedContractFunction(func, tx_params)

    def clob_deposit(
        self,
        token: str,
        amount: int,
        fromRouter: bool,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Deposit tokens into a CLOB.
        Args:
            token: Address of the token to deposit
            amount: Amount of tokens to deposit
            fromRouter: Whether the deposit is from the router
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        token = self.web3.to_checksum_address(token)
        tx_params = {**kwargs}
        func = self.contract.functions.clobDeposit(token, amount, fromRouter)
        return TypedContractFunction(func, tx_params)

    def clob_post_limit_order(
        self,
        clob: str,
        args: ICLOBPostLimitOrderArgs,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Post a limit order to a CLOB.
        Args:
            clob: Address of the CLOB contract
            args: dict with keys matching PostLimitOrderArgs
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        clob = self.web3.to_checksum_address(clob)
        tx_params = {**kwargs}
        func = self.contract.functions.clobPostLimitOrder(clob, tuple(args))
        return TypedContractFunction(func, tx_params)

    def clob_withdraw(
        self,
        token: str,
        amount: int,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Withdraw tokens from a CLOB.
        Args:
            token: Address of the token to withdraw
            amount: Amount of tokens to withdraw
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        token = self.web3.to_checksum_address(token)
        tx_params = {**kwargs}
        func = self.contract.functions.clobWithdraw(token, amount)
        return TypedContractFunction(func, tx_params)

    def clob_post_fill_order(
        self,
        clob: str,
        args: ICLOBPostFillOrderArgs,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Execute a fill order on a CLOB.
        Args:
            clob: Address of the CLOB contract
            args: dict with keys matching PostFillOrderArgs
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        clob = self.web3.to_checksum_address(clob)
        tx_params = {**kwargs}
        func = self.contract.functions.clobPostFillOrder(clob, tuple(args))
        return TypedContractFunction(func, tx_params)

    def execute_route(
        self,
        tokenIn: str,
        amountIn: int,
        amountOutMin: int,
        deadline: int,
        isUnwrapping: bool,
        settlementIn: int,
        hops: list[Any],
        value: int = 0,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Execute a multi-hop route.
        Args:
            tokenIn: Address of the input token
            amountIn: Amount of input tokens
            amountOutMin: Minimum amount of output tokens expected
            deadline: Transaction deadline timestamp
            isUnwrapping: Whether to unwrap WETH to ETH at the end
            settlementIn: Settlement type
            hops: Array of encoded hop data
            value: ETH value to send with the transaction (for wrapping)
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        tokenIn = self.web3.to_checksum_address(tokenIn)
        tx_params = {"value": value, **kwargs}
        func = self.contract.functions.executeRoute(
            tokenIn, amountIn, amountOutMin, deadline, isUnwrapping, settlementIn, hops
        )
        return TypedContractFunction(func, tx_params)

    def univ2_swap_exact_tokens_for_tokens(
        self,
        amountIn: int,
        amountOutMin: int,
        path: list[str],
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Execute a UniswapV2 swap.
        Args:
            amountIn: Amount of input tokens
            amountOutMin: Minimum amount of output tokens expected
            path: Array of token addresses in the swap path
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        path = [self.web3.to_checksum_address(addr) for addr in path]
        tx_params = {**kwargs}
        func = self.contract.functions.uniV2SwapExactTokensForTokens(
            amountIn, amountOutMin, path
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_buy(
        self,
        launchToken: str,
        amountOutBase: int,
        quoteToken: str,
        worstAmountInQuote: int,
        value: int = 0,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Buy tokens from a launchpad.
        Args:
            launchToken: Address of the launch token
            amountOutBase: Amount of base tokens to receive
            quoteToken: Address of the quote token
            worstAmountInQuote: Maximum amount of quote tokens to spend
            value: ETH value to send with the transaction (if using ETH)
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        launchToken = self.web3.to_checksum_address(launchToken)
        quoteToken = self.web3.to_checksum_address(quoteToken)
        tx_params = {"value": value, **kwargs}
        func = self.contract.functions.launchpadBuy(
            launchToken, amountOutBase, quoteToken, worstAmountInQuote
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_buy_permit2(
        self,
        launchToken: str,
        amountOutBase: int,
        quoteToken: str,
        worstAmountInQuote: int,
        permitSingle: dict[str, Any],
        signature: bytes,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Buy tokens from a launchpad using Permit2.
        Args:
            launchToken: Address of the launch token
            amountOutBase: Amount of base tokens to receive
            quoteToken: Address of the quote token
            worstAmountInQuote: Maximum amount of quote tokens to spend
            permitSingle: PermitSingle struct
            signature: Signature bytes for the permit
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        launchToken = self.web3.to_checksum_address(launchToken)
        quoteToken = self.web3.to_checksum_address(quoteToken)
        tx_params = {**kwargs}
        func = self.contract.functions.launchpadBuyPermit2(
            launchToken, amountOutBase, quoteToken, worstAmountInQuote, permitSingle, signature
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_sell(
        self,
        launchToken: str,
        amountInBase: int,
        worstAmountOutQuote: int,
        unwrapEth: bool,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Sell tokens on a launchpad.
        Args:
            launchToken: Address of the launch token
            amountInBase: Amount of base tokens to sell
            worstAmountOutQuote: Minimum amount of quote tokens to receive
            unwrapEth: Whether to unwrap WETH to ETH
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        launchToken = self.web3.to_checksum_address(launchToken)
        tx_params = {**kwargs}
        func = self.contract.functions.launchpadSell(
            launchToken, amountInBase, worstAmountOutQuote, unwrapEth
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_sell_permit2(
        self,
        launchToken: str,
        amountInBase: int,
        worstAmountOutQuote: int,
        unwrapEth: bool,
        permitSingle: dict[str, Any],
        signature: bytes,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Sell tokens on a launchpad using Permit2.
        Args:
            launchToken: Address of the token to sell
            amountInBase: Amount of base tokens to sell
            worstAmountOutQuote: Minimum amount of quote tokens to receive
            unwrapEth: Whether to unwrap WETH to ETH
            permitSingle: PermitSingle struct
            signature: Signature bytes for the permit
            **kwargs: Additional transaction parameters
        Returns:
            TypedContractFunction that can be executed
        """
        launchToken = self.web3.to_checksum_address(launchToken)
        tx_params = {**kwargs}
        func = self.contract.functions.launchpadSellPermit2(
            launchToken, amountInBase, worstAmountOutQuote, unwrapEth, permitSingle, signature
        )
        return TypedContractFunction(func, tx_params)
