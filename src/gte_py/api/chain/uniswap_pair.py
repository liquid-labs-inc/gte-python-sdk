# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import SwapData
from .events import ApprovalEvent, BurnEvent, MintEvent, SwapEvent, SyncEvent, TransferEvent


class UniswapPair:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("uniswap_pair")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def domain_separator(self) -> HexBytes:
        func = self.contract.functions.DOMAIN_SEPARATOR()
        return await func.call()

    async def minimum_liquidity(self) -> int:
        func = self.contract.functions.MINIMUM_LIQUIDITY()
        return await func.call()

    async def permit_typehash(self) -> HexBytes:
        func = self.contract.functions.PERMIT_TYPEHASH()
        return await func.call()

    async def allowance(self, param1: ChecksumAddress, param2: ChecksumAddress) -> int:
        func = self.contract.functions.allowance(param1, param2)
        return await func.call()

    def approve(self, spender: ChecksumAddress, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approve(spender, value)
        return TypedContractFunction(func, params={**kwargs})

    async def balance_of(self, param: ChecksumAddress) -> int:
        func = self.contract.functions.balanceOf(param)
        return await func.call()

    def burn(self, to: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount0, amount1)
        """
        func = self.contract.functions.burn(to)
        return TypedContractFunction(func, params={**kwargs})

    async def decimals(self) -> int:
        func = self.contract.functions.decimals()
        return await func.call()

    async def factory(self) -> ChecksumAddress:
        func = self.contract.functions.factory()
        return await func.call()

    async def get_reserves(self) -> tuple[Any, Any, int]:
        """
        Returns:
            tuple: (reserve0, reserve1, block_timestamp_last)
        """
        func = self.contract.functions.getReserves()
        return await func.call()

    def initialize(self, token0: ChecksumAddress, token1: ChecksumAddress, router: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(token0, token1, router)
        return TypedContractFunction(func, params={**kwargs})

    async def k_last(self) -> int:
        func = self.contract.functions.kLast()
        return await func.call()

    def mint(self, to: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.mint(to)
        return TypedContractFunction(func, params={**kwargs})

    async def name(self) -> str:
        func = self.contract.functions.name()
        return await func.call()

    async def nonces(self, param: ChecksumAddress) -> int:
        func = self.contract.functions.nonces(param)
        return await func.call()

    def permit(self, owner: ChecksumAddress, spender: ChecksumAddress, value: int, deadline: int, v: int, r: HexBytes, s: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.permit(owner, spender, value, deadline, v, r, s)
        return TypedContractFunction(func, params={**kwargs})

    async def price0_cumulative_last(self) -> int:
        func = self.contract.functions.price0CumulativeLast()
        return await func.call()

    async def price1_cumulative_last(self) -> int:
        func = self.contract.functions.price1CumulativeLast()
        return await func.call()

    async def router(self) -> ChecksumAddress:
        func = self.contract.functions.router()
        return await func.call()

    def skim(self, to: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.skim(to)
        return TypedContractFunction(func, params={**kwargs})

    def swap(self, d: SwapData, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.swap(tuple(d))
        return TypedContractFunction(func, params={**kwargs})

    async def symbol(self) -> str:
        func = self.contract.functions.symbol()
        return await func.call()

    def sync(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.sync()
        return TypedContractFunction(func, params={**kwargs})

    async def token0(self) -> ChecksumAddress:
        func = self.contract.functions.token0()
        return await func.call()

    async def token1(self) -> ChecksumAddress:
        func = self.contract.functions.token1()
        return await func.call()

    async def total_supply(self) -> int:
        func = self.contract.functions.totalSupply()
        return await func.call()

    def transfer(self, to: ChecksumAddress, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transfer(to, value)
        return TypedContractFunction(func, params={**kwargs})

    def transfer_from(self, from_: ChecksumAddress, to: ChecksumAddress, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferFrom(from_, to, value)
        return TypedContractFunction(func, params={**kwargs})