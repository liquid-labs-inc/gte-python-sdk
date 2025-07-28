# This file is auto-generated. Do not edit manually.
from dataclasses import dataclass
from eth_typing import ChecksumAddress
from .structs import AmendArgs, ConfigParams, Order, PostFillOrderArgs, PostLimitOrderArgs, SettingsParams

@dataclass
class AccountCreditedEvent:
    account: ChecksumAddress
    token: ChecksumAddress
    amount: int
    event_nonce: int

@dataclass
class AccountDebitedEvent:
    account: ChecksumAddress
    token: ChecksumAddress
    amount: int
    event_nonce: int

@dataclass
class AccountFeeTierUpdatedEvent:
    account: ChecksumAddress
    fee_tier: int
    event_nonce: int

@dataclass
class ApprovalEvent:
    from_: ChecksumAddress
    spender: ChecksumAddress
    value: int

@dataclass
class BondingCurveUpdatedEvent:
    old_curve: ChecksumAddress
    new_curve: ChecksumAddress
    event_nonce: int

@dataclass
class BondingLockedEvent:
    token: ChecksumAddress
    pair_address: ChecksumAddress
    event_nonce: int

@dataclass
class CancelFailedEvent:
    order_id: int
    owner: ChecksumAddress
    nonce: int

@dataclass
class DepositEvent:
    to: ChecksumAddress
    value: int

@dataclass
class FeeCollectedEvent:
    token: ChecksumAddress
    fee: int
    event_nonce: int

@dataclass
class FeeRecipientSetEvent:
    fee_recipient: ChecksumAddress
    event_nonce: int

@dataclass
class FillOrderProcessedEvent:
    account: ChecksumAddress
    order_id: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int
    nonce: int

@dataclass
class FillOrderSubmittedEvent:
    owner: ChecksumAddress
    order_id: int
    args: PostFillOrderArgs
    nonce: int

@dataclass
class InitializedEvent:
    version: int

@dataclass
class LaunchpadDeployedEvent:
    quote_asset: ChecksumAddress
    bonding_curve: ChecksumAddress
    router: ChecksumAddress
    event_nonce: int

@dataclass
class LimitOrderProcessedEvent:
    account: ChecksumAddress
    order_id: int
    amount_posted_in_base: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int
    nonce: int

@dataclass
class LimitOrderSubmittedEvent:
    owner: ChecksumAddress
    order_id: int
    args: PostLimitOrderArgs
    nonce: int

@dataclass
class MarketCreatedEvent:
    creator: ChecksumAddress
    base_token: ChecksumAddress
    quote_token: ChecksumAddress
    market: ChecksumAddress
    quote_decimals: int
    base_decimals: int
    config: ConfigParams
    settings: SettingsParams
    event_nonce: int

@dataclass
class MaxLimitOrdersAllowlistedEvent:
    account: ChecksumAddress
    toggle: bool
    nonce: int

@dataclass
class MaxLimitOrdersPerTxUpdatedEvent:
    new_max_limits: int
    nonce: int

@dataclass
class MinLimitOrderAmountInBaseUpdatedEvent:
    new_min_limit_order_amount_in_base: int
    nonce: int

@dataclass
class OperatorApprovedEvent:
    account: ChecksumAddress
    operator: ChecksumAddress
    event_nonce: int

@dataclass
class OperatorDisapprovedEvent:
    account: ChecksumAddress
    operator: ChecksumAddress
    event_nonce: int

@dataclass
class OrderAmendedEvent:
    pre_amend: Order
    args: AmendArgs
    quote_token_delta: int
    base_token_delta: int
    event_nonce: int

@dataclass
class OrderCanceledEvent:
    order_id: int
    owner: ChecksumAddress
    quote_token_refunded: int
    base_token_refunded: int
    settlement: int
    nonce: int

@dataclass
class OrderMatchedEvent:
    taker_order_id: int
    maker_order_id: int
    taker_order: Order
    maker_order: Order
    traded_base: int
    nonce: int

@dataclass
class OwnershipHandoverCanceledEvent:
    pending_owner: ChecksumAddress

@dataclass
class OwnershipHandoverRequestedEvent:
    pending_owner: ChecksumAddress

@dataclass
class OwnershipTransferStartedEvent:
    previous_owner: ChecksumAddress
    new_owner: ChecksumAddress

@dataclass
class OwnershipTransferredEvent:
    previous_owner: ChecksumAddress
    new_owner: ChecksumAddress

@dataclass
class PairCreatedEvent:
    token0: ChecksumAddress
    token1: ChecksumAddress
    pair: ChecksumAddress
    param: int

@dataclass
class QuoteAssetUpdatedEvent:
    old_quote_token: ChecksumAddress
    new_quote_token: ChecksumAddress
    new_quote_token_decimals: int
    event_nonce: int

@dataclass
class RolesApprovedEvent:
    account: ChecksumAddress
    operator: ChecksumAddress
    roles: int
    event_nonce: int

@dataclass
class RolesDisapprovedEvent:
    account: ChecksumAddress
    operator: ChecksumAddress
    roles: int
    event_nonce: int

@dataclass
class SwapEvent:
    buyer: ChecksumAddress
    token: ChecksumAddress
    base_delta: int
    quote_delta: int
    next_amount_sold: int
    new_price: int
    event_nonce: int

@dataclass
class TickSizeUpdatedEvent:
    new_tick_size: int
    nonce: int

@dataclass
class TokenLaunchedEvent:
    dev: ChecksumAddress
    token: ChecksumAddress
    quote_asset: ChecksumAddress
    bonding_curve: ChecksumAddress
    timestamp: int
    quote_scaling: int
    event_nonce: int

@dataclass
class TransferEvent:
    from_: ChecksumAddress
    to: ChecksumAddress
    value: int

@dataclass
class WithdrawEvent:
    account: ChecksumAddress
    recipient: ChecksumAddress
    token: ChecksumAddress
    amount: int
    event_nonce: int

@dataclass
class WithdrawalEvent:
    from_: ChecksumAddress
    value: int

