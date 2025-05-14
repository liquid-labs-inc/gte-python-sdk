"""Structure definitions for GTE contracts."""

from dataclasses import dataclass
from enum import IntEnum
from typing import TypedDict

from eth_typing import ChecksumAddress


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


class ICLOBConfigParams(TypedDict):
    """Configuration parameters for CLOB initialization."""
    
    factory: str
    maxNumOrders: int
    quoteToken: str
    baseToken: str
    quoteSize: int
    baseSize: int


class ICLOBSettingsParams(TypedDict):
    """Settings parameters for CLOB initialization."""
    
    status: bool
    maxLimitsPerTx: int
    minLimitOrderAmountInBase: int
    tickSize: int


"""
"components": [
  { "name": "side", "type": "uint8", "internalType": "enum Side" },
  {
    "name": "cancelTimestamp",
    "type": "uint32",
    "internalType": "uint32"
  },
  { "name": "id", "type": "uint256", "internalType": "OrderId" },
  {
    "name": "prevOrderId",
    "type": "uint256",
    "internalType": "OrderId"
  },
  {
    "name": "nextOrderId",
    "type": "uint256",
    "internalType": "OrderId"
  },
  { "name": "owner", "type": "address", "internalType": "address" },
  { "name": "price", "type": "uint256", "internalType": "uint256" },
  { "name": "amount", "type": "uint256", "internalType": "uint256" }
]
        """


@dataclass
class CLOBOrder:
    """Order structure from contract."""

    side: Side
    cancelTimestamp: int
    id: int
    prevOrderId: int
    nextOrderId: int
    owner: ChecksumAddress
    price: int
    amount: int

    @classmethod
    def from_tuple(
        cls,
        order_tuple: tuple[
            int,
            int,
            int,
            int,
            int,
            ChecksumAddress,
            int,
            int,
        ],
    ) -> "CLOBOrder":
        """Convert from tuple to Order."""
        return cls(
            side=Side(order_tuple[0]),
            cancelTimestamp=order_tuple[1],
            id=order_tuple[2],
            prevOrderId=order_tuple[3],
            nextOrderId=order_tuple[4],
            owner=ChecksumAddress(order_tuple[5]),
            price=order_tuple[6],
            amount=order_tuple[7],
        )

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
