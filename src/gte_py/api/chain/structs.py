# This file is auto-generated. Do not edit manually.
from typing import NamedTuple, Any
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from enum import IntEnum

# Enums
class FeeTiers(IntEnum):
    # TODO: Add actual enum values for FeeTiers
    # Example: VALUE_NAME = 0
    pass

class FillOrderType(IntEnum):
    IMMEDIATE_OR_CANCEL = 0
    FILL_OR_KILL = 1

class LimitOrderType(IntEnum):
    GOOD_TILL_CANCELLED = 0
    POST_ONLY = 1

class Settlement(IntEnum):
    INSTANT = 0
    ACCOUNT = 1

class OrderSide(IntEnum):
    BUY = 0
    SELL = 1

class OperatorRole(IntEnum):
    ADMIN = 1
    DEPOSIT = 2
    WITHDRAW = 4
    LAUNCHPAD_FILL = 8

# Structs
class AmendArgs(NamedTuple):
    """Struct definition for AmendArgs."""

    order_id: int
    amount_in_base: int
    price: int
    cancel_timestamp: int
    side: int
    limit_order_type: int
    settlement: int

class CancelArgs(NamedTuple):
    """Struct definition for CancelArgs."""

    order_ids: list[int]
    settlement: int

class ConfigParams(NamedTuple):
    """Struct definition for ConfigParams."""

    quote_token: ChecksumAddress
    base_token: ChecksumAddress
    quote_size: int
    base_size: int

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

    factory: ChecksumAddress
    max_num_orders: int
    quote_token: ChecksumAddress
    base_token: ChecksumAddress
    quote_size: int
    base_size: int

class MarketSettings(NamedTuple):
    """Struct definition for MarketSettings."""

    status: bool
    max_limits_per_tx: int
    min_limit_order_amount_in_base: int
    tick_size: int

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

class PostFillOrderArgs(NamedTuple):
    """Struct definition for PostFillOrderArgs."""

    amount: int
    price_limit: int
    side: int
    amount_is_base: bool
    fill_order_type: int
    settlement: int

class PostFillOrderResult(NamedTuple):
    """Struct definition for PostFillOrderResult."""

    account: ChecksumAddress
    order_id: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int

class PostLimitOrderArgs(NamedTuple):
    """Struct definition for PostLimitOrderArgs."""

    amount_in_base: int
    price: int
    cancel_timestamp: int
    side: int
    client_order_id: int
    limit_order_type: int
    settlement: int

class PostLimitOrderResult(NamedTuple):
    """Struct definition for PostLimitOrderResult."""

    account: ChecksumAddress
    order_id: int
    amount_posted_in_base: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int

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

