# This file is auto-generated. Do not edit manually.
from dataclasses import dataclass
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from typing import Any
from .structs import AmendArgs, BookSettingsPerp, ConfigParams, FundingRateSettingsPerp, MarketSettings, Order, SettingsParams

@dataclass
class AccountCreditedEvent:
    event_nonce: int
    account: ChecksumAddress
    token: ChecksumAddress
    amount: int

@dataclass
class AccountDebitedEvent:
    event_nonce: int
    account: ChecksumAddress
    token: ChecksumAddress
    amount: int

@dataclass
class AccountFeeTierUpdatedEvent:
    event_nonce: int
    account: ChecksumAddress
    new_tier: int

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
    asset: HexBytes
    order_id: int
    owner: ChecksumAddress
    book_type: int
    nonce: int

@dataclass
class CrossMarginDisabledEvent:
    asset: HexBytes
    nonce: int

@dataclass
class CrossMarginEnabledEvent:
    asset: HexBytes
    nonce: int

@dataclass
class DepositEvent:
    to: ChecksumAddress
    value: int

@dataclass
class DivergenceCapUpdatedEvent:
    asset: HexBytes
    divergence_cap: int
    nonce: int

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
class FeeTierUpdatedEvent:
    account: ChecksumAddress
    fee_tier: int
    nonce: int

@dataclass
class FeesAccruedEvent:
    event_nonce: int
    token: ChecksumAddress
    amount: int

@dataclass
class FeesClaimedEvent:
    event_nonce: int
    token: ChecksumAddress
    fee: int

@dataclass
class FundingClampsUpdatedEvent:
    asset: HexBytes
    inner_clamp: int
    outer_clamp: int
    nonce: int

@dataclass
class FundingIntervalUpdatedEvent:
    asset: HexBytes
    funding_interval: int
    reset_interval: int
    nonce: int

@dataclass
class FundingSettledEvent:
    asset: HexBytes
    funding: int
    cumulative_funding: int
    open_interest: int
    nonce: int

@dataclass
class InitializedEvent:
    version: int

@dataclass
class InsuranceFundDepositEvent:
    account: ChecksumAddress
    amount: int

@dataclass
class InsuranceFundWithdrawalEvent:
    account: ChecksumAddress
    amount: int

@dataclass
class InterestRateUpdatedEvent:
    asset: HexBytes
    interest_rate: int
    nonce: int

@dataclass
class LaunchpadDeployedEvent:
    quote_asset: ChecksumAddress
    bonding_curve: ChecksumAddress
    router: ChecksumAddress
    event_nonce: int

@dataclass
class LimitOrderCreatedEvent:
    event_nonce: int
    order_id: int
    price: int
    amount: int
    side: int

@dataclass
class LiquidationEvent:
    asset: HexBytes
    account: ChecksumAddress
    subaccount: int
    base_delta: int
    quote_delta: int
    rpnl: int
    margin: int
    fee: int
    liquidation_type: int
    nonce: int

@dataclass
class LiquidationFeeRateUpdatedEvent:
    asset: HexBytes
    liquidation_fee_rate: int
    nonce: int

@dataclass
class LotSizeInBaseUpdatedEvent:
    event_nonce: int
    new_lot_size_in_base: int

@dataclass
class MaintenanceMarginRatioUpdatedEvent:
    asset: HexBytes
    maintenance_margin_ratio: int
    nonce: int

@dataclass
class MakerFeeRatesUpdatedEvent:
    maker_fee_rates: list[Any]
    nonce: int

@dataclass
class MarginAddedEvent:
    account: ChecksumAddress
    subaccount: int
    amount: int
    new_margin: int
    nonce: int

@dataclass
class MarginRemovedEvent:
    account: ChecksumAddress
    subaccount: int
    amount: int
    new_margin: int
    nonce: int

@dataclass
class MarkPriceUpdatedEvent:
    asset: HexBytes
    mark_price: int
    p1: int
    p2: int
    p3: int
    nonce: int

