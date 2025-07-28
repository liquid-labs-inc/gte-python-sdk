# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes


class UniswapRouter:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("uniswap_router")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def weth(self) -> ChecksumAddress:
        func = self.contract.functions.WETH()
        return await func.call()

    def add_liquidity(self, token_a: ChecksumAddress, token_b: ChecksumAddress, amount_a_desired: int, amount_b_desired: int, amount_a_min: int, amount_b_min: int, to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_a, amount_b, liquidity)
        """
        func = self.contract.functions.addLiquidity(token_a, token_b, amount_a_desired, amount_b_desired, amount_a_min, amount_b_min, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def add_liquidity_eth(self, token: ChecksumAddress, amount_token_desired: int, amount_token_min: int, amount_eth_min: int, to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_token, amount_eth, liquidity)
        """
        func = self.contract.functions.addLiquidityETH(token, amount_token_desired, amount_token_min, amount_eth_min, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    async def factory(self) -> ChecksumAddress:
        func = self.contract.functions.factory()
        return await func.call()

    async def get_amount_in(self, amount_out: int, reserve_in: int, reserve_out: int) -> int:
        func = self.contract.functions.getAmountIn(amount_out, reserve_in, reserve_out)
        return await func.call()

    async def get_amount_out(self, amount_in: int, reserve_in: int, reserve_out: int) -> int:
        func = self.contract.functions.getAmountOut(amount_in, reserve_in, reserve_out)
        return await func.call()

    async def get_amounts_in(self, amount_out: int, path: list[ChecksumAddress]) -> list[int]:
        func = self.contract.functions.getAmountsIn(amount_out, path)
        return await func.call()

    async def get_amounts_out(self, amount_in: int, path: list[ChecksumAddress]) -> list[int]:
        func = self.contract.functions.getAmountsOut(amount_in, path)
        return await func.call()

    async def quote(self, amount_a: int, reserve_a: int, reserve_b: int) -> int:
        func = self.contract.functions.quote(amount_a, reserve_a, reserve_b)
        return await func.call()

    def remove_liquidity(self, token_a: ChecksumAddress, token_b: ChecksumAddress, liquidity: int, amount_a_min: int, amount_b_min: int, to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_a, amount_b)
        """
        func = self.contract.functions.removeLiquidity(token_a, token_b, liquidity, amount_a_min, amount_b_min, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def remove_liquidity_eth(self, token: ChecksumAddress, liquidity: int, amount_token_min: int, amount_eth_min: int, to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_token, amount_eth)
        """
        func = self.contract.functions.removeLiquidityETH(token, liquidity, amount_token_min, amount_eth_min, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def remove_liquidity_eth_supporting_fee_on_transfer_tokens(self, token: ChecksumAddress, liquidity: int, amount_token_min: int, amount_eth_min: int, to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.removeLiquidityETHSupportingFeeOnTransferTokens(token, liquidity, amount_token_min, amount_eth_min, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def remove_liquidity_eth_with_permit(self, token: ChecksumAddress, liquidity: int, amount_token_min: int, amount_eth_min: int, to: ChecksumAddress, deadline: int, approve_max: bool, v: int, r: HexBytes, s: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_token, amount_eth)
        """
        func = self.contract.functions.removeLiquidityETHWithPermit(token, liquidity, amount_token_min, amount_eth_min, to, deadline, approve_max, v, r, s)
        return TypedContractFunction(func, params={**kwargs})

    def remove_liquidity_eth_with_permit_supporting_fee_on_transfer_tokens(self, token: ChecksumAddress, liquidity: int, amount_token_min: int, amount_eth_min: int, to: ChecksumAddress, deadline: int, approve_max: bool, v: int, r: HexBytes, s: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(token, liquidity, amount_token_min, amount_eth_min, to, deadline, approve_max, v, r, s)
        return TypedContractFunction(func, params={**kwargs})

    def remove_liquidity_with_permit(self, token_a: ChecksumAddress, token_b: ChecksumAddress, liquidity: int, amount_a_min: int, amount_b_min: int, to: ChecksumAddress, deadline: int, approve_max: bool, v: int, r: HexBytes, s: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_a, amount_b)
        """
        func = self.contract.functions.removeLiquidityWithPermit(token_a, token_b, liquidity, amount_a_min, amount_b_min, to, deadline, approve_max, v, r, s)
        return TypedContractFunction(func, params={**kwargs})

    def swap_eth_for_exact_tokens(self, amount_out: int, path: list[ChecksumAddress], to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapETHForExactTokens(amount_out, path, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_exact_eth_for_tokens(self, amount_out_min: int, path: list[ChecksumAddress], to_: ChecksumAddress, deadline: int, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactETHForTokens(amount_out_min, path, to_, deadline)
        return TypedContractFunction(func, params={"value": value, **kwargs})

    def swap_exact_eth_for_tokens_supporting_fee_on_transfer_tokens(self, amount_out_min: int, path: list[ChecksumAddress], to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(amount_out_min, path, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_exact_tokens_for_eth(self, amount_in: int, amount_out_min: int, path: list[ChecksumAddress], to_: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactTokensForETH(amount_in, amount_out_min, path, to_, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_exact_tokens_for_eth_supporting_fee_on_transfer_tokens(self, amount_in: int, amount_out_min: int, path: list[ChecksumAddress], to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(amount_in, amount_out_min, path, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list[ChecksumAddress], to_: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactTokensForTokens(amount_in, amount_out_min, path, to_, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_exact_tokens_for_tokens_supporting_fee_on_transfer_tokens(self, amount_in: int, amount_out_min: int, path: list[ChecksumAddress], to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(amount_in, amount_out_min, path, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_tokens_for_exact_eth(self, amount_out: int, amount_in_max: int, path: list[ChecksumAddress], to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapTokensForExactETH(amount_out, amount_in_max, path, to, deadline)
        return TypedContractFunction(func, params={**kwargs})

    def swap_tokens_for_exact_tokens(self, amount_out: int, amount_in_max: int, path: list[ChecksumAddress], to: ChecksumAddress, deadline: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swapTokensForExactTokens(amount_out, amount_in_max, path, to, deadline)
        return TypedContractFunction(func, params={**kwargs})