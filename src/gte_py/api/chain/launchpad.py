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

    async def account_manager(self) -> ChecksumAddress:
        func = self.contract.functions.accountManager()
        return await func.call()

    async def base_sold_from_curve(self, token: ChecksumAddress) -> int:
        func = self.contract.functions.baseSoldFromCurve(token)
        return await func.call()

    def buy(self, account: ChecksumAddress, token: ChecksumAddress, amount_out_base: int, max_amount_in_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_out_base_actual, amount_in_quote)
        """
        func = self.contract.functions.buy(account, token, amount_out_base, max_amount_in_quote)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        return TypedContractFunction(func, params={**kwargs})

    async def current_bonding_curve(self) -> ChecksumAddress:
        func = self.contract.functions.currentBondingCurve()
        return await func.call()

    async def current_quote_asset(self) -> ChecksumAddress:
        func = self.contract.functions.currentQuoteAsset()
        return await func.call()

    async def distributor(self) -> ChecksumAddress:
        func = self.contract.functions.distributor()
        return await func.call()

    async def event_nonce(self) -> int:
        func = self.contract.functions.eventNonce()
        return await func.call()

    async def get_pair(self, token: ChecksumAddress) -> ChecksumAddress:
        func = self.contract.functions.getPair(token)
        return await func.call()

    async def gte_router(self) -> ChecksumAddress:
        func = self.contract.functions.gteRouter()
        return await func.call()

    def initialize(self, owner_: ChecksumAddress, quote_asset_: ChecksumAddress, bonding_curve_: ChecksumAddress, launchpad_lp_vault_: ChecksumAddress, launch_fee_: int, bonding_curve_init_data: HexBytes, uni_v2_init_code_hash_: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(owner_, quote_asset_, bonding_curve_, launchpad_lp_vault_, launch_fee_, bonding_curve_init_data, uni_v2_init_code_hash_)
        return TypedContractFunction(func, params={**kwargs})

    async def is_fee_sharing_launch_token(self, token: ChecksumAddress) -> bool:
        func = self.contract.functions.isFeeSharingLaunchToken(token)
        return await func.call()

    async def is_launch_token(self, token: ChecksumAddress) -> bool:
        func = self.contract.functions.isLaunchToken(token)
        return await func.call()

    def launch(self, name: str, symbol: str, media_uri: str, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.launch(name, symbol, media_uri)
        return TypedContractFunction(func, params={**kwargs})

    async def launch_fee(self) -> int:
        func = self.contract.functions.launchFee()
        return await func.call()

    async def launches(self, launch_token: ChecksumAddress) -> LaunchData:
        func = self.contract.functions.launches(launch_token)
        return await func.call()

    async def launchpad_lp_vault(self) -> ChecksumAddress:
        func = self.contract.functions.launchpadLPVault()
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        func = self.contract.functions.ownershipHandoverExpiresAt(pending_owner)
        return await func.call()

    async def quote_base_for_quote(self, token: ChecksumAddress, quote_amount: int, is_buy: bool) -> int:
        func = self.contract.functions.quoteBaseForQuote(token, quote_amount, is_buy)
        return await func.call()

    async def quote_bought_by_curve(self, token: ChecksumAddress) -> int:
        func = self.contract.functions.quoteBoughtByCurve(token)
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

    def sell(self, account: ChecksumAddress, token: ChecksumAddress, amount_in_base: int, min_amount_out_quote: int, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (amount_in_base_actual, amount_out_quote_actual)
        """
        func = self.contract.functions.sell(account, token, amount_in_base, min_amount_out_quote)
        return TypedContractFunction(func, params={**kwargs})

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})

    async def uni_v2_factory(self) -> ChecksumAddress:
        func = self.contract.functions.uniV2Factory()
        return await func.call()

    async def uni_v2_init_code_hash(self) -> HexBytes:
        func = self.contract.functions.uniV2InitCodeHash()
        return await func.call()

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

    def update_launchpad_lp_vault(self, new_launchpad_lp_vault: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.updateLaunchpadLPVault(new_launchpad_lp_vault)
        return TypedContractFunction(func, params={**kwargs})

    def update_quote_asset(self, new_quote_asset: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.updateQuoteAsset(new_quote_asset)
        return TypedContractFunction(func, params={**kwargs})