from typing import Any

from eth_typing import Address, ChecksumAddress
from hexbytes import HexBytes
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from .structs import ICLOBCancelArgs, ICLOBPostLimitOrderArgs
from .utils import TypedContractFunction, load_abi


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
        return self.contract.functions.weth().call()

    async def get_launchpad(self) -> ChecksumAddress:
        """Get the Launchpad contract address."""
        return self.contract.functions.launchpad().call()

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
        self, clob_address: str, args: ICLOBCancelArgs, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[HexBytes]:
        """
        Cancel a CLOB order.

        Args:
            clob_address: Address of the CLOB contract
            args: CancelArgs struct from the CLOB interface
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        clob_address = self.web3.to_checksum_address(clob_address)
        tx_params = {**kwargs}

        func = self.contract.functions.clobCancel(clob_address, args)
        return TypedContractFunction(func, tx_params)

    def clob_deposit(
        self,
        token_address: ChecksumAddress,
        amount: int,
        from_router: bool,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Deposit tokens into a CLOB.

        Args:
            token_address: Address of the token to deposit
            amount: Amount of tokens to deposit
            from_router: Whether the deposit is from the router
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """

        tx_params = {**kwargs}

        func = self.contract.functions.clobDeposit(token_address, amount, from_router)
        return TypedContractFunction(func, tx_params)

    def clob_post_limit_order(
        self,
        clob_address: str,
        args: ICLOBPostLimitOrderArgs,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Post a limit order to a CLOB.

        Args:
            clob_address: Address of the CLOB contract
            args: PostLimitOrderArgs struct from the CLOB interface
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        clob_address = self.web3.to_checksum_address(clob_address)
        tx_params = {**kwargs}

        func = self.contract.functions.clobPostLimitOrder(clob_address, args)
        return TypedContractFunction(func, tx_params)

    def clob_withdraw(
        self, token_address: str, amount: int, **kwargs
    ) -> TypedContractFunction[HexBytes]:
        """
        Withdraw tokens from a CLOB.

        Args:
            token_address: Address of the token to withdraw
            amount: Amount of tokens to withdraw
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        token_address = self.web3.to_checksum_address(token_address)
        tx_params = {**kwargs}

        func = self.contract.functions.clobWithdraw(token_address, amount)
        return TypedContractFunction(func, tx_params)

    def execute_clob_post_fill_order(
        self, clob_address: str, args: dict[str, Any], **kwargs
    ) -> TypedContractFunction[HexBytes]:
        """
        Execute a fill order on a CLOB.

        Args:
            clob_address: Address of the CLOB contract
            args: PostFillOrderArgs struct from the CLOB interface
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        clob_address = self.web3.to_checksum_address(clob_address)

        tx_params = {**kwargs}

        func = self.contract.functions.executeClobPostFillOrder(clob_address, args)
        return TypedContractFunction(func, tx_params)

    def execute_route(
        self,
        token_in: Address,
        amount_in: int,
        amount_out_min: int,
        deadline: int,
        hops: list[bytes],
        settlement: int,
        value: int = 0,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Execute a multi-hop route.

        Args:
            token_in: Address of the input token
            amount_in: Amount of input tokens
            amount_out_min: Minimum amount of output tokens expected
            deadline: Transaction deadline timestamp
            hops: Array of encoded hop data
            settlement: Settlement type (NONE=0, WRAP=1, UNWRAP=2)
            value: ETH value to send with the transaction (for wrapping)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """

        tx_params = {"value": value, **kwargs}

        func = self.contract.functions.executeRoute(
            token_in, amount_in, amount_out_min, deadline, hops, settlement
        )
        return TypedContractFunction(func, tx_params)

    def execute_univ2_swap_exact_tokens_for_tokens(
        self,
        amount_in: int,
        amount_out_min: int,
        path: list[Address],
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Execute a UniswapV2 swap.

        Args:
            amount_in: Amount of input tokens
            amount_out_min: Minimum amount of output tokens expected
            path: Array of token addresses in the swap path
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """

        tx_params = {**kwargs}

        func = self.contract.functions.executeUniV2SwapExactTokensForTokens(
            amount_in, amount_out_min, path
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_buy(
        self,
        launch_token: Address,
        amount_out_base: int,
        quote_token: Address,
        worst_amount_in_quote: int,
        value: int = 0,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Buy tokens from a launchpad.

        Args:
            launch_token: Address of the launch token
            amount_out_base: Amount of base tokens to receive
            quote_token: Address of the quote token
            worst_amount_in_quote: Maximum amount of quote tokens to spend
            value: ETH value to send with the transaction (if using ETH)
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        tx_params = {"value": value, **kwargs}

        func = self.contract.functions.launchpadBuy(
            launch_token, amount_out_base, quote_token, worst_amount_in_quote
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_buy_permit2(
        self,
        launch_token: Address,
        amount_out_base: int,
        quote_token: Address,
        worst_amount_in_quote: int,
        permit_single: dict[str, Any],
        signature: bytes,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Buy tokens from a launchpad using Permit2.

        Args:
            launch_token: Address of the launch token
            amount_out_base: Amount of base tokens to receive
            quote_token: Address of the quote token
            worst_amount_in_quote: Maximum amount of quote tokens to spend
            permit_single: PermitSingle struct from the IAllowanceTransfer interface
            signature: Signature bytes for the permit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """

        tx_params = {**kwargs}

        func = self.contract.functions.launchpadBuyPermit2(
            launch_token,
            amount_out_base,
            quote_token,
            worst_amount_in_quote,
            permit_single,
            signature,
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_sell(
        self,
        launch_token: str,
        amount_in_base: int,
        worst_amount_out_quote: int,
        unwrap_eth: bool,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Sell tokens on a launchpad.

        Args:
            launch_token: Address of the launch token
            amount_in_base: Amount of base tokens to sell
            worst_amount_out_quote: Minimum amount of quote tokens to receive
            unwrap_eth: Whether to unwrap WETH to ETH
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        launch_token = self.web3.to_checksum_address(launch_token)
        tx_params = {**kwargs}

        func = self.contract.functions.launchpadSell(
            launch_token, amount_in_base, worst_amount_out_quote, unwrap_eth
        )
        return TypedContractFunction(func, tx_params)

    def launchpad_sell_permit2(
        self,
        token: str,
        amount_in_base: int,
        worst_amount_out_quote: int,
        permit_single: dict[str, Any],
        signature: bytes,
        **kwargs,
    ) -> TypedContractFunction[HexBytes]:
        """
        Sell tokens on a launchpad using Permit2.

        Args:
            token: Address of the token to sell
            amount_in_base: Amount of base tokens to sell
            worst_amount_out_quote: Minimum amount of quote tokens to receive
            permit_single: PermitSingle struct from the IAllowanceTransfer interface
            signature: Signature bytes for the permit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be executed
        """
        token = self.web3.to_checksum_address(token)
        tx_params = {**kwargs}

        func = self.contract.functions.launchpadSellPermit2(
            token, amount_in_base, worst_amount_out_quote, permit_single, signature
        )
        return TypedContractFunction(func, tx_params)
