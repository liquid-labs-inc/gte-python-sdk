# This file is auto-generated. Do not edit manually.
from typing import NamedTuple, Any
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from enum import IntEnum

# Enums
class BookType(IntEnum):
    STANDARD = 0
    BACKSTOP = 1

class CancelType(IntEnum):
    USER = 0
    EXPIRY = 1
    NON_COMPETITIVE = 2

class FeeTier(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2

class FeeTiers(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2

class FillOrderType(IntEnum):
    MARKET = 0
    LIMIT = 1

class LimitOrderType(IntEnum):
    GOOD_TILL_CANCELLED = 0
    POST_ONLY = 1

class LiquidationType(IntEnum):
    LIQUIDATEE = 0
    BACKSTOP_LIQUIDATEE = 1
    DELIST = 2
    DELEVERAGE_MAKER = 3
    DELEVERAGE_TAKER = 4

class Settlement(IntEnum):
    INSTANT = 0
    ACCOUNT = 1

class Side(IntEnum):
    BUY = 0
    SELL = 1

class Status(IntEnum):
    NULL = 0
    INACTIVE = 1
    ACTIVE = 2
    DELISTED = 3

class TiF(IntEnum):
    GTC = 0
    MOC = 1
    FOK = 2
    IOC = 3

# Structs
class AmendArgs(NamedTuple):
    """Struct definition for AmendArgs."""

    order_or_client_id: int
    amount_in_base: int
    price: int
    cancel_timestamp: int
    side: int

class AmendLimitOrderArgsPerp(NamedTuple):
    """Struct definition for AmendLimitOrderArgsPerp."""

    asset: HexBytes
    subaccount: int
    order_or_client_id: int
    base_amount: int
    price: int
    expiry_time: int
    side: int
    reduce_only: bool

class BookSettingsPerp(NamedTuple):
    """Struct definition for BookSettingsPerp."""

    max_num_orders: int
    max_limits_per_tx: int
    min_limit_order_amount_in_base: int
    tick_size: int

class ConditionPerp(NamedTuple):
    """Struct definition for ConditionPerp."""

    trigger_price: int
    stop_loss: bool

class ConfigParams(NamedTuple):
    """Struct definition for ConfigParams."""

    quote_token: ChecksumAddress
    base_token: ChecksumAddress
    quote_size: int
    base_size: int

class FundingRateSettingsPerp(NamedTuple):
    """Struct definition for FundingRateSettingsPerp."""

    funding_interval: int
    reset_interval: int
    reset_iterations: int
    inner_clamp: int
    outer_clamp: int
    interest_rate: int

class LaunchData(NamedTuple):
    """Struct definition for LaunchData."""

    active: bool
    is_fee_sharing: bool
    quote: ChecksumAddress
    curve: ChecksumAddress
    pair: ChecksumAddress

class Limit(NamedTuple):
    """Struct definition for Limit."""

    num_orders: int
    head_order: int
    tail_order: int

class MarketConfig(NamedTuple):
    """Struct definition for MarketConfig."""

    quote_token: ChecksumAddress
    base_token: ChecksumAddress
    quote_size: int
    base_size: int

class MarketParamsPerp(NamedTuple):
    """Struct definition for MarketParamsPerp."""

    max_open_leverage: int
    maintenance_margin_ratio: int
    liquidation_fee_rate: int
    divergence_cap: int
    reduce_only_cap: int
    builder_rev_share_bps: int
    partial_liquidation_threshold: int
    partial_liquidation_rate: int
    index_fair_clamp: int
    micro_price_clip_bps: int
    cross_margin_enabled: bool
    funding_interval: int
    reset_interval: int
    reset_iterations: int
    inner_clamp: int
    outer_clamp: int
    interest_rate: int
    max_num_orders: int
    max_limits_per_tx: int
    min_limit_order_amount_in_base: int
    tick_size: int
    lot_size: int
    initial_price: int

class MarketSettings(NamedTuple):
    """Struct definition for MarketSettings."""

    status: bool
    max_limits_per_tx: int
    min_limit_order_amount_in_base: int
    tick_size: int
    lot_size_in_base: int
    builder_rev_share_bps: int

class MarketSettingsPerp(NamedTuple):
    """Struct definition for MarketSettingsPerp."""

    status: int
    cross_margin_enabled: bool
    max_open_leverage: int
    maintenance_margin_ratio: int
    liquidation_fee_rate: int
    divergence_cap: int
    reduce_only_cap: int
    partial_liquidation_threshold: int
    partial_liquidation_rate: int
    index_fair_clamp: int
    micro_price_clip_bps: int
    builder_rev_share_bps: int

class MerkleDataPerp(NamedTuple):
    """Struct definition for MerkleDataPerp."""

    proof: list[HexBytes]
    root: HexBytes
    signature: HexBytes

class Order(NamedTuple):
    """Struct definition for Order."""

    side: int
    cancel_timestamp: int
    maker_fee_rate: Any
    id_: int
    prev_order_id: int
    next_order_id: int
    owner: ChecksumAddress
    price: int
    amount: int
    builder_code: HexBytes

class OrderPerp(NamedTuple):
    """Struct definition for OrderPerp."""

    side: int
    expiry_time: int
    id_: int
    prev_order_id: int
    next_order_id: int
    owner: ChecksumAddress
    price: int
    amount: int
    subaccount: int
    builder_code: HexBytes
    reduce_only: bool

class OrderProcessedData(NamedTuple):
    """Struct definition for OrderProcessedData."""

    base_posted: int
    base_traded: int
    quote_traded: int
    taker_fee_charged: int
    taker_fee_rate: Any
    maker_fee_rate: Any
    start_order_id: int
    end_order_id: int
    makers_cleared: int
    side: int
    client_order_id: int
    tif: int
    expiry_time: int
    limit_price: int
    amount: int
    builder_code: HexBytes

class OrderProcessedDataPerp(NamedTuple):
    """Struct definition for OrderProcessedDataPerp."""

    base_posted: int
    quote_traded: int
    base_traded: int
    book_type: int
    liquidation: bool
    start_order_id: int
    end_order_id: int
    makers_cleared: int
    client_order_id: int
    subaccount: int
    amount_submitted: int
    reduce_only: bool
    base_denominated: bool
    tif: int
    expiry_time: int
    limit_price: int
    side: int
    builder_code: HexBytes

class PermitDetails(NamedTuple):
    """Struct definition for PermitDetails."""

    token: ChecksumAddress
    amount: int
    expiration: int
    nonce: int

class PermitSingle(NamedTuple):
    """Struct definition for PermitSingle."""

    details: PermitDetails
    spender: ChecksumAddress
    sig_deadline: int

class PlaceOrderArgs(NamedTuple):
    """Struct definition for PlaceOrderArgs."""

    side: int
    client_order_id: int
    builder_code: HexBytes
    tif: int
    expiry_time: int
    limit_price: int
    amount: int
    base_denominated: bool

class PlaceOrderArgsPerp(NamedTuple):
    """Struct definition for PlaceOrderArgsPerp."""

    subaccount: int
    asset: HexBytes
    builder_code: HexBytes
    side: int
    limit_price: int
    amount: int
    base_denominated: bool
    tif: int
    expiry_time: int
    client_order_id: int
    reduce_only: bool

class PlaceOrderResult(NamedTuple):
    """Struct definition for PlaceOrderResult."""

    order_id: int
    base_posted: int
    base_traded: int
    quote_traded: int
    taker_fee_charged: int

class PlaceOrderResultPerp(NamedTuple):
    """Struct definition for PlaceOrderResultPerp."""

    order_id: int
    base_posted: int
    base_traded: int
    quote_traded: int

class PositionPerp(NamedTuple):
    """Struct definition for PositionPerp."""

    is_long: bool
    amount: int
    open_notional: int
    leverage: int
    last_cumulative_funding: int

class SettingsParams(NamedTuple):
    """Struct definition for SettingsParams."""

    owner: ChecksumAddress
    max_limits_per_tx: int
    min_limit_order_amount_in_base: int
    tick_size: int
    lot_size_in_base: int
    builder_rev_share_bps: int

class SettleParams(NamedTuple):
    """Struct definition for SettleParams."""

    side: int
    taker: ChecksumAddress
    taker_fee_rate: Any
    taker_builder_code: HexBytes
    taker_base_amount: int
    taker_quote_amount: int
    base_token: ChecksumAddress
    quote_token: ChecksumAddress
    builder_rev_share_bps: int
    maker_credits: list[Any]

class SignDataPerp(NamedTuple):
    """Struct definition for SignDataPerp."""

    sig: HexBytes
    nonce: int
    expiry: int

class SwapData(NamedTuple):
    """Struct definition for SwapData."""

    amount0_out: int
    amount1_out: int
    to: ChecksumAddress
    user: ChecksumAddress
    data: HexBytes

class TwapOrderArgsPerp(NamedTuple):
    """Struct definition for TwapOrderArgsPerp."""

    asset: HexBytes
    account: ChecksumAddress
    subaccount: int
    amount: int
    slippage_pct: int
    min_time: int
    expiry_time: int
    base_denominated: bool
    reduce_only: bool
    side: int
    tif: int
    client_order_id: int

