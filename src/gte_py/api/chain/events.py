# This file is auto-generated. Do not edit manually.
from dataclasses import dataclass
from eth_typing import ChecksumAddress
from typing import Any
from hexbytes import HexBytes
from .structs import AmendArgs, ConfigParams, Order, OrderProcessedData, SettingsParams
from .structs import BookSettingsPerp, FundingRateSettingsPerp, MarketSettingsPerp, OrderPerp, OrderProcessedDataPerp

@dataclass
class AccountCreditedEvent:
    event_nonce: int
    account: ChecksumAddress
    token: ChecksumAddress
    amount: int
    new_balance: int

@dataclass
class AccountDebitedEvent:
    event_nonce: int
    account: ChecksumAddress
    token: ChecksumAddress
    amount: int
    new_balance: int

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
class BuilderCodeRegisteredEvent:
    nonce: int
    builder_code: HexBytes
    account: ChecksumAddress

@dataclass
class BuilderCodeRegisteredPerpEvent:
    account: ChecksumAddress
    builder_code: HexBytes
    nonce: int

@dataclass
class BuilderRevShareBpsUpdatedEvent:
    nonce: int
    new_builder_rev_share_bps: int

@dataclass
class BuilderRevShareBpsUpdatedPerpEvent:
    asset: HexBytes
    builder_rev_share_bps: int
    nonce: int

@dataclass
class BurnEvent:
    sender: ChecksumAddress
    amount0: int
    amount1: int
    to: ChecksumAddress

@dataclass
class CancelFailedEvent:
    event_nonce: int
    order_id: int
    owner: ChecksumAddress

@dataclass
class CancelFailedPerpEvent:
    asset: HexBytes
    order_id: int
    owner: ChecksumAddress
    book_type: int
    nonce: int

@dataclass
class ConditionalCanceledPerpEvent:
    account: ChecksumAddress
    conditional_nonces: list[int]
    nonce: int

@dataclass
class CrossMarginDisabledPerpEvent:
    asset: HexBytes
    nonce: int

@dataclass
class CrossMarginEnabledPerpEvent:
    asset: HexBytes
    nonce: int

@dataclass
class DepositEvent:
    to: ChecksumAddress
    value: int

@dataclass
class DepositPerpEvent:
    account: ChecksumAddress
    amount: int

@dataclass
class DivergenceCapUpdatedPerpEvent:
    asset: HexBytes
    divergence_cap: int
    nonce: int

@dataclass
class FeeTierUpdatedPerpEvent:
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
class FundingClampsUpdatedPerpEvent:
    asset: HexBytes
    inner_clamp: int
    outer_clamp: int
    nonce: int

@dataclass
class FundingIntervalUpdatedPerpEvent:
    asset: HexBytes
    funding_interval: int
    reset_interval: int
    nonce: int

@dataclass
class FundingSettledPerpEvent:
    asset: HexBytes
    funding: int
    cumulative_funding: int
    open_interest: int
    nonce: int

@dataclass
class IndexFairClampUpdatedPerpEvent:
    asset: HexBytes
    index_fair_clamp: int
    nonce: int

@dataclass
class InitializedEvent:
    version: int

@dataclass
class InitializedPerpEvent:
    version: int

@dataclass
class InsuranceFundDepositPerpEvent:
    account: ChecksumAddress
    amount: int

@dataclass
class InsuranceFundWithdrawalPerpEvent:
    account: ChecksumAddress
    amount: int

@dataclass
class InterestRateUpdatedPerpEvent:
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
class LiquidationFeeRateUpdatedPerpEvent:
    asset: HexBytes
    liquidation_fee_rate: int
    nonce: int

@dataclass
class LiquidationPerpEvent:
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
class LiquidatorPointsSetPerpEvent:
    account: ChecksumAddress
    points: int
    nonce: int

@dataclass
class LotSizeInBaseUpdatedEvent:
    event_nonce: int
    new_lot_size_in_base: int

@dataclass
class MaintenanceMarginRatioUpdatedPerpEvent:
    asset: HexBytes
    maintenance_margin_ratio: int
    nonce: int

@dataclass
class MakerFeeRatesUpdatedPerpEvent:
    maker_fee_rates: list[Any]
    nonce: int

@dataclass
class MarginAddedPerpEvent:
    account: ChecksumAddress
    subaccount: int
    amount: int
    new_margin: int
    nonce: int

@dataclass
class MarginRemovedPerpEvent:
    account: ChecksumAddress
    subaccount: int
    amount: int
    new_margin: int
    nonce: int

@dataclass
class MarkPriceUpdatedPerpEvent:
    asset: HexBytes
    mark_price: int
    index_fair: int
    impact_price: int
    micro_price: int
    nonce: int

@dataclass
class MarketCreatedEvent:
    event_nonce: int
    creator: ChecksumAddress
    base_token: ChecksumAddress
    quote_token: ChecksumAddress
    market: ChecksumAddress
    quote_decimals: int
    base_decimals: int
    config: ConfigParams
    settings: SettingsParams

@dataclass
class MarketCreatedPerpEvent:
    asset: HexBytes
    market_settings: MarketSettingsPerp
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
class MarketStatusUpdatedPerpEvent:
    asset: HexBytes
    status: int
    nonce: int

@dataclass
class MaxLeverageUpdatedPerpEvent:
    asset: HexBytes
    max_open_leverage: int
    nonce: int

@dataclass
class MaxLimitOrdersPerTxUpdatedEvent:
    event_nonce: int
    new_max_limits: int

