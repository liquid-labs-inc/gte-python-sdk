# This file is auto-generated. Do not edit manually.
from typing import NamedTuple, Any
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from enum import IntEnum

# Enums
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

    order_id: int
    amount_in_base: int
    price: int
    cancel_timestamp: int
    side: int

class AmendLimitOrderArgsPerp(NamedTuple):
    """Struct definition for AmendLimitOrderArgsPerp."""

    asset: HexBytes
    subaccount: int
    order_id: int
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

class CancelArgs(NamedTuple):
    """Struct definition for CancelArgs."""

    order_ids: list[int]

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
    bonding_curve: ChecksumAddress
    quote: ChecksumAddress
    unallocated_field_0: int
    unallocated_field_1: int
    base_sold_from_curve: int
    quote_bought_by_curve: int

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
    partial_liquidation_threshold: int
    partial_liquidation_rate: int
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

class Order(NamedTuple):
    """Struct definition for Order."""

    side: int
    cancel_timestamp: int
    id_: int
    prev_order_id: int
    next_order_id: int
    owner: ChecksumAddress
    price: int
    amount: int

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
    reduce_only: bool

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
    tif: int
    expiry_time: int
    limit_price: int
    amount: int
    base_denominated: bool

class PlaceOrderArgsPerp(NamedTuple):
    """Struct definition for PlaceOrderArgsPerp."""

    subaccount: int
    asset: HexBytes
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

    account: ChecksumAddress
    order_id: int
    base_posted: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int
    was_market_order: bool

class PlaceOrderResultPerp(NamedTuple):
    """Struct definition for PlaceOrderResultPerp."""

    order_id: int
    base_posted: int
    quote_traded: int
    base_traded: int

class PositionPerp(NamedTuple):
    """Struct definition for PositionPerp."""

    is_long: bool
    amount: int
    open_notional: int
    leverage: int
    last_cumulative_funding: int

class PostFillOrderArgs(NamedTuple):
    """Struct definition for PostFillOrderArgs."""

    amount: int
    price_limit: int
    side: int
    amount_is_base: bool
    fill_order_type: int
    settlement: int

class PostLimitOrderArgs(NamedTuple):
    """Struct definition for PostLimitOrderArgs."""

    amount_in_base: int
    price: int
    cancel_timestamp: int
    side: int
    client_order_id: int
    limit_order_type: int
    settlement: int

class SettingsParams(NamedTuple):
    """Struct definition for SettingsParams."""

    owner: ChecksumAddress
    max_limits_per_tx: int
    min_limit_order_amount_in_base: int
    tick_size: int

class SettleParams(NamedTuple):
    """Struct definition for SettleParams."""

    taker: ChecksumAddress
    quote_token: ChecksumAddress
    base_token: ChecksumAddress
    side: int
    settlement: int
    taker_quote_amount: int
    taker_base_amount: int
    maker_credits: list[Any]

class SignDataPerp(NamedTuple):
    """Struct definition for SignDataPerp."""

    sig: HexBytes
    nonce: int
    expiry: int

