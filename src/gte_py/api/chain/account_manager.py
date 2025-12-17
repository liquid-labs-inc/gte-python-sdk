# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import SettleParams
from .events import AccountCreditedEvent, AccountDebitedEvent, AccountFeeTierUpdatedEvent, BuilderCodeRegisteredEvent, FeesAccruedEvent, FeesClaimedEvent, InitializedEvent, MarketRegisteredEvent, OperatorApprovedEvent, OperatorDisapprovedEvent, OwnershipHandoverCanceledEvent, OwnershipHandoverRequestedEvent, OwnershipTransferredEvent, RolesUpdatedEvent


class AccountManager:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("account_manager")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def admin(self) -> int:
        func = self.contract.functions.ADMIN()
        return await func.call()

    def accrue_fee(self, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.accrueFee(token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def accrue_launch_fee(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.accrueLaunchFee(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def approve_operator(self, account: ChecksumAddress, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approveOperator(account, operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    async def clob_manager(self) -> ChecksumAddress:
        func = self.contract.functions.clobManager()
        return await func.call()

    def collect_fees(self, token: ChecksumAddress, fee_recipient: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.collectFees(token, fee_recipient)
        return TypedContractFunction(func, params={**kwargs})

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        return TypedContractFunction(func, params={**kwargs})

    def credit_account(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.creditAccount(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def credit_account_no_event(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.creditAccountNoEvent(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def debit_account(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.debitAccount(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def deposit(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.deposit(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def deposit_from_perps(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.depositFromPerps(account, amount)
        return TypedContractFunction(func, params={**kwargs})

    def deposit_to(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.depositTo(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def disapprove_operator(self, account: ChecksumAddress, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.disapproveOperator(account, operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def distributor(self) -> ChecksumAddress:
        func = self.contract.functions.distributor()
        return await func.call()

    async def get_account_balance(self, account: ChecksumAddress, token: ChecksumAddress) -> int:
        func = self.contract.functions.getAccountBalance(account, token)
        return await func.call()

    async def get_account_balances(self, accounts: list[ChecksumAddress], tokens: list[ChecksumAddress]) -> list[int]:
        func = self.contract.functions.getAccountBalances(accounts, tokens)
        return await func.call()

    async def get_builder_code_owner(self, builder_code: HexBytes) -> ChecksumAddress:
        func = self.contract.functions.getBuilderCodeOwner(builder_code)
        return await func.call()

    async def get_event_nonce(self) -> int:
        func = self.contract.functions.getEventNonce()
        return await func.call()

    async def get_fee_rates_for_account(self, account: ChecksumAddress) -> tuple[Any, Any]:
        """
        Returns:
            tuple: (maker_rate, taker_rate)
        """
        func = self.contract.functions.getFeeRatesForAccount(account)
        return await func.call()

    async def get_fee_rates_for_tier(self, tier: int) -> tuple[Any, Any]:
        """
        Returns:
            tuple: (maker_rate, taker_rate)
        """
        func = self.contract.functions.getFeeRatesForTier(tier)
        return await func.call()

    async def get_fee_tier(self, account: ChecksumAddress) -> int:
        func = self.contract.functions.getFeeTier(account)
        return await func.call()

    async def get_operator_event_nonce(self) -> int:
        func = self.contract.functions.getOperatorEventNonce()
        return await func.call()

    async def get_operator_role_approvals(self, account: ChecksumAddress, operator: ChecksumAddress) -> int:
        func = self.contract.functions.getOperatorRoleApprovals(account, operator)
        return await func.call()

    async def get_spot_maker_fee_rate_for_tier(self, tier: int) -> int:
        func = self.contract.functions.getSpotMakerFeeRateForTier(tier)
        return await func.call()

    async def get_spot_taker_fee_rate_for_tier(self, tier: int) -> int:
        func = self.contract.functions.getSpotTakerFeeRateForTier(tier)
        return await func.call()

    async def get_total_fees(self, token: ChecksumAddress) -> int:
        func = self.contract.functions.getTotalFees(token)
        return await func.call()

    async def get_unclaimed_fees(self, token: ChecksumAddress) -> int:
        func = self.contract.functions.getUnclaimedFees(token)
        return await func.call()

    def grant_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantRoles(user, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def gte_router(self) -> ChecksumAddress:
        func = self.contract.functions.gteRouter()
        return await func.call()

    async def has_all_roles(self, user: ChecksumAddress, roles: int) -> bool:
        func = self.contract.functions.hasAllRoles(user, roles)
        return await func.call()

    async def has_any_role(self, user: ChecksumAddress, roles: int) -> bool:
        func = self.contract.functions.hasAnyRole(user, roles)
        return await func.call()

    def initialize(self, owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(owner)
        return TypedContractFunction(func, params={**kwargs})

    async def launchpad(self) -> ChecksumAddress:
        func = self.contract.functions.launchpad()
        return await func.call()

    async def operator_hub(self) -> ChecksumAddress:
        func = self.contract.functions.operatorHub()
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        func = self.contract.functions.ownershipHandoverExpiresAt(pending_owner)
        return await func.call()

    async def perp_manager(self) -> ChecksumAddress:
        func = self.contract.functions.perpManager()
        return await func.call()

    def register_builder_code(self, account: ChecksumAddress, builder_code: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.registerBuilderCode(account, builder_code)
        return TypedContractFunction(func, params={**kwargs})

    def register_market(self, market: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.registerMarket(market)
        return TypedContractFunction(func, params={**kwargs})

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

    def set_spot_account_fee_tier(self, account: ChecksumAddress, fee_tier: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setSpotAccountFeeTier(account, fee_tier)
        return TypedContractFunction(func, params={**kwargs})

    def set_spot_account_fee_tiers(self, accounts: list[ChecksumAddress], fee_tiers: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setSpotAccountFeeTiers(accounts, fee_tiers)
        return TypedContractFunction(func, params={**kwargs})

    def settle_incoming_order(self, params: SettleParams, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.settleIncomingOrder(tuple(params))
        return TypedContractFunction(func, params={**kwargs})

    async def spot_maker_fee_rates(self) -> int:
        func = self.contract.functions.spotMakerFeeRates()
        return await func.call()

    async def spot_taker_fee_rates(self) -> int:
        func = self.contract.functions.spotTakerFeeRates()
        return await func.call()

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})

    def unregister_builder_code(self, builder_code: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.unregisterBuilderCode(builder_code)
        return TypedContractFunction(func, params={**kwargs})

    async def weth(self) -> ChecksumAddress:
        func = self.contract.functions.weth()
        return await func.call()

    def withdraw(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.withdraw(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def withdraw_from(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.withdrawFrom(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})