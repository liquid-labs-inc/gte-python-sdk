"""Structure definitions for GTE contracts."""

from enum import IntEnum
from typing import TypedDict, List, Dict, Any


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
    orderIds: List[int]


class CancelArgs(TypedDict):
    """Arguments for canceling orders through router."""
    
    isBuy: int
    orderId: int


# CLOB specific structures
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

    orderIds: List[int]
    settlement: int


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
