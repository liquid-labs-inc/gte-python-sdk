# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import ConfigParams, SettingsParams, SettleParams
from .events import AccountCreditedEvent, AccountDebitedEvent, AccountFeeTierUpdatedEvent, DepositEvent, FeeCollectedEvent, FeeRecipientSetEvent, InitializedEvent, MarketCreatedEvent, OperatorApprovedEvent, OperatorDisapprovedEvent, OwnershipHandoverCanceledEvent, OwnershipHandoverRequestedEvent, OwnershipTransferredEvent, WithdrawEvent


class ClobFactory:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("clob_factory")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    def approve_operator(self, operator: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approveOperator(operator)
        return TypedContractFunction(func, params={**kwargs})

    async def approved_operators(self, account: ChecksumAddress, operator: ChecksumAddress) -> bool:
        func = self.contract.functions.approvedOperators(account, operator)
        return await func.call()

    async def beacon(self) -> ChecksumAddress:
        func = self.contract.functions.beacon()
        return await func.call()

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def collect_fees(self, token: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.collectFees(token)
        return TypedContractFunction(func, params={**kwargs})

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        return TypedContractFunction(func, params={**kwargs})

    def create_market(self, base_token: ChecksumAddress, quote_token: ChecksumAddress, settings: SettingsParams, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.createMarket(base_token, quote_token, tuple(settings))
        return TypedContractFunction(func, params={**kwargs})

    def credit_account(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.creditAccount(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def debit_account(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.debitAccount(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def deposit(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, from_operator: bool, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.deposit(account, token, amount, from_operator)
        return TypedContractFunction(func, params={**kwargs})

    def disapprove_operator(self, operator: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.disapproveOperator(operator)
        return TypedContractFunction(func, params={**kwargs})

    async def get_account_balance(self, account: ChecksumAddress, token: ChecksumAddress) -> int:
        func = self.contract.functions.getAccountBalance(account, token)
        return await func.call()

    async def get_event_nonce(self) -> int:
        func = self.contract.functions.getEventNonce()
        return await func.call()

    async def get_fee_recipient(self) -> ChecksumAddress:
        func = self.contract.functions.getFeeRecipient()
        return await func.call()

    async def get_fee_tier(self, account: ChecksumAddress) -> int:
        func = self.contract.functions.getFeeTier(account)
        return await func.call()

    async def get_maker_fee_rate(self, fee_tier: int) -> Any:
        func = self.contract.functions.getMakerFeeRate(fee_tier)
        return await func.call()

    async def get_market_address(self, quote_token: ChecksumAddress, base_token: ChecksumAddress) -> ChecksumAddress:
        func = self.contract.functions.getMarketAddress(quote_token, base_token)
        return await func.call()

    async def get_taker_fee_rate(self, fee_tier: int) -> Any:
        func = self.contract.functions.getTakerFeeRate(fee_tier)
        return await func.call()

    def initialize(self, owner: ChecksumAddress, fee_recipient: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(owner, fee_recipient)
        return TypedContractFunction(func, params={**kwargs})

    async def is_market(self, market: ChecksumAddress) -> bool:
        func = self.contract.functions.isMarket(market)
        return await func.call()

    async def maker_fees(self) -> int:
        func = self.contract.functions.makerFees()
        return await func.call()

    async def max_num_orders(self) -> int:
        func = self.contract.functions.maxNumOrders()
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        func = self.contract.functions.ownershipHandoverExpiresAt(pending_owner)
        return await func.call()

    def pull_from_account(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.pullFromAccount(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def push_to_account(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.pushToAccount(account, token, amount)
        return TypedContractFunction(func, params={**kwargs})

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceOwnership()
        return TypedContractFunction(func, params={**kwargs})

    def request_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.requestOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def set_account_fee_tiers(self, accounts: list[ChecksumAddress], fee_tiers: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setAccountFeeTiers(accounts, fee_tiers)
        return TypedContractFunction(func, params={**kwargs})

    def set_fee_recipient(self, new_fee_recipient: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFeeRecipient(new_fee_recipient)
        return TypedContractFunction(func, params={**kwargs})

    def settle_incoming_order(self, params: SettleParams, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.settleIncomingOrder(tuple(params))
        return TypedContractFunction(func, params={**kwargs})

    async def taker_fees(self) -> int:
        func = self.contract.functions.takerFees()
        return await func.call()

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})

    def withdraw(self, account: ChecksumAddress, token: ChecksumAddress, amount: int, to_operator: bool, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.withdraw(account, token, amount, to_operator)
        return TypedContractFunction(func, params={**kwargs})