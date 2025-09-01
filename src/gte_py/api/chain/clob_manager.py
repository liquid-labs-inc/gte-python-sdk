# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import ConfigParams, SettingsParams
from .events import InitializedEvent, MarketCreatedEvent, OwnershipHandoverCanceledEvent, OwnershipHandoverRequestedEvent, OwnershipTransferredEvent, RolesUpdatedEvent


class ClobManager:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("clob_manager")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def abi_version(self) -> int:
        func = self.contract.functions.ABI_VERSION()
        return await func.call()

    async def expired_order_clearer(self) -> int:
        func = self.contract.functions.EXPIRED_ORDER_CLEARER()
        return await func.call()

    async def fee_tier_setter(self) -> int:
        func = self.contract.functions.FEE_TIER_SETTER()
        return await func.call()

    async def market_manager(self) -> int:
        func = self.contract.functions.MARKET_MANAGER()
        return await func.call()

    async def max_limit_whitelister(self) -> int:
        func = self.contract.functions.MAX_LIMIT_WHITELISTER()
        return await func.call()

    async def account_manager(self) -> ChecksumAddress:
        func = self.contract.functions.accountManager()
        return await func.call()

    def admin_cancel_expired_orders(self, market: ChecksumAddress, ids: list[int], side: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.adminCancelExpiredOrders(market, ids, side)
        return TypedContractFunction(func, params={**kwargs})

    async def beacon(self) -> ChecksumAddress:
        func = self.contract.functions.beacon()
        return await func.call()

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        return TypedContractFunction(func, params={**kwargs})

    def create_market(self, base_token: ChecksumAddress, quote_token: ChecksumAddress, settings: SettingsParams, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.createMarket(base_token, quote_token, tuple(settings))
        return TypedContractFunction(func, params={**kwargs})

    async def get_event_nonce(self) -> int:
        func = self.contract.functions.getEventNonce()
        return await func.call()

    async def get_market_address(self, token_a: ChecksumAddress, token_b: ChecksumAddress) -> ChecksumAddress:
        func = self.contract.functions.getMarketAddress(token_a, token_b)
        return await func.call()

    async def get_max_limit_exempt(self, account: ChecksumAddress) -> bool:
        func = self.contract.functions.getMaxLimitExempt(account)
        return await func.call()

    def grant_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantRoles(user, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def has_all_roles(self, user: ChecksumAddress, roles: int) -> bool:
        func = self.contract.functions.hasAllRoles(user, roles)
        return await func.call()

    async def has_any_role(self, user: ChecksumAddress, roles: int) -> bool:
        func = self.contract.functions.hasAnyRole(user, roles)
        return await func.call()

    def initialize(self, owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(owner)
        return TypedContractFunction(func, params={**kwargs})

    async def is_market(self, market: ChecksumAddress) -> bool:
        func = self.contract.functions.isMarket(market)
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        func = self.contract.functions.ownershipHandoverExpiresAt(pending_owner)
        return await func.call()

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceOwnership()
        return TypedContractFunction(func, params={**kwargs})

    def renounce_roles(self, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceRoles(roles)
        return TypedContractFunction(func, params={**kwargs})

    def request_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.requestOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def revoke_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeRoles(user, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def roles_of(self, user: ChecksumAddress) -> int:
        func = self.contract.functions.rolesOf(user)
        return await func.call()

    def set_account_fee_tiers(self, accounts: list[ChecksumAddress], fee_tiers: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setAccountFeeTiers(accounts, fee_tiers)
        return TypedContractFunction(func, params={**kwargs})

    def set_lot_size_in_base(self, market: ChecksumAddress, new_lot_size: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setLotSizeInBase(market, new_lot_size)
        return TypedContractFunction(func, params={**kwargs})

    def set_max_limits_exempt(self, accounts: list[ChecksumAddress], toggles: list[bool], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMaxLimitsExempt(accounts, toggles)
        return TypedContractFunction(func, params={**kwargs})

    def set_max_limits_per_tx(self, market: ChecksumAddress, new_max_limits: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMaxLimitsPerTx(market, new_max_limits)
        return TypedContractFunction(func, params={**kwargs})

    def set_min_limit_order_amount_in_base(self, market: ChecksumAddress, new_min_limit_order_amount_in_base: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMinLimitOrderAmountInBase(market, new_min_limit_order_amount_in_base)
        return TypedContractFunction(func, params={**kwargs})

    def set_tick_size(self, market: ChecksumAddress, new_tick_size: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setTickSize(market, new_tick_size)
        return TypedContractFunction(func, params={**kwargs})

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})