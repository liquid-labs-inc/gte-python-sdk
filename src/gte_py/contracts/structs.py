"""Structure definitions for GTE contracts."""

from enum import IntEnum
from typing import TypedDict


class Side(IntEnum):
    """Order side enum."""

    BUY = 0
    SELL = 1


class Settlement(IntEnum):
    """Settlement type enum."""

    NONE = 0
    INSTANT = 1


class LimitOrderType(IntEnum):
    """Limit order type enum."""

    GOOD_TILL_CANCELLED = 0
    IMMEDIATE_OR_CANCEL = 1
    FILL_OR_KILL = 2
    GOOD_TILL_TIME = 3


class FillOrderType(IntEnum):
    """Fill order type enum."""

    IMMEDIATE_OR_CANCEL = 0
    FILL_OR_KILL = 1


# Token permissions and permit structures for allowance transfers
class TokenPermissions(TypedDict):
    """Token permission definition."""

    token: str
    amount: int


class PermitDetails(TypedDict):
    """Permit details for Permit2."""

    token: str
    amount: int
    expiration: int
    nonce: int


class PermitSingle(TypedDict):
    """PermitSingle struct for Permit2."""

    details: PermitDetails
    spender: str
    sigDeadline: int


# Basic order arguments
class PostLimitOrderArgs(TypedDict):
    """Arguments for posting a limit order to router."""

    isBuy: int
    tokenInOutAmt: int
    tokenOutInAmt: int
    deadline: int


class PostFillOrderArgs(TypedDict):
    """Arguments for posting a fill order to router."""

    isBuy: int
    tokenInOutAmt: int
    tokenOutInAmt: int
    deadline: int
    orderIds: list[int]


class CancelArgs(TypedDict):
    """Arguments for canceling orders through router."""

    isBuy: int
    orderId: int


# CLOB specific structures
class ICLOBPostLimitOrderArgs(TypedDict):
    """Arguments for posting a limit order."""

    amountInBase: int
    price: int
    cancelTimestamp: int
    side: int
    clientOrderId: int
    limitOrderType: int
    settlement: int


class ICLOBPostLimitOrderResult(TypedDict):
    """Result from posting a limit order."""

    account: str
    orderId: int
    amountPostedInBase: int
    quoteTokenAmountTraded: int
    baseTokenAmountTraded: int
    takerFee: int


class ICLOBPostFillOrderArgs(TypedDict):
    """Arguments for posting a fill order."""

    amount: int
    priceLimit: int
    side: int
    amountIsBase: bool
    fillOrderType: int
    settlement: int


class ICLOBPostFillOrderResult(TypedDict):
    """Result from posting a fill order."""

    account: str
    orderId: int
    quoteTokenAmountTraded: int
    baseTokenAmountTraded: int
    takerFee: int


class ICLOBAmendArgs(TypedDict):
    """Arguments for amending an order."""

    orderId: int
    amountInBase: int
    price: int
    cancelTimestamp: int
    side: int
    limitOrderType: int
    settlement: int


class ICLOBCancelArgs(TypedDict):
    """Arguments for canceling orders."""

    orderIds: list[int]
    settlement: int


class OrderStruct(TypedDict):
    """Order structure from contract."""

    side: int
    cancelTimestamp: int
    id: int
    prevOrderId: int
    nextOrderId: int
    owner: str
    price: int
    amount: int


class LimitStruct(TypedDict):
    """Limit structure from contract."""

    numOrders: int
    headOrder: int
    tailOrder: int


class MarketConfig(TypedDict):
    """Market configuration."""

    factory: str
    maxNumOrders: int
    quoteToken: str
    baseToken: str
    quoteSize: int
    baseSize: int


class MarketSettings(TypedDict):
    """Market settings."""

    status: bool
    maxLimitsPerTx: int
    minLimitOrderAmountInBase: int
    tickSize: int


# Launchpad structures
class LaunchDetails(TypedDict):
    """Details for launching a new token."""

    name: str
    symbol: str
    mediaURI: str
    initialBaseReserve: int
    initialQuoteReserve: int
    quoteToken: str
    virtualBaseReserve: int
    virtualQuoteReserve: int


# Event TypedDict definitions for ICLOB contract events
class LimitOrderSubmittedEvent(TypedDict):
    """Event emitted when a limit order is submitted."""
    
    owner: str  # indexed
    orderId: int
    args: ICLOBPostLimitOrderArgs
    nonce: int


class LimitOrderProcessedEvent(TypedDict):
    """Event emitted when a limit order is processed."""
    
    account: str  # indexed
    orderId: int
    amountPostedInBase: int
    quoteTokenAmountTraded: int
    baseTokenAmountTraded: int
    takerFee: int
    nonce: int


class FillOrderSubmittedEvent(TypedDict):
    """Event emitted when a fill order is submitted."""
    
    owner: str  # indexed
    orderId: int
    args: ICLOBPostFillOrderArgs
    nonce: int


class FillOrderProcessedEvent(TypedDict):
    """Event emitted when a fill order is processed."""
    
    account: str  # indexed
    orderId: int
    quoteTokenAmountTraded: int
    baseTokenAmountTraded: int
    takerFee: int
    nonce: int


class OrderMatchedEvent(TypedDict):
    """Event emitted when orders are matched."""
    
    takerOrderId: int
    makerOrderId: int
    takerOrder: OrderStruct
    makerOrder: OrderStruct
    tradedBase: int
    nonce: int


class OrderAmendedEvent(TypedDict):
    """Event emitted when an order is amended."""
    
    preAmend: OrderStruct
    args: ICLOBAmendArgs
    quoteTokenDelta: int
    baseTokenDelta: int
    eventNonce: int


class OrderCanceledEvent(TypedDict):
    """Event emitted when an order is canceled."""
    
    orderId: int
    owner: str
    quoteTokenRefunded: int
    baseTokenRefunded: int
    settlement: int
    nonce: int


class OrderReducedEvent(TypedDict):
    """Event emitted when an order is reduced in size."""
    
    orderId: int
    newAmountInBase: int
    refundAmountInBase: int
    settlement: int
    nonce: int


class CancelFailedEvent(TypedDict):
    """Event emitted when a cancel operation fails."""
    
    orderId: int
    owner: str
    nonce: int


class MaxLimitOrdersAllowlistedEvent(TypedDict):
    """Event emitted when an account's max limit orders allowlist status changes."""
    
    account: str  # indexed
    toggle: bool
    nonce: int


class MaxLimitOrdersPerTxUpdatedEvent(TypedDict):
    """Event emitted when the maximum limit orders per transaction is updated."""
    
    newMaxLimits: int
    nonce: int


class MinLimitOrderAmountInBaseUpdatedEvent(TypedDict):
    """Event emitted when the minimum limit order amount is updated."""
    
    newMinLimitOrderAmountInBase: int
    nonce: int


class TickSizeUpdatedEvent(TypedDict):
    """Event emitted when the tick size is updated."""
    
    newTickSize: int
    nonce: int
