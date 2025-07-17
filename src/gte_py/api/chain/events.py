"""Event type classes for CLOB contract events."""

from dataclasses import dataclass
from typing import Any, Dict, cast

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
    raw_data: dict[str, Any]
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


@dataclass
class CancelFailedEvent(CLOBEvent):
    """Event emitted when a cancel operation fails."""

    order_id: int
    owner: ChecksumAddress


@dataclass
class InitializedEvent(CLOBEvent):
    """Event emitted when a contract is initialized."""

    version: int


@dataclass
class OwnershipTransferStartedEvent(CLOBEvent):
    """Event emitted when ownership transfer is started."""

    previous_owner: ChecksumAddress
    new_owner: ChecksumAddress


@dataclass
class ClobOwnershipTransferredEvent(CLOBEvent):
    """Event emitted when ownership is transferred."""

    previous_owner: ChecksumAddress
    new_owner: ChecksumAddress


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


@dataclass
class MarketCreatedEvent(CLOBManagerEvent):
    """Event emitted when a market is created."""

    creator: ChecksumAddress
    base_token: ChecksumAddress
    quote_token: ChecksumAddress
    market: ChecksumAddress
    quote_decimals: int
    base_decimals: int
    config: dict[str, Any]
    settings: dict[str, Any]


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


@dataclass
class OwnershipHandoverCanceledEvent(CLOBManagerEvent):
    """Event emitted when an ownership handover is canceled."""
    
    pending_owner: ChecksumAddress


@dataclass
class OwnershipHandoverRequestedEvent(CLOBManagerEvent):
    """Event emitted when an ownership handover is requested."""
    
    pending_owner: ChecksumAddress


@dataclass
class ClobManagerOwnershipTransferredEvent(CLOBManagerEvent):
    """Event emitted when ownership is transferred."""
    
    old_owner: ChecksumAddress
    new_owner: ChecksumAddress


@dataclass
class RolesApprovedEvent(CLOBManagerEvent):
    """Event emitted when roles are approved for an operator."""

    account: ChecksumAddress
    operator: ChecksumAddress
    roles: int


