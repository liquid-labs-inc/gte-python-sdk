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


# Contract input structs with proper TypedDict definitions
class ICLOBPostLimitOrderArgs(TypedDict):
    """Arguments for posting a limit order."""

    amountInBaseLots: int
    priceInTicks: int
    cancelTimestamp: int
    side: int
    limitOrderType: int
    settlement: int


class ICLOBPostLimitOrderResult(TypedDict):
    """Result from posting a limit order."""

    orderId: int
    makerAmountInQuote: int
    takerAmountInQuote: int


class ICLOBPostFillOrderArgs(TypedDict):
    """Arguments for posting a fill order."""

    amountInBaseLots: int
    priceInTicks: int
    side: int
    fillOrderType: int
    settlement: int


class ICLOBPostFillOrderResult(TypedDict):
    """Result from posting a fill order."""

    makerAmountInQuote: int
    takerAmountInQuote: int


class ICLOBReduceArgs(TypedDict):
    """Arguments for reducing an order."""

    orderId: int
    amountInBaseLots: int
    settlement: int


class ICLOBCancelArgs(TypedDict):
    """Arguments for canceling orders."""

    orderIds: list[int]
    settlement: int
