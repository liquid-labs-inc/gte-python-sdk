# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import CancelArgs, PermitDetails, PermitSingle, PostFillOrderArgs, PostLimitOrderArgs


class Router:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("router")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def abi_version(self) -> int:
        func = self.contract.functions.ABI_VERSION()
        return await func.call()

    def clob_cancel(self, clob: ChecksumAddress, args: CancelArgs, is_unwrapping: bool, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.clobCancel(clob, tuple(args), is_unwrapping)
        return TypedContractFunction(func, params={**kwargs})

    def clob_deposit(self, token: ChecksumAddress, amount: int, from_router: bool, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.clobDeposit(token, amount, from_router)
        return TypedContractFunction(func, params={**kwargs})

    async def clob_factory(self) -> ChecksumAddress:
        func = self.contract.functions.clobFactory()
        return await func.call()

    def clob_post_fill_order(self, clob: ChecksumAddress, args: PostFillOrderArgs, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.clobPostFillOrder(clob, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def clob_post_limit_order(self, clob: ChecksumAddress, args: PostLimitOrderArgs, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.clobPostLimitOrder(clob, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def clob_withdraw(self, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.clobWithdraw(token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def execute_route(self, token_in: ChecksumAddress, amount_in: int, amount_out_min: int, deadline: int, is_unwrapping: bool, settlement_in: int, hops: list[HexBytes], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.executeRoute(token_in, amount_in, amount_out_min, deadline, is_unwrapping, settlement_in, hops)
        return TypedContractFunction(func, params={**kwargs})

    async def launchpad(self) -> ChecksumAddress:
        func = self.contract.functions.launchpad()
        return await func.call()

    def launchpad_buy(self, launch_token: ChecksumAddress, amount_out_base: int, quote_token: ChecksumAddress, worst_amount_in_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (base_bought, quote_spent)
        """
        func = self.contract.functions.launchpadBuy(launch_token, amount_out_base, quote_token, worst_amount_in_quote)
        return TypedContractFunction(func, params={**kwargs})

    def launchpad_buy_permit2(self, launch_token: ChecksumAddress, amount_out_base: int, quote_token: ChecksumAddress, worst_amount_in_quote: int, permit_single: PermitSingle, signature: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (base_bought, quote_spent)
        """
        func = self.contract.functions.launchpadBuyPermit2(launch_token, amount_out_base, quote_token, worst_amount_in_quote, tuple(permit_single), signature)
        return TypedContractFunction(func, params={**kwargs})

    def launchpad_sell(self, launch_token: ChecksumAddress, amount_in_base: int, worst_amount_out_quote: int, unwrap_eth: bool, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (base_spent, quote_bought)
        """
        func = self.contract.functions.launchpadSell(launch_token, amount_in_base, worst_amount_out_quote, unwrap_eth)
        return TypedContractFunction(func, params={**kwargs})

    def launchpad_sell_permit2(self, launch_token: ChecksumAddress, amount_in_base: int, worst_amount_out_quote: int, unwrap_eth: bool, permit_single: PermitSingle, signature: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (base_spent, quote_bought)
        """
        func = self.contract.functions.launchpadSellPermit2(launch_token, amount_in_base, worst_amount_out_quote, unwrap_eth, tuple(permit_single), signature)
        return TypedContractFunction(func, params={**kwargs})

    async def permit2(self) -> ChecksumAddress:
        func = self.contract.functions.permit2()
        return await func.call()

    async def uni_v2_router(self) -> ChecksumAddress:
        func = self.contract.functions.uniV2Router()
        return await func.call()

    def uni_v2_swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list[ChecksumAddress], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.uniV2SwapExactTokensForTokens(amount_in, amount_out_min, path)
        return TypedContractFunction(func, params={**kwargs})

    async def weth(self) -> ChecksumAddress:
        func = self.contract.functions.weth()
        return await func.call()