@dataclass
class RolesDisapprovedEvent(CLOBManagerEvent):
    """Event emitted when roles are disapproved for an operator."""

    account: ChecksumAddress
    operator: ChecksumAddress
    roles: int


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

    owner = cast(ChecksumAddress, args.get("owner"))
    order_id = cast(int, args.get("orderId"))
    order_args = cast(ICLOBPostLimitOrderArgs, args.get("args"))

    return LimitOrderSubmittedEvent(
        **base_info,
        owner=owner,
        order_id=order_id,
        args=order_args,
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

    account = cast(ChecksumAddress, args.get("account"))
    order_id = cast(int, args.get("orderId"))
    amount_posted_in_base = cast(int, args.get("amountPostedInBase"))
    quote_token_amount_traded = cast(int, args.get("quoteTokenAmountTraded"))
    base_token_amount_traded = cast(int, args.get("baseTokenAmountTraded"))
    taker_fee = cast(int, args.get("takerFee"))
    nonce = cast(int, args.get("nonce"))

    return LimitOrderProcessedEvent(
        **base_info,
        account=account,
        order_id=order_id,
        amount_posted_in_base=amount_posted_in_base,
        quote_token_amount_traded=quote_token_amount_traded,
        base_token_amount_traded=base_token_amount_traded,
        taker_fee=taker_fee,
        nonce=nonce,
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
    
    owner = cast(ChecksumAddress, args.get("owner"))
    order_id = cast(int, args.get("orderId"))
    order_args = cast(ICLOBPostFillOrderArgs, args.get("args"))

    return FillOrderSubmittedEvent(
        **base_info,
        owner=owner,
        order_id=order_id,
        args=order_args,
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

    account = cast(ChecksumAddress, args.get("account"))
    order_id = cast(int, args.get("orderId"))
    quote_token_amount_traded = cast(int, args.get("quoteTokenAmountTraded"))
    base_token_amount_traded = cast(int, args.get("baseTokenAmountTraded"))
    taker_fee = cast(int, args.get("takerFee"))
    nonce = cast(int, args.get("nonce"))

    return FillOrderProcessedEvent(
        **base_info,
        account=account,
        order_id=order_id,
        quote_token_amount_traded=quote_token_amount_traded,
        base_token_amount_traded=base_token_amount_traded,
        taker_fee=taker_fee,
        nonce=nonce,
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

    taker_order_id = cast(int, args.get("takerOrderId"))
    maker_order_id = cast(int, args.get("makerOrderId"))
    taker_order = cast(OrderStruct, args.get("takerOrder"))
    maker_order = cast(OrderStruct, args.get("makerOrder"))
    traded_base = cast(int, args.get("tradedBase"))
    nonce = cast(int, args.get("nonce"))

    return OrderMatchedEvent(
        **base_info,
        taker_order_id=taker_order_id,
        maker_order_id=maker_order_id,
        taker_order=taker_order,
        maker_order=maker_order,
        traded_base=traded_base,
        nonce=nonce,
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

    pre_amend = cast(OrderStruct, args.get("preAmend"))
    amend_args = cast(ICLOBAmendArgs, args.get("args"))
    quote_token_delta = cast(int, args.get("quoteTokenDelta"))
    base_token_delta = cast(int, args.get("baseTokenDelta"))
    nonce = cast(int, args.get("eventNonce", 0))

    return OrderAmendedEvent(
        **base_info,
        pre_amend=pre_amend,
        args=amend_args,
        quote_token_delta=quote_token_delta,
        base_token_delta=base_token_delta,
        nonce=nonce,
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

    order_id = cast(int, args.get("orderId"))
    owner = cast(ChecksumAddress, args.get("owner"))
    quote_token_refunded = cast(int, args.get("quoteTokenRefunded"))
    base_token_refunded = cast(int, args.get("baseTokenRefunded"))
    settlement = cast(int, args.get("settlement"))

    return OrderCanceledEvent(
        **base_info,
        order_id=order_id,
        owner=owner,
        quote_token_refunded=quote_token_refunded,
        base_token_refunded=base_token_refunded,            
        settlement=settlement,
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

    new_tick_size = cast(int, args.get("newTickSize"))

    return TickSizeUpdatedEvent(
        **base_info,
        new_tick_size=new_tick_size,
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

    new_min = cast(int, args.get("newMinLimitOrderAmountInBase"))

    return MinLimitOrderAmountInBaseUpdatedEvent(
        **base_info,
        new_min_limit_order_amount_in_base=new_min,
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

    new_max_limits = cast(int, args.get("newMaxLimits"))

    return MaxLimitOrdersPerTxUpdatedEvent(
        **base_info,
        new_max_limits=new_max_limits,
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

    account = cast(ChecksumAddress, args.get("account"))
    toggle = cast(bool, args.get("toggle"))

    return MaxLimitOrdersAllowlistedEvent(
        **base_info,
        account=account,
        toggle=toggle,
    )


def parse_cancel_failed(event_data: EventData) -> CancelFailedEvent:
    """
    Parse CancelFailed event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed CancelFailedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    order_id = cast(int, args.get("orderId"))
    owner = cast(ChecksumAddress, args.get("owner"))

    return CancelFailedEvent(
        **base_info,
        order_id=order_id,
        owner=owner,
    )


def parse_initialized(event_data: EventData) -> InitializedEvent:
    """
    Parse Initialized event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed InitializedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    version = cast(int, args.get("version"))

    return InitializedEvent(
        **base_info,
        version=version,
        nonce=0,
    )


def parse_ownership_transfer_started(event_data: EventData) -> OwnershipTransferStartedEvent:
    """
    Parse OwnershipTransferStarted event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OwnershipTransferStartedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    previous_owner = cast(ChecksumAddress, args.get("previousOwner"))
    new_owner = cast(ChecksumAddress, args.get("newOwner"))

    return OwnershipTransferStartedEvent(
        **base_info,
        previous_owner=previous_owner,
        new_owner=new_owner,
        nonce=0,
    )


def parse_ownership_handover_canceled(event_data: EventData) -> OwnershipHandoverCanceledEvent:
    """
    Parse OwnershipHandoverCanceled event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OwnershipHandoverCanceledEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)
    
    pending_owner = cast(ChecksumAddress, args.get("pendingOwner"))

    return OwnershipHandoverCanceledEvent(
        **base_info,
        pending_owner=pending_owner,
        nonce=0,
    )



def parse_ownership_handover_requested(event_data: EventData) -> OwnershipHandoverRequestedEvent:
    """
    Parse OwnershipHandoverRequested event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed OwnershipHandoverRequestedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)
    
    pending_owner = cast(ChecksumAddress, args.get("pendingOwner"))

    # This event doesn't have a nonce in the standard Ownable contract
    return OwnershipHandoverRequestedEvent(
        **base_info,
        pending_owner=pending_owner,
        nonce=0,
    )


def parse_ownership_transferred(event_data: EventData) -> ClobManagerOwnershipTransferredEvent:
    """
    Parse OwnershipTransferred event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed ClobManagerOwnershipTransferredEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)
    
    old_owner = cast(ChecksumAddress, args.get("oldOwner"))
    new_owner = cast(ChecksumAddress, args.get("newOwner"))

    return ClobManagerOwnershipTransferredEvent(
        **base_info,
        old_owner=old_owner,
        new_owner=new_owner,
        nonce=0,
    )


def parse_clob_ownership_transferred(event_data: EventData) -> ClobOwnershipTransferredEvent:
    """
    Parse CLOB OwnershipTransferred event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed ClobOwnershipTransferredEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)
    
    previous_owner = cast(ChecksumAddress, args.get("previousOwner"))
    new_owner = cast(ChecksumAddress, args.get("newOwner"))

    return ClobOwnershipTransferredEvent(
        **base_info,
        previous_owner=previous_owner,
        new_owner=new_owner,
        nonce=0,
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

    account = cast(ChecksumAddress, args.get("account"))
    token = cast(ChecksumAddress, args.get("token"))
    amount = cast(int, args.get("amount"))

    return AccountCreditedEvent(
        **base_info,
        account=account,
        token=token,
        amount=amount,
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

    account = cast(ChecksumAddress, args.get("account"))
    token = cast(ChecksumAddress, args.get("token"))
    amount = cast(int, args.get("amount"))

    return AccountDebitedEvent(
        **base_info,
        account=account,
        token=token,
        amount=amount,
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

    account = cast(ChecksumAddress, args.get("account"))
    fee_tier = cast(int, args.get("feeTier"))

    return AccountFeeTierUpdatedEvent(
        **base_info,
        account=account,
        fee_tier=fee_tier,
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

    account = cast(ChecksumAddress, args.get("account"))
    funder = cast(ChecksumAddress, args.get("funder"))
    token = cast(ChecksumAddress, args.get("token"))
    amount = cast(int, args.get("amount"))

    return DepositEvent(
        **base_info,
        account=account,
        funder=funder,
        token=token,
        amount=amount,
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

    token = cast(ChecksumAddress, args.get("token"))
    fee = cast(int, args.get("fee"))

    return FeeCollectedEvent(
        **base_info,
        token=token,
        fee=fee,
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

    fee_recipient = cast(ChecksumAddress, args.get("feeRecipient"))

    return FeeRecipientSetEvent(
        **base_info,
        fee_recipient=fee_recipient,
    )



def parse_market_created(event_data: EventData) -> MarketCreatedEvent:
    """
    Parse MarketCreated event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed MarketCreatedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    creator = cast(ChecksumAddress, args.get("creator"))
    base_token = cast(ChecksumAddress, args.get("baseToken"))
    quote_token = cast(ChecksumAddress, args.get("quoteToken"))
    market = cast(ChecksumAddress, args.get("market"))
    quote_decimals = cast(int, args.get("quoteDecimals"))
    base_decimals = cast(int, args.get("baseDecimals"))
    config = cast(dict[str, Any], args.get("config"))
    settings = cast(dict[str, Any], args.get("settings"))
    nonce = cast(int, args.get("eventNonce", 0))

    return MarketCreatedEvent(
        **base_info,
        creator=creator,
        base_token=base_token,
        quote_token=quote_token,
        market=market,
        quote_decimals=quote_decimals,
        base_decimals=base_decimals,
        config=config,
        settings=settings,
        nonce=nonce,
    )


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

    account = cast(ChecksumAddress, args.get("account"))
    operator = cast(ChecksumAddress, args.get("operator"))
    nonce = cast(int, args.get("eventNonce", 0))

    return OperatorApprovedEvent(
        **base_info,
        account=account,
        operator=operator,
        nonce=nonce,
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

    account = cast(ChecksumAddress, args.get("account"))
    operator = cast(ChecksumAddress, args.get("operator"))
    nonce = cast(int, args.get("eventNonce", 0))

    return OperatorDisapprovedEvent(
        **base_info,
        account=account,
        operator=operator,
        nonce=nonce,
    )


def parse_roles_approved(event_data: EventData) -> RolesApprovedEvent:
    """
    Parse RolesApproved event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed RolesApprovedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    account = cast(ChecksumAddress, args.get("account"))
    operator = cast(ChecksumAddress, args.get("operator"))
    roles = cast(int, args.get("roles"))
    nonce = cast(int, args.get("eventNonce", 0))

    return RolesApprovedEvent(
        **base_info,
        account=account,
        operator=operator,
        roles=roles,
        nonce=nonce,
    )


def parse_roles_disapproved(event_data: EventData) -> RolesDisapprovedEvent:
    """
    Parse RolesDisapproved event.

    Args:
        event_data: Raw event data from web3

    Returns:
        Typed RolesDisapprovedEvent
    """
    args = event_data.get("args", {})
    base_info = _create_base_event_info(event_data)

    account = cast(ChecksumAddress, args.get("account"))
    operator = cast(ChecksumAddress, args.get("operator"))
    roles = cast(int, args.get("roles"))
    nonce = cast(int, args.get("eventNonce", 0))

    return RolesDisapprovedEvent(
        **base_info,
        account=account,
        operator=operator,
        roles=roles,
        nonce=nonce,
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

    account = cast(ChecksumAddress, args.get("account"))
    recipient = cast(ChecksumAddress, args.get("recipient"))
    token = cast(ChecksumAddress, args.get("token"))
    amount = cast(int, args.get("amount"))
    nonce = cast(int, args.get("eventNonce", 0))

    return WithdrawEvent(
        **base_info,
        account=account,
        recipient=recipient,
        token=token,
        amount=amount,
        nonce=nonce,
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
    "CancelFailed": parse_cancel_failed,
    "Initialized": parse_initialized,
    "OwnershipTransferStarted": parse_ownership_transfer_started,
    "OwnershipTransferred": parse_ownership_transferred,
}

# Add CLOB Manager event parsers to the global dictionary
CLOB_MANAGER_EVENT_PARSERS = {
    "AccountCredited": parse_account_credited,
    "AccountDebited": parse_account_debited,
    "AccountFeeTierUpdated": parse_account_fee_tier_updated,
    "Deposit": parse_deposit,
    "FeeCollected": parse_fee_collected,
    "FeeRecipientSet": parse_fee_recipient_set,
    "MarketCreated": parse_market_created,
    "OperatorApproved": parse_operator_approved,
    "OperatorDisapproved": parse_operator_disapproved,
    "Withdraw": parse_withdraw,
    "OwnershipHandoverCanceled": parse_ownership_handover_canceled,
    "OwnershipHandoverRequested": parse_ownership_handover_requested,
    "OwnershipTransferred": parse_ownership_transferred,
}

# Update the existing EVENT_PARSERS dictionary
EVENT_PARSERS.update(CLOB_MANAGER_EVENT_PARSERS)  # type: ignore[assignment]


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
        return cast(CLOBEvent, parser_func(event_data))

    # Return base event for unknown event types
    args = event_data.get("args", {})
    nonce = args.get("nonce", args.get("eventNonce", 0))

    raw_data = cast(dict[str, Any], cast(object, event_data))

    return CLOBEvent(
        tx_hash=event_data.get("transactionHash"),
        log_index=event_data.get("logIndex"),
        block_number=event_data.get("blockNumber"),
        address=event_data.get("address"),
        event_name=event_name,
        raw_data=raw_data,
    )