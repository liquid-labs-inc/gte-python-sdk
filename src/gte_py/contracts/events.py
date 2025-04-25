"""Event type classes for CLOB contract events."""

from dataclasses import dataclass
from typing import Optional, Any, Dict

from eth_typing import ChecksumAddress, HexStr

from .structs import (
    ICLOBPostLimitOrderArgs,
    ICLOBPostFillOrderArgs,
    ICLOBAmendArgs,
    OrderStruct
)


@dataclass
class CLOBEvent:
    """Base class for CLOB events."""
    tx_hash: HexStr
    log_index: int
    block_number: int
    address: ChecksumAddress
    event_name: str
    raw_data: Dict[str, Any]


@dataclass
class LimitOrderSubmittedEvent(CLOBEvent):
    """Event emitted when a limit order is submitted."""
    owner: ChecksumAddress
    order_id: int
    args: ICLOBPostLimitOrderArgs
    nonce: int


@dataclass
class LimitOrderProcessedEvent(CLOBEvent):
    """Event emitted when a limit order is processed."""
    account: ChecksumAddress
    order_id: int
    amount_posted_in_base: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int
    nonce: int


@dataclass
class FillOrderSubmittedEvent(CLOBEvent):
    """Event emitted when a fill order is submitted."""
    owner: ChecksumAddress
    order_id: int
    args: ICLOBPostFillOrderArgs
    nonce: int


@dataclass
class FillOrderProcessedEvent(CLOBEvent):
    """Event emitted when a fill order is processed."""
    account: ChecksumAddress
    order_id: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int
    nonce: int


@dataclass
class OrderMatchedEvent(CLOBEvent):
    """Event emitted when orders are matched."""
    taker_order_id: int
    maker_order_id: int
    taker_order: OrderStruct
    maker_order: OrderStruct
    traded_base: int
    nonce: int


@dataclass
class OrderAmendedEvent(CLOBEvent):
    """Event emitted when an order is amended."""
    pre_amend: OrderStruct
    args: ICLOBAmendArgs
    quote_token_delta: int
    base_token_delta: int
    event_nonce: int


@dataclass
class OrderCanceledEvent(CLOBEvent):
    """Event emitted when an order is canceled."""
    order_id: int
    owner: ChecksumAddress
    quote_token_refunded: int
    base_token_refunded: int
    settlement: int
    nonce: int


@dataclass
class OrderReducedEvent(CLOBEvent):
    """Event emitted when an order is reduced in size."""
    order_id: int
    new_amount_in_base: int
    refund_amount_in_base: int
    settlement: int
    nonce: int


@dataclass
class CancelFailedEvent(CLOBEvent):
    """Event emitted when a cancel operation fails."""
    order_id: int
    owner: ChecksumAddress
    nonce: int


@dataclass
class MaxLimitOrdersAllowlistedEvent(CLOBEvent):
    """Event emitted when an account's max limit orders allowlist status changes."""
    account: ChecksumAddress
    toggle: bool
    nonce: int


@dataclass
class MaxLimitOrdersPerTxUpdatedEvent(CLOBEvent):
    """Event emitted when the maximum limit orders per transaction is updated."""
    new_max_limits: int
    nonce: int


@dataclass
class MinLimitOrderAmountInBaseUpdatedEvent(CLOBEvent):
    """Event emitted when the minimum limit order amount is updated."""
    new_min_limit_order_amount_in_base: int
    nonce: int


@dataclass
class TickSizeUpdatedEvent(CLOBEvent):
    """Event emitted when the tick size is updated."""
    new_tick_size: int
    nonce: int


