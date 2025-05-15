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
    nonce: int


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
    nonce: int  # Added missing nonce field


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


@dataclass
class TickSizeUpdatedEvent(CLOBEvent):
    """Event emitted when the tick size is updated."""

    new_tick_size: int


@dataclass
class MinLimitOrderAmountInBaseUpdatedEvent(CLOBEvent):
    """Event emitted when the minimum limit order amount in base is updated."""

    new_min_limit_order_amount_in_base: int


@dataclass
class MaxLimitOrdersPerTxUpdatedEvent(CLOBEvent):
    """Event emitted when the maximum limit orders per transaction is updated."""

    new_max_limits: int


@dataclass
class MaxLimitOrdersAllowlistedEvent(CLOBEvent):
    """Event emitted when an account is added/removed from max limit orders exemption."""

    account: ChecksumAddress
    toggle: bool


# CLOB Manager Events
@dataclass
class CLOBManagerEvent:
    """Base class for CLOB Manager events."""

    tx_hash: HexBytes
    log_index: int
    block_number: int
    address: ChecksumAddress
    event_name: str
    raw_data: Dict[str, Any]
    nonce: int


@dataclass
class AccountCreditedEvent(CLOBManagerEvent):
    """Event emitted when an account is credited."""

    account: ChecksumAddress
    token: ChecksumAddress
    amount: int


@dataclass
class AccountDebitedEvent(CLOBManagerEvent):
    """Event emitted when an account is debited."""

    account: ChecksumAddress
    token: ChecksumAddress
    amount: int


@dataclass
class AccountFeeTierUpdatedEvent(CLOBManagerEvent):
    """Event emitted when an account fee tier is updated."""

    account: ChecksumAddress
    fee_tier: int


@dataclass
class DepositEvent(CLOBManagerEvent):
    """Event emitted when a deposit is made."""

    account: ChecksumAddress
    funder: ChecksumAddress
    token: ChecksumAddress
    amount: int


@dataclass
class FeeCollectedEvent(CLOBManagerEvent):
    """Event emitted when fees are collected."""

    token: ChecksumAddress
    fee: int


@dataclass
class FeeRecipientSetEvent(CLOBManagerEvent):
    """Event emitted when the fee recipient is set."""

    fee_recipient: ChecksumAddress


# @dataclass
# class MarketCreatedEvent(CLOBManagerEvent):
#     """Event emitted when a market is created."""
#
#     creator: ChecksumAddress
#     base_token: ChecksumAddress
#     quote_token: ChecksumAddress
#     market: ChecksumAddress
#     quote_decimals: int
#     base_decimals: int
#     config: ICLOBConfigParams
#     settings: ICLOBSettingsParams


@dataclass
class OperatorApprovedEvent(CLOBManagerEvent):
    """Event emitted when an operator is approved."""

    account: ChecksumAddress
    operator: ChecksumAddress


@dataclass
class OperatorDisapprovedEvent(CLOBManagerEvent):
    """Event emitted when an operator is disapproved."""

    account: ChecksumAddress
    operator: ChecksumAddress


@dataclass
class WithdrawEvent(CLOBManagerEvent):
    """Event emitted when a withdrawal is made."""

    account: ChecksumAddress
    recipient: ChecksumAddress
    token: ChecksumAddress
    amount: int


def _create_base_event_info(event_data: EventData) -> Dict[str, Any]:
    """
    Create base event info dictionary from raw event data.

    Args:
        event_data: Raw event data from web3

    Returns:
        Base event info dictionary
    """

    return {
        "tx_hash": event_data.get("transactionHash"),
        "log_index": event_data.get("logIndex"),
        "block_number": event_data.get("blockNumber"),
        "address": event_data.get("address"),
        "event_name": event_data.get("event"),
        "raw_data": event_data,
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
        nonce=args.get("nonce"),
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
        nonce=args.get("nonce"),  # Added nonce field extraction
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
        nonce=args.get('nonce')
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
        nonce=args.get('nonce')
    )


def parse_tick_size_updated(event_data: EventData) -> TickSizeUpdatedEvent:
    """
    Parse TickSizeUpdated event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed TickSizeUpdatedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return TickSizeUpdatedEvent(
        **base_info,
        new_tick_size=args.get("newTickSize"),
    )


def parse_min_limit_order_amount_in_base_updated(event_data: EventData) -> MinLimitOrderAmountInBaseUpdatedEvent:
    """
    Parse MinLimitOrderAmountInBaseUpdated event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed MinLimitOrderAmountInBaseUpdatedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return MinLimitOrderAmountInBaseUpdatedEvent(
        **base_info,
        new_min_limit_order_amount_in_base=args.get("newMinLimitOrderAmountInBase"),
    )