@dataclass
class MarketCreatedEvent:
    asset: HexBytes
    market_settings: MarketSettings
    funding_settings: FundingRateSettingsPerp
    book_settings: BookSettingsPerp
    lot_size: int
    initial_price: int
    nonce: int

@dataclass
class MarketRegisteredEvent:
    event_nonce: int
    market: ChecksumAddress

@dataclass
class MarketStatusUpdatedEvent:
    asset: HexBytes
    status: int
    nonce: int

@dataclass
class MaxLeverageUpdatedEvent:
    asset: HexBytes
    max_open_leverage: int
    nonce: int

@dataclass
class MaxLimitOrdersPerTxUpdatedEvent:
    event_nonce: int
    new_max_limits: int

@dataclass
class MaxLimitsPerTxUpdatedEvent:
    asset: HexBytes
    max_limits_per_tx: int
    nonce: int

@dataclass
class MaxNumOrdersUpdatedEvent:
    asset: HexBytes
    max_num_orders: int
    nonce: int

@dataclass
class MinLimitOrderAmountInBaseUpdatedEvent:
    asset: HexBytes
    min_limit_order_amount_in_base: int
    nonce: int

@dataclass
class OperatorApprovedEvent:
    event_nonce: int
    account: ChecksumAddress
    operator: ChecksumAddress
    new_roles: int

@dataclass
class OperatorDisapprovedEvent:
    event_nonce: int
    account: ChecksumAddress
    operator: ChecksumAddress
    removed_roles: int

@dataclass
class OrderAmendedEvent:
    asset: HexBytes
    order_id: int
    new_order: Order
    collateral_delta: int
    book_type: int
    nonce: int

@dataclass
class OrderCanceledEvent:
    asset: HexBytes
    order_id: int
    owner: ChecksumAddress
    subaccount: int
    collateral_refunded: int
    book_type: int
    nonce: int

@dataclass
class OrderProcessedEvent:
    asset: HexBytes
    account: ChecksumAddress
    subaccount: int
    order_id: int
    amount_submitted: int
    base_denominated: bool
    tif: int
    expiry_time: int
    limit_price: int
    side: int
    reduce_only: bool
    base_posted: int
    quote_traded: int
    base_traded: int
    book_type: int
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
    old_owner: ChecksumAddress
    new_owner: ChecksumAddress

@dataclass
class PairCreatedEvent:
    token0: ChecksumAddress
    token1: ChecksumAddress
    pair: ChecksumAddress
    param: int

@dataclass
class PartialLiquidationRateUpdatedEvent:
    asset: HexBytes
    partial_liquidation_rate: int
    nonce: int

@dataclass
class PartialLiquidationThresholdUpdatedEvent:
    asset: HexBytes
    partial_liquidation_threshold: int
    nonce: int

@dataclass
class PositionLeverageSetEvent:
    asset: HexBytes
    account: ChecksumAddress
    subaccount: int
    new_leverage: int
    collateral_delta: int
    new_margin: int
    nonce: int

@dataclass
class ProtocolActivatedEvent:
    nonce: int

@dataclass
class ProtocolDeactivatedEvent:
    nonce: int

@dataclass
class QuoteAssetUpdatedEvent:
    old_quote_token: ChecksumAddress
    new_quote_token: ChecksumAddress
    new_quote_token_decimals: int
    event_nonce: int

@dataclass
class ReduceOnlyCapUpdatedEvent:
    asset: HexBytes
    reduce_only_cap: int
    nonce: int

@dataclass
class ResetIterationsUpdatedEvent:
    asset: HexBytes
    reset_iterations: int
    nonce: int

@dataclass
class RolesUpdatedEvent:
    user: ChecksumAddress
    roles: int

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
class TakerFeeRatesUpdatedEvent:
    taker_fee_rates: list[Any]
    nonce: int

@dataclass
class TickSizeUpdatedEvent:
    asset: HexBytes
    tick_size: int
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
    amount: int

@dataclass
class WithdrawalEvent:
    from_: ChecksumAddress
    value: int