def convert_event_data_to_typed_event(event_data: Dict[str, Any]) -> CLOBEvent:
    """
    Convert raw event data to typed event.
    
    Args:
        event_data: Raw event data from web3
        
    Returns:
        Typed event class instance
    """
    event_name = event_data.get('event')
    base_info = {
        'tx_hash': event_data.get('transactionHash'),
        'log_index': event_data.get('logIndex'),
        'block_number': event_data.get('blockNumber'),
        'address': event_data.get('address'),
        'event_name': event_name,
        'raw_data': event_data
    }
    
    args = event_data.get('args', {})
    
    if event_name == 'LimitOrderSubmitted':
        return LimitOrderSubmittedEvent(
            **base_info,
            owner=args.get('owner'),
            order_id=args.get('orderId'),
            args=args.get('args'),
            nonce=args.get('nonce')
        )
    elif event_name == 'LimitOrderProcessed':
        return LimitOrderProcessedEvent(
            **base_info,
            account=args.get('account'),
            order_id=args.get('orderId'),
            amount_posted_in_base=args.get('amountPostedInBase'),
            quote_token_amount_traded=args.get('quoteTokenAmountTraded'),
            base_token_amount_traded=args.get('baseTokenAmountTraded'),
            taker_fee=args.get('takerFee'),
            nonce=args.get('nonce')
        )
    elif event_name == 'FillOrderSubmitted':
        return FillOrderSubmittedEvent(
            **base_info,
            owner=args.get('owner'),
            order_id=args.get('orderId'),
            args=args.get('args'),
            nonce=args.get('nonce')
        )
    elif event_name == 'FillOrderProcessed':
        return FillOrderProcessedEvent(
            **base_info,
            account=args.get('account'),
            order_id=args.get('orderId'),
            quote_token_amount_traded=args.get('quoteTokenAmountTraded'),
            base_token_amount_traded=args.get('baseTokenAmountTraded'),
            taker_fee=args.get('takerFee'),
            nonce=args.get('nonce')
        )
    elif event_name == 'OrderMatched':
        return OrderMatchedEvent(
            **base_info,
            taker_order_id=args.get('takerOrderId'),
            maker_order_id=args.get('makerOrderId'),
            taker_order=args.get('takerOrder'),
            maker_order=args.get('makerOrder'),
            traded_base=args.get('tradedBase'),
            nonce=args.get('nonce')
        )
    elif event_name == 'OrderAmended':
        return OrderAmendedEvent(
            **base_info,
            pre_amend=args.get('preAmend'),
            args=args.get('args'),
            quote_token_delta=args.get('quoteTokenDelta'),
            base_token_delta=args.get('baseTokenDelta'),
            event_nonce=args.get('eventNonce')
        )
    elif event_name == 'OrderCanceled':
        return OrderCanceledEvent(
            **base_info,
            order_id=args.get('orderId'),
            owner=args.get('owner'),
            quote_token_refunded=args.get('quoteTokenRefunded'),
            base_token_refunded=args.get('baseTokenRefunded'),
            settlement=args.get('settlement'),
            nonce=args.get('nonce')
        )
    elif event_name == 'OrderReduced':
        return OrderReducedEvent(
            **base_info,
            order_id=args.get('orderId'),
            new_amount_in_base=args.get('newAmountInBase'),
            refund_amount_in_base=args.get('refundAmountInBase'),
            settlement=args.get('settlement'),
            nonce=args.get('nonce')
        )
    elif event_name == 'CancelFailed':
        return CancelFailedEvent(
            **base_info,
            order_id=args.get('orderId'),
            owner=args.get('owner'),
            nonce=args.get('nonce')
        )
    elif event_name == 'MaxLimitOrdersAllowlisted':
        return MaxLimitOrdersAllowlistedEvent(
            **base_info,
            account=args.get('account'),
            toggle=args.get('toggle'),
            nonce=args.get('nonce')
        )
    elif event_name == 'MaxLimitOrdersPerTxUpdated':
        return MaxLimitOrdersPerTxUpdatedEvent(
            **base_info,
            new_max_limits=args.get('newMaxLimits'),
            nonce=args.get('nonce')
        )
    elif event_name == 'MinLimitOrderAmountInBaseUpdated':
        return MinLimitOrderAmountInBaseUpdatedEvent(
            **base_info,
            new_min_limit_order_amount_in_base=args.get('newMinLimitOrderAmountInBase'),
            nonce=args.get('nonce')
        )
    elif event_name == 'TickSizeUpdated':
        return TickSizeUpdatedEvent(
            **base_info,
            new_tick_size=args.get('newTickSize'),
            nonce=args.get('nonce')
        )
    else:
        # Return base event for unknown event types
        return CLOBEvent(**base_info)