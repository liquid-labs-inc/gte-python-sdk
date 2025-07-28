# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .events import ApprovalEvent, TransferEvent


class Erc20:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("erc20")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def name(self) -> str:
        func = self.contract.functions.name()
        return await func.call()

    def approve(self, spender: ChecksumAddress, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approve(spender, value)
        return TypedContractFunction(func, params={**kwargs})

    async def total_supply(self) -> int:
        func = self.contract.functions.totalSupply()
        return await func.call()

    def transfer_from(self, from_: ChecksumAddress, to: ChecksumAddress, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferFrom(from_, to, value)
        return TypedContractFunction(func, params={**kwargs})

    async def decimals(self) -> int:
        func = self.contract.functions.decimals()
        return await func.call()

    async def balance_of(self, owner: ChecksumAddress) -> int:
        func = self.contract.functions.balanceOf(owner)
        return await func.call()

    async def symbol(self) -> str:
        func = self.contract.functions.symbol()
        return await func.call()

    def transfer(self, to: ChecksumAddress, value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transfer(to, value)
        return TypedContractFunction(func, params={**kwargs})

    async def allowance(self, owner: ChecksumAddress, spender: ChecksumAddress) -> int:
        func = self.contract.functions.allowance(owner, spender)
        return await func.call()

    def increase_allowance(self, spender: ChecksumAddress, added_value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.increaseAllowance(spender, added_value)
        return TypedContractFunction(func, params={**kwargs})

    def decrease_allowance(self, spender: ChecksumAddress, subtracted_value: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.decreaseAllowance(spender, subtracted_value)
        return TypedContractFunction(func, params={**kwargs})