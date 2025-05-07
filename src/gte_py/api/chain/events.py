"""Event type classes for CLOB contract events."""

from dataclasses import dataclass
from typing import Any, Dict

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3.types import EventData

from .structs import OrderStruct, ICLOBPostLimitOrderArgs, ICLOBPostFillOrderArgs, ICLOBAmendArgs


@dataclass
class CLOBEvent:
    """Base class for CLOB events."""

    tx_hash: HexBytes
    log_index: int
    block_number: int
    address: ChecksumAddress
    event_name: str
    raw_data: Dict[str, Any]
    nonce: int


@dataclass
class LimitOrderSubmittedEvent(CLOBEvent):
    """Event emitted when a limit order is submitted."""

    owner: ChecksumAddress
    order_id: int
    args: ICLOBPostLimitOrderArgs


@dataclass
class LimitOrderProcessedEvent(CLOBEvent):
    """Event emitted when a limit order is processed."""

    account: ChecksumAddress
    order_id: int
    amount_posted_in_base: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int


@dataclass
class FillOrderSubmittedEvent(CLOBEvent):
    """Event emitted when a fill order is submitted."""

    owner: ChecksumAddress
    order_id: int
    args: ICLOBPostFillOrderArgs


@dataclass
class FillOrderProcessedEvent(CLOBEvent):
    """Event emitted when a fill order is processed."""

    account: ChecksumAddress
    order_id: int
    quote_token_amount_traded: int
    base_token_amount_traded: int
    taker_fee: int


@dataclass
class OrderMatchedEvent(CLOBEvent):
    """Event emitted when orders are matched."""

    taker_order_id: int
    maker_order_id: int
    taker_order: OrderStruct
    maker_order: OrderStruct
    traded_base: int


@dataclass
class OrderAmendedEvent(CLOBEvent):
    """Event emitted when an order is amended."""

    pre_amend: OrderStruct
    args: ICLOBAmendArgs
    quote_token_delta: int
    base_token_delta: int


@dataclass
class OrderCanceledEvent(CLOBEvent):
    """Event emitted when an order is canceled."""

    order_id: int
    owner: ChecksumAddress
    quote_token_refunded: int
    base_token_refunded: int
    settlement: int


def _create_base_event_info(event_data: EventData) -> Dict[str, Any]:
    """
    Create base event info dictionary from raw event data.

    Args:
        event_data: Raw event data from web3

    Returns:
        Base event info dictionary
    """
    args = event_data.get("args", {})
    nonce = args.get("nonce", args.get("eventNonce", 0))

    return {
        "tx_hash": event_data.get("transactionHash"),
        "log_index": event_data.get("logIndex"),
        "block_number": event_data.get("blockNumber"),
        "address": event_data.get("address"),
        "event_name": event_data.get("event"),
        "raw_data": event_data,
        "nonce": nonce,
    }


def parse_limit_order_submitted(event_data: EventData) -> LimitOrderSubmittedEvent:
    """
    Parse LimitOrderSubmitted event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed LimitOrderSubmittedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return LimitOrderSubmittedEvent(
        **base_info, owner=args.get("owner"), order_id=args.get("orderId"), args=args.get("args")
    )


def parse_limit_order_processed(event_data: EventData) -> LimitOrderProcessedEvent:
    """
    Parse LimitOrderProcessed event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed LimitOrderProcessedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return LimitOrderProcessedEvent(
        **base_info,
        account=args.get("account"),
        order_id=args.get("orderId"),
        amount_posted_in_base=args.get("amountPostedInBase"),
        quote_token_amount_traded=args.get("quoteTokenAmountTraded"),
        base_token_amount_traded=args.get("baseTokenAmountTraded"),
        taker_fee=args.get("takerFee"),
    )


def parse_fill_order_submitted(event_data: EventData) -> FillOrderSubmittedEvent:
    """
    Parse FillOrderSubmitted event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed FillOrderSubmittedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return FillOrderSubmittedEvent(
        **base_info, owner=args.get("owner"), order_id=args.get("orderId"), args=args.get("args")
    )


def parse_fill_order_processed(event_data: EventData) -> FillOrderProcessedEvent:
    """
    Parse FillOrderProcessed event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed FillOrderProcessedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return FillOrderProcessedEvent(
        **base_info,
        account=args.get("account"),
        order_id=args.get("orderId"),
        quote_token_amount_traded=args.get("quoteTokenAmountTraded"),
        base_token_amount_traded=args.get("baseTokenAmountTraded"),
        taker_fee=args.get("takerFee"),
    )


def parse_order_matched(event_data: EventData) -> OrderMatchedEvent:
    """
    Parse OrderMatched event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OrderMatchedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return OrderMatchedEvent(
        **base_info,
        taker_order_id=args.get("takerOrderId"),
        maker_order_id=args.get("makerOrderId"),
        taker_order=args.get("takerOrder"),
        maker_order=args.get("makerOrder"),
        traded_base=args.get("tradedBase"),
    )


def parse_order_amended(event_data: EventData) -> OrderAmendedEvent:
    """
    Parse OrderAmended event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OrderAmendedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return OrderAmendedEvent(
        **base_info,
        pre_amend=args.get("preAmend"),
        args=args.get("args"),
        quote_token_delta=args.get("quoteTokenDelta"),
        base_token_delta=args.get("baseTokenDelta"),
    )


def parse_order_canceled(event_data: EventData) -> OrderCanceledEvent:
    """
    Parse OrderCanceled event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OrderCanceledEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return OrderCanceledEvent(
        **base_info,
        order_id=args.get("orderId"),
        owner=args.get("owner"),
        quote_token_refunded=args.get("quoteTokenRefunded"),
        base_token_refunded=args.get("baseTokenRefunded"),
        settlement=args.get("settlement"),
    )


# Dictionary mapping event names to their parser functions
EVENT_PARSERS = {
    "LimitOrderSubmitted": parse_limit_order_submitted,
    "LimitOrderProcessed": parse_limit_order_processed,
    "FillOrderSubmitted": parse_fill_order_submitted,
    "FillOrderProcessed": parse_fill_order_processed,
    "OrderMatched": parse_order_matched,
    "OrderAmended": parse_order_amended,
    "OrderCanceled": parse_order_canceled,
}


def convert_event_data_to_typed_event(event_data: EventData) -> CLOBEvent:
    """
    Convert raw event data to typed event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed event class instance
    """
    event_name = event_data.get("event")

    # Look up the appropriate parser function
    parser_func = EVENT_PARSERS.get(event_name)

    if parser_func:
        return parser_func(event_data)

    # Return base event for unknown event types
    args = event_data.get("args", {})
    nonce = args.get("nonce", args.get("eventNonce", 0))

    return CLOBEvent(
        tx_hash=event_data.get("transactionHash"),
        log_index=event_data.get("logIndex"),
        block_number=event_data.get("blockNumber"),
        address=event_data.get("address"),
        event_name=event_name,
        raw_data=event_data,
        nonce=nonce,
    )
