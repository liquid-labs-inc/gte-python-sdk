# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import LaunchData
from .events import BondingCurveUpdatedEvent, BondingLockedEvent, InitializedEvent, LaunchpadDeployedEvent, OwnershipHandoverCanceledEvent, OwnershipHandoverRequestedEvent, OwnershipTransferredEvent, QuoteAssetUpdatedEvent, SwapEvent, TokenLaunchedEvent


class Launchpad:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("launchpad")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def abi_version(self) -> int:
        func = self.contract.functions.ABI_VERSION()
        return await func.call()

    async def bonding_supply(self) -> int:
        func = self.contract.functions.BONDING_SUPPLY()
        return await func.call()

    async def total_supply(self) -> int:
        func = self.contract.functions.TOTAL_SUPPLY()
        return await func.call()

    async def __unallocated_slot_0(self) -> int:
        func = self.contract.functions.__unallocated_slot_0()
        return await func.call()

    async def __unallocated_slot_1(self) -> int:
        func = self.contract.functions.__unallocated_slot_1()
        return await func.call()

    async def bonding_curve(self) -> ChecksumAddress:
        func = self.contract.functions.bondingCurve()
        return await func.call()

    def buy(self, account: ChecksumAddress, token: ChecksumAddress, recipient: ChecksumAddress, amount_out_base: int, max_amount_in_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_out_base_actual, amount_in_quote_actual)
        """
        func = self.contract.functions.buy(account, token, recipient, amount_out_base, max_amount_in_quote)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        return TypedContractFunction(func, params={**kwargs})

    async def event_nonce(self) -> int:
        func = self.contract.functions.eventNonce()
        return await func.call()

    async def gte_router(self) -> ChecksumAddress:
        func = self.contract.functions.gteRouter()
        return await func.call()

    def initialize(self, owner_: ChecksumAddress, quote_asset_: ChecksumAddress, bonding_curve_: ChecksumAddress, virtual_base_: int, virtual_quote_: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(owner_, quote_asset_, bonding_curve_, virtual_base_, virtual_quote_)
        return TypedContractFunction(func, params={**kwargs})

    def launch(self, name: str, symbol: str, media_uri: str, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.launch(name, symbol, media_uri)
        return TypedContractFunction(func, params={**kwargs})

    async def launch_fee(self) -> int:
        func = self.contract.functions.launchFee()
        return await func.call()

    async def launches(self, launch_token: ChecksumAddress) -> LaunchData:
        func = self.contract.functions.launches(launch_token)
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        func = self.contract.functions.ownershipHandoverExpiresAt(pending_owner)
        return await func.call()

    def pull_fees(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.pullFees()
        return TypedContractFunction(func, params={**kwargs})

    async def quote_asset(self) -> ChecksumAddress:
        func = self.contract.functions.quoteAsset()
        return await func.call()

    async def quote_base_for_quote(self, token: ChecksumAddress, quote_amount: int, is_buy: bool) -> int:
        func = self.contract.functions.quoteBaseForQuote(token, quote_amount, is_buy)
        return await func.call()

    async def quote_quote_for_base(self, token: ChecksumAddress, base_amount: int, is_buy: bool) -> int:
        func = self.contract.functions.quoteQuoteForBase(token, base_amount, is_buy)
        return await func.call()

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceOwnership()
        return TypedContractFunction(func, params={**kwargs})

    def request_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.requestOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def sell(self, account: ChecksumAddress, token: ChecksumAddress, recipient: ChecksumAddress, amount_in_base: int, min_amount_out_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_in_base_actual, amount_out_quote_actual)
        """
        func = self.contract.functions.sell(account, token, recipient, amount_in_base, min_amount_out_quote)
        return TypedContractFunction(func, params={**kwargs})

    def set_virtual_reserves(self, virtual_base: int, virtual_quote: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setVirtualReserves(virtual_base, virtual_quote)
        return TypedContractFunction(func, params={**kwargs})

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})

    async def uni_v2_router(self) -> ChecksumAddress:
        func = self.contract.functions.uniV2Router()
        return await func.call()

    def update_bonding_curve(self, new_bonding_curve: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.updateBondingCurve(new_bonding_curve)
        return TypedContractFunction(func, params={**kwargs})

    def update_init_code_hash(self, new_hash: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.updateInitCodeHash(new_hash)
        return TypedContractFunction(func, params={**kwargs})

    def update_launch_fee(self, new_launch_fee: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.updateLaunchFee(new_launch_fee)
        return TypedContractFunction(func, params={**kwargs})

    def update_quote_asset(self, new_quote_asset: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.updateQuoteAsset(new_quote_asset)
        return TypedContractFunction(func, params={**kwargs})