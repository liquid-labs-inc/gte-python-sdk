# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .events import PairCreatedEvent


class UniswapFactory:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("uniswap_factory")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def all_pairs(self, param: int) -> ChecksumAddress:
        func = self.contract.functions.allPairs(param)
        return await func.call()

    async def all_pairs_length(self) -> int:
        func = self.contract.functions.allPairsLength()
        return await func.call()

    def create_pair(self, token_a: ChecksumAddress, token_b: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.createPair(token_a, token_b)
        return TypedContractFunction(func, params={**kwargs})

    async def fee_to(self) -> ChecksumAddress:
        func = self.contract.functions.feeTo()
        return await func.call()

    async def fee_to_setter(self) -> ChecksumAddress:
        func = self.contract.functions.feeToSetter()
        return await func.call()

    async def get_pair(self, token_a: ChecksumAddress, token_b: ChecksumAddress) -> ChecksumAddress:
        func = self.contract.functions.getPair(token_a, token_b)
        return await func.call()

    def set_fee_to(self, param: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFeeTo(param)
        return TypedContractFunction(func, params={**kwargs})

    def set_fee_to_setter(self, param: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFeeToSetter(param)
        return TypedContractFunction(func, params={**kwargs})