@dataclass
class MaxLimitsPerTxUpdatedPerpEvent:
    asset: HexBytes
    max_limits_per_tx: int
    nonce: int

@dataclass
class MaxNumOrdersUpdatedPerpEvent:
    asset: HexBytes
    max_num_orders: int
    nonce: int

@dataclass
class MicroPriceClipBpsUpdatedPerpEvent:
    asset: HexBytes
    micro_price_clip_bps: int
    nonce: int

@dataclass
class MinLimitOrderAmountInBaseUpdatedEvent:
    event_nonce: int
    new_min_limit_order_amount_in_base: int

@dataclass
class MinLimitOrderAmountInBaseUpdatedPerpEvent:
    asset: HexBytes
    min_limit_order_amount_in_base: int
    nonce: int

@dataclass
class MintEvent:
    sender: ChecksumAddress
    amount0: int
    amount1: int

@dataclass
class OperatorApprovedEvent:
    event_nonce: int
    account: ChecksumAddress
    operator: ChecksumAddress
    new_roles: int

@dataclass
class OperatorApprovedPerpEvent:
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
class OperatorDisapprovedPerpEvent:
    event_nonce: int
    account: ChecksumAddress
    operator: ChecksumAddress
    removed_roles: int

@dataclass
class OrderAmendedEvent:
    event_nonce: int
    pre_amend: Order
    args: AmendArgs
    quote_token_delta: int
    base_token_delta: int
    maker_fee_rate: Any

@dataclass
class OrderAmendedPerpEvent:
    asset: HexBytes
    order_id: int
    new_order: OrderPerp
    collateral_delta: int
    book_type: int
    nonce: int

@dataclass
class OrderCanceledEvent:
    event_nonce: int
    order_id: int
    owner: ChecksumAddress
    quote_token_refunded: int
    base_token_refunded: int
    context: int

@dataclass
class OrderCanceledPerpEvent:
    asset: HexBytes
    order_id: int
    owner: ChecksumAddress
    subaccount: int
    collateral_refunded: int
    book_type: int
    nonce: int

@dataclass
class OrderProcessedEvent:
    event_nonce: int
    account: ChecksumAddress
    order_id: int
    data: OrderProcessedData

@dataclass
class OrderProcessedPerpEvent:
    asset: HexBytes
    account: ChecksumAddress
    order_id: int
    nonce: int
    data: OrderProcessedDataPerp

@dataclass
class OwnershipHandoverCanceledEvent:
    pending_owner: ChecksumAddress

@dataclass
class OwnershipHandoverCanceledPerpEvent:
    pending_owner: ChecksumAddress

@dataclass
class OwnershipHandoverRequestedEvent:
    pending_owner: ChecksumAddress

@dataclass
class OwnershipHandoverRequestedPerpEvent:
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
class OwnershipTransferredPerpEvent:
    old_owner: ChecksumAddress
    new_owner: ChecksumAddress

@dataclass
class PairCreatedEvent:
    token0: ChecksumAddress
    token1: ChecksumAddress
    token0_decimals: int
    token1_decimals: int
    pair: ChecksumAddress
    param: int

@dataclass
class PartialLiquidationRateUpdatedPerpEvent:
    asset: HexBytes
    partial_liquidation_rate: int
    nonce: int

@dataclass
class PartialLiquidationThresholdUpdatedPerpEvent:
    asset: HexBytes
    partial_liquidation_threshold: int
    nonce: int

@dataclass
class PositionLeverageSetPerpEvent:
    asset: HexBytes
    account: ChecksumAddress
    subaccount: int
    new_leverage: int
    collateral_delta: int
    new_margin: int
    nonce: int

@dataclass
class ProtocolActivatedPerpEvent:
    nonce: int

@dataclass
class ProtocolDeactivatedPerpEvent:
    nonce: int

@dataclass
class QuoteAssetUpdatedEvent:
    old_quote_token: ChecksumAddress
    new_quote_token: ChecksumAddress
    new_quote_token_decimals: int
    event_nonce: int

@dataclass
class ReduceOnlyCapUpdatedPerpEvent:
    asset: HexBytes
    reduce_only_cap: int
    nonce: int

@dataclass
class RemoveExemptFromLimitPerTxCapPerpEvent:
    account: ChecksumAddress
    nonce: int

@dataclass
class ResetIterationsUpdatedPerpEvent:
    asset: HexBytes
    reset_iterations: int
    nonce: int

@dataclass
class RolesUpdatedEvent:
    user: ChecksumAddress
    roles: int

@dataclass
class RolesUpdatedPerpEvent:
    user: ChecksumAddress
    roles: int

@dataclass
class SetExemptFromLimitPerTxCapPerpEvent:
    account: ChecksumAddress
    nonce: int

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
class SyncEvent:
    reserve0: Any
    reserve1: Any

@dataclass
class TakerFeeRatesUpdatedPerpEvent:
    taker_fee_rates: list[Any]
    nonce: int

@dataclass
class TickSizeUpdatedEvent:
    event_nonce: int
    new_tick_size: int

@dataclass
class TickSizeUpdatedPerpEvent:
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
    event_nonce: int

@dataclass
class TransferEvent:
    from_: ChecksumAddress
    to: ChecksumAddress
    value: int

@dataclass
class TwapCanceledPerpEvent:
    account: ChecksumAddress
    root: HexBytes
    nonce: int

@dataclass
class WithdrawPerpEvent:
    account: ChecksumAddress
    amount: int

@dataclass
class WithdrawalEvent:
    from_: ChecksumAddress
    value: int

