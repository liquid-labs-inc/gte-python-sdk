# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes


class OperatorContract:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("operator_contract")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def account_manager(self) -> ChecksumAddress:
        func = self.contract.functions.accountManager()
        return await func.call()

    def approve_operator_perps(self, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approveOperatorPerps(operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    def approve_operator_spot(self, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approveOperatorSpot(operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    def disapprove_operator_perps(self, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.disapproveOperatorPerps(operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    def disapprove_operator_spot(self, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.disapproveOperatorSpot(operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def get_role_approvals_perps(self, account: ChecksumAddress, operator: ChecksumAddress) -> int:
        func = self.contract.functions.getRoleApprovalsPerps(account, operator)
        return await func.call()

    async def get_role_approvals_spot(self, account: ChecksumAddress, operator: ChecksumAddress) -> int:
        func = self.contract.functions.getRoleApprovalsSpot(account, operator)
        return await func.call()

    async def perp_manager(self) -> ChecksumAddress:
        func = self.contract.functions.perpManager()
        return await func.call()