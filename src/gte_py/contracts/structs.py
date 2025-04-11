from typing import Dict, Any, List, TypedDict, Optional, Union

class CancelArgs(TypedDict):
    """CLOB CancelArgs struct"""
    limitOrderHash: bytes
    refundGasTo: str

class PostLimitOrderArgs(TypedDict):
    """CLOB PostLimitOrderArgs struct"""
    orderType: int
    deadline: int
    tokenIn: str
    tokenOut: str
    amountIn: int
    limitPrice: int
    reservePrice: int
    maker: str
    salt: bytes
    hook: str
    additionalValidationData: bytes

class PostFillOrderArgs(TypedDict):
    """CLOB PostFillOrderArgs struct"""
    orderType: int  
    limitOrderHash: bytes
    takerSalt: bytes
    refundGasTo: str
    matcher: str
    additionalValidationData: bytes
    fillAmount: int
    fillPrice: int
    signature: bytes

class TokenPermissions(TypedDict):
    """Permit2 TokenPermissions struct"""
    token: str
    amount: int

class PermitDetails(TypedDict):
    """Permit2 PermitDetails struct"""
    token: str
    amount: int
    expiration: int
    nonce: int

class PermitSingle(TypedDict):
    """Permit2 PermitSingle struct"""
    details: PermitDetails
    spender: str
    sigDeadline: int

# ICLOB specific enums
class Side:
    """ICLOB Side enum"""
    BUY = 0
    SELL = 1

class Settlement:
    """ICLOB Settlement enum"""
    INSTANT = 0
    ACCOUNT = 1

class LimitOrderType:
    """ICLOB LimitOrderType enum"""
    GOOD_TILL_CANCELLED = 0
    POST_ONLY = 1

class FillOrderType:
    """ICLOB FillOrderType enum"""
    FILL_OR_KILL = 0
    IMMEDIATE_OR_CANCEL = 1

# ICLOB specific structs
class ICLOBCancelArgs(TypedDict):
    """ICLOB CancelArgs struct"""
    orderIds: List[int]
    settlement: int

class ICLOBPostLimitOrderArgs(TypedDict):
    """ICLOB PostLimitOrderArgs struct"""
    amountInBaseLots: int
    priceInTicks: int
    cancelTimestamp: int
    side: int
    limitOrderType: int
    settlement: int

class ICLOBPostLimitOrderResult(TypedDict):
    """ICLOB PostLimitOrderResult struct"""
    orderId: int
    amountPostedInBaseLots: int
    quoteTokenAmountTradedInAtoms: int
    baseTokenAmountTradedInAtoms: int

class ICLOBPostFillOrderArgs(TypedDict):
    """ICLOB PostFillOrderArgs struct"""
    amountInBaseLots: int
    priceInTicks: int
    side: int
    fillOrderType: int
    settlement: int

class ICLOBPostFillOrderResult(TypedDict):
    """ICLOB PostFillOrderResult struct"""
    orderId: int
    amountFilledInBaseLots: int
    quoteTokenAmountTradedInAtoms: int
    baseTokenAmountTradedInAtoms: int

class ICLOBReduceArgs(TypedDict):
    """ICLOB ReduceArgs struct"""
    orderId: int
    amountInBaseLots: int
    settlement: int

class LaunchDetails(TypedDict):
    """Launchpad details struct"""
    active: bool
    bondingCurve: str
    quote: str
    quoteScaling: int
    baseScaling: int
    baseSoldFromCurve: int
    quoteBoughtByCurve: int
