# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import AmendArgs, PermitDetails, PermitSingle, PlaceOrderArgs, PlaceOrderResult


class Router:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("router")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def abi_version(self) -> int:
        func = self.contract.functions.ABI_VERSION()
        return await func.call()

    async def acct_manager(self) -> ChecksumAddress:
        func = self.contract.functions.acctManager()
        return await func.call()

    def add_amm_liquidity(self, token_a: ChecksumAddress, token_b: ChecksumAddress, amount_a_desired: int, amount_b_desired: int, amount_a_min: int, amount_b_min: int, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_a, amount_b, liquidity)
        """
        func = self.contract.functions.addAMMLiquidity(token_a, token_b, amount_a_desired, amount_b_desired, amount_a_min, amount_b_min, deadline)
        return TypedContractFunction(func, params={**kwargs})

    async def clob_admin_panel(self) -> ChecksumAddress:
        func = self.contract.functions.clobAdminPanel()
        return await func.call()

    def clob_amend(self, clob: ChecksumAddress, args: AmendArgs, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (quote_delta, base_delta)
        """
        func = self.contract.functions.clobAmend(clob, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def clob_cancel(self, clob: ChecksumAddress, order_or_client_ids: list[int], **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (quote_refunded, base_refunded)
        """
        func = self.contract.functions.clobCancel(clob, order_or_client_ids)
        return TypedContractFunction(func, params={**kwargs})

    def clob_place_order(self, clob: ChecksumAddress, args: PlaceOrderArgs, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.clobPlaceOrder(clob, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def execute_route(self, token_in: ChecksumAddress, amount_in: int, amount_out_min: int, deadline: int, hops: list[HexBytes], **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (final_amount_out, final_token_out)
        """
        func = self.contract.functions.executeRoute(token_in, amount_in, amount_out_min, deadline, hops)
        return TypedContractFunction(func, params={**kwargs})

    def get_swap_user(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.getSwapUser()
        return TypedContractFunction(func, params={**kwargs})

    async def launchpad(self) -> ChecksumAddress:
        func = self.contract.functions.launchpad()
        return await func.call()

    def launchpad_buy(self, launch_token: ChecksumAddress, amount_out_base: int, worst_amount_in_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (base_bought, quote_spent)
        """
        func = self.contract.functions.launchpadBuy(launch_token, amount_out_base, worst_amount_in_quote)
        return TypedContractFunction(func, params={**kwargs})

    def launchpad_sell(self, launch_token: ChecksumAddress, amount_in_base: int, worst_amount_out_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (base_spent, quote_bought)
        """
        func = self.contract.functions.launchpadSell(launch_token, amount_in_base, worst_amount_out_quote)
        return TypedContractFunction(func, params={**kwargs})

    async def permit2(self) -> ChecksumAddress:
        func = self.contract.functions.permit2()
        return await func.call()

    def remove_amm_liquidity(self, token_a: ChecksumAddress, token_b: ChecksumAddress, liquidity: int, amount_a_min: int, amount_b_min: int, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_a, amount_b)
        """
        func = self.contract.functions.removeAMMLiquidity(token_a, token_b, liquidity, amount_a_min, amount_b_min, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def spot_deposit(self, token: ChecksumAddress, amount: int, from_router: bool, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.spotDeposit(token, amount, from_router)
        return TypedContractFunction(func, params={**kwargs})

    def spot_deposit_permit2(self, token: ChecksumAddress, amount: int, permit_single: PermitSingle, signature: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.spotDepositPermit2(token, amount, tuple(permit_single), signature)
        return TypedContractFunction(func, params={**kwargs})

    def spot_withdraw(self, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.spotWithdraw(token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def swap_exact_tokens_for_tokens_amm(self, amount_in: int, amount_out_min: int, path: list[ChecksumAddress], deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactTokensForTokensAMM(amount_in, amount_out_min, path, deadline)
        return TypedContractFunction(func, params={**kwargs})

    async def uni_v2_router(self) -> ChecksumAddress:
        func = self.contract.functions.uniV2Router()
        return await func.call()