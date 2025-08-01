"""Example of watching CLOB events in real-time."""
import sys
sys.path.append(".")
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from web3 import AsyncWeb3
from gte_py.api.chain.event_source import EventStream
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import WALLET_PRIVATE_KEY, WALLET_ADDRESS, print_separator
from examples.constants import BTC_USD_CLOB

# BTC/USD market address
MARKET_ADDRESS = BTC_USD_CLOB


def handle_limit_order(event):
    """Handle a limit order event."""
    print(f"LIMIT ORDER: Account: {event.account}")
    print(f"  Order ID: {event.order_id}")
    print(f"  Amount Posted: {event.amount_posted_in_base}")
    print(f"  Quote Amount Traded: {event.quote_token_amount_traded}")
    print(f"  Base Amount Traded: {event.base_token_amount_traded}")
    print(f"  Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print("")


def handle_fill_order(event):
    """Handle a fill order event."""
    print(f"FILL ORDER: Account: {event.account}")
    print(f"  Order ID: {event.order_id}")
    print(f"  Quote Amount Traded: {event.quote_token_amount_traded}")
    print(f"  Base Amount Traded: {event.base_token_amount_traded}")
    print(f"  Taker Fee: {event.taker_fee}")
    print(f"  Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print("")


def handle_order_canceled(event):
    """Handle an order canceled event."""
    print(f"ORDER CANCELED: Order ID: {event.order_id}")
    print(f"  Owner: {event.owner}")
    print(f"  Quote Refunded: {event.quote_token_refunded}")
    print(f"  Base Refunded: {event.base_token_refunded}")
    print(f"  Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print("")


def handle_order_amended(event):
    """Handle an order amended event."""
    print(f"ORDER AMENDED: Quote Delta: {event.quote_token_delta}")
    print(f"  Base Delta: {event.base_token_delta}")
    print(f"  Event Nonce: {event.nonce}")
    print(f"  Pre-amend: {event.pre_amend}")
    print(f"  Args: {event.args}")
    print(f"  Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print("")


def handle_order_matched(event):
    """Handle an order matched event."""
    print(f"ORDER MATCHED: Taker: {event.taker_order_id} Maker: {event.maker_order_id}")
    print(f"  Taker Owner: {event.taker_order.owner}")
    print(f"  Maker Owner: {event.maker_order.owner}")
    print(f"  Price: {event.maker_order.price}")
    print(f"  Traded Base: {event.traded_base}")
    print(f"  Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    print("")


async def watch_account_orders(clob: ICLOB, account, duration_seconds=60):
    """Watch for all orders from a specific account for a duration."""
    print_separator(f"Watching Orders for Account {account}")

    print(f"Streaming events for {duration_seconds} seconds...")

    # Create streams with longer poll intervals to avoid rate limiting
    # 5 streams * 1 request per 6 seconds = ~0.83 requests/second (well under 5/sec limit)
    limit_stream = clob.stream_limit_order_processed_events(account=account, poll_interval=6.0)
    fill_stream = clob.stream_fill_order_processed_events(account=account, poll_interval=6.0)

    # Set up handlers and exit conditions
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=duration_seconds)

    exit_condition = lambda: datetime.now() >= end_time

    # Set up async tasks
    tasks = [
        asyncio.create_task(process_stream_async(limit_stream, handle_limit_order, exit_condition)),
        asyncio.create_task(process_stream_async(fill_stream, handle_fill_order, exit_condition))
    ]

    # Wait for tasks to complete
    await asyncio.gather(*tasks)

    print(f"Finished watching account orders after {duration_seconds} seconds")


async def watch_all_market_activity(clob: ICLOB, duration_seconds=60):
    """Watch all market activity for a duration."""
    print_separator("Watching All Market Activity")

    print(f"Streaming events for {duration_seconds} seconds...")

    # Create streams with staggered poll intervals to avoid rate limiting
    limit_stream = clob.stream_limit_order_processed_events(poll_interval=3.0)
    fill_stream = clob.stream_fill_order_processed_events(poll_interval=3.0)
    cancel_stream = clob.stream_order_canceled_events(poll_interval=3.0)
    amend_stream = clob.stream_order_amended_events(poll_interval=3.0)
    match_stream = clob.stream_order_matched_events(poll_interval=3.0)

    # Set up handlers and exit conditions
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=duration_seconds)

    exit_condition = lambda: datetime.now() >= end_time

    # Set up async tasks
    tasks = [
        asyncio.create_task(process_stream_async(limit_stream, handle_limit_order, exit_condition)),
        asyncio.create_task(process_stream_async(fill_stream, handle_fill_order, exit_condition)),
        asyncio.create_task(process_stream_async(cancel_stream, handle_order_canceled, exit_condition)),
        asyncio.create_task(process_stream_async(amend_stream, handle_order_amended, exit_condition)),
        asyncio.create_task(process_stream_async(match_stream, handle_order_matched, exit_condition))
    ]

    # Wait for tasks to complete
    await asyncio.gather(*tasks)

    print(f"Finished watching market activity after {duration_seconds} seconds")


async def process_stream_async(stream: EventStream[Any], handler, exit_condition):
    """Process an event stream asynchronously."""
    # Get initial events
    async for event in stream.stream():
        handler(event)
        if exit_condition():
            break


async def main():
    """Run the CLOB event watching examples."""
    config = TESTNET_CONFIG

    async with GTEClient(
        config=config,
        wallet_private_key=WALLET_PRIVATE_KEY,
    ) as client:
        print("Connected to blockchain:")
        print(f"Chain ID: {await client._web3.eth.chain_id}")
        print(f"Latest block: {await client._web3.eth.get_block_number()}")

        # Get the CLOB contract from execution
        clob = client.execution._clob_client.get_clob(AsyncWeb3.to_checksum_address(MARKET_ADDRESS))

        # Example 1: Watch for all market activity for 30 seconds
        await watch_all_market_activity(clob, duration_seconds=30)

        # Example 2: Watch for specific account activity for 30 seconds
        await watch_account_orders(clob, WALLET_ADDRESS, duration_seconds=30)

        print("\nAll examples completed. Exiting.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