def parse_max_limit_orders_per_tx_updated(event_data: EventData) -> MaxLimitOrdersPerTxUpdatedEvent:
    """
    Parse MaxLimitOrdersPerTxUpdated event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed MaxLimitOrdersPerTxUpdatedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return MaxLimitOrdersPerTxUpdatedEvent(
        **base_info,
        new_max_limits=args.get("newMaxLimits"),
    )


def parse_max_limit_orders_allowlisted(event_data: EventData) -> MaxLimitOrdersAllowlistedEvent:
    """
    Parse MaxLimitOrdersAllowlisted event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed MaxLimitOrdersAllowlistedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return MaxLimitOrdersAllowlistedEvent(
        **base_info,
        account=args.get("account"),
        toggle=args.get("toggle"),
    )


# CLOB Manager event parsers
def parse_account_credited(event_data: EventData) -> AccountCreditedEvent:
    """
    Parse AccountCredited event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed AccountCreditedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return AccountCreditedEvent(
        **base_info,
        account=args.get("account"),
        token=args.get("token"),
        amount=args.get("amount"),
    )


def parse_account_debited(event_data: EventData) -> AccountDebitedEvent:
    """
    Parse AccountDebited event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed AccountDebitedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return AccountDebitedEvent(
        **base_info,
        account=args.get("account"),
        token=args.get("token"),
        amount=args.get("amount"),
    )


def parse_account_fee_tier_updated(event_data: EventData) -> AccountFeeTierUpdatedEvent:
    """
    Parse AccountFeeTierUpdated event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed AccountFeeTierUpdatedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return AccountFeeTierUpdatedEvent(
        **base_info,
        account=args.get("account"),
        fee_tier=args.get("feeTier"),
    )


def parse_deposit(event_data: EventData) -> DepositEvent:
    """
    Parse Deposit event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed DepositEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return DepositEvent(
        **base_info,
        account=args.get("account"),
        funder=args.get("funder"),
        token=args.get("token"),
        amount=args.get("amount"),
    )


def parse_fee_collected(event_data: EventData) -> FeeCollectedEvent:
    """
    Parse FeeCollected event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed FeeCollectedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return FeeCollectedEvent(
        **base_info,
        token=args.get("token"),
        fee=args.get("fee"),
    )


def parse_fee_recipient_set(event_data: EventData) -> FeeRecipientSetEvent:
    """
    Parse FeeRecipientSet event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed FeeRecipientSetEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return FeeRecipientSetEvent(
        **base_info,
        fee_recipient=args.get("feeRecipient"),
    )


# def parse_market_created(event_data: EventData) -> MarketCreatedEvent:
#     """
#     Parse MarketCreated event.
#
#     Args:
#         event_data: Raw event data from web3
#
#     Returns:
#         Typed MarketCreatedEvent
#     """
#     args = event_data.get("args", {})
#     base_info = _create_base_event_info(event_data)
#
#     return MarketCreatedEvent(
#         **base_info,
#         creator=args.get("creator"),
#         base_token=args.get("baseToken"),
#         quote_token=args.get("quoteToken"),
#         market=args.get("market"),
#         quote_decimals=args.get("quoteDecimals"),
#         base_decimals=args.get("baseDecimals"),
#         config=args.get("config"),
#         settings=args.get("settings"),
#     )


def parse_operator_approved(event_data: EventData) -> OperatorApprovedEvent:
    """
    Parse OperatorApproved event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OperatorApprovedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return OperatorApprovedEvent(
        **base_info,
        account=args.get("account"),
        operator=args.get("operator"),
    )


def parse_operator_disapproved(event_data: EventData) -> OperatorDisapprovedEvent:
    """
    Parse OperatorDisapproved event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OperatorDisapprovedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return OperatorDisapprovedEvent(
        **base_info,
        account=args.get("account"),
        operator=args.get("operator"),
    )


def parse_withdraw(event_data: EventData) -> WithdrawEvent:
    """
    Parse Withdraw event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed WithdrawEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    return WithdrawEvent(
        **base_info,
        account=args.get("account"),
        recipient=args.get("recipient"),
        token=args.get("token"),
        amount=args.get("amount"),
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
    "TickSizeUpdated": parse_tick_size_updated,
    "MinLimitOrderAmountInBaseUpdated": parse_min_limit_order_amount_in_base_updated,
    "MaxLimitOrdersPerTxUpdated": parse_max_limit_orders_per_tx_updated,
    "MaxLimitOrdersAllowlisted": parse_max_limit_orders_allowlisted,
}

# Add CLOB Manager event parsers to the global dictionary
CLOB_MANAGER_EVENT_PARSERS = {
    "AccountCredited": parse_account_credited,
    "AccountDebited": parse_account_debited,
    "AccountFeeTierUpdated": parse_account_fee_tier_updated,
    "Deposit": parse_deposit,
    "FeeCollected": parse_fee_collected,
    "FeeRecipientSet": parse_fee_recipient_set,
    # "MarketCreated": parse_market_created,
    "OperatorApproved": parse_operator_approved,
    "OperatorDisapproved": parse_operator_disapproved,
    "Withdraw": parse_withdraw,
}

# Update the existing EVENT_PARSERS dictionary
EVENT_PARSERS.update(CLOB_MANAGER_EVENT_PARSERS)


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
