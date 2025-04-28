"""Example of on-chain trading with the GTE client."""

import asyncio
import logging
from typing import Optional

from web3 import AsyncWeb3
from web3.types import TxReceipt

from examples.utils import show_all_orders
from gte_py.api.contracts.iclob_historical import CLOBHistoricalQuerier
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Side, TimeInForce, Market

from utils import (
    print_separator,
    display_market_info,
    show_balances,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
    MARKET_ADDRESS
)


async def approve_and_deposit_example(client: Client, market: Market, amount: float, price: float) -> None:
    """Example of approving and depositing tokens to the exchange."""
    print_separator("Approve and Deposit Tokens Example")

    # Get the quote token address
    quote = market.quote_token_address
    print(f"Creating transaction to approve and deposit {amount} {market.quote_asset.symbol}...")

    # Get deposit transactions - this returns a list containing [approve_tx, deposit_tx]
    tx_funcs = client.account.deposit_to_market(
        token_address=quote,
        amount=market.round_quote_to_ticks_int(amount * price),
        gas=100000,
    )

    print("\nSending approval transaction...")
    await tx_funcs[0].send_wait(WALLET_PRIVATE_KEY)

    print("\nSending deposit transaction...")
    await tx_funcs[1].send_wait(WALLET_PRIVATE_KEY)

    # Now deposit the base token
    base = market.base_token_address
    print(f"Creating transaction to approve and deposit {amount} {market.base_asset.symbol}...")
    tx_funcs = client.account.deposit_to_market(
        token_address=base,
        amount=market.round_base_to_lots_int(amount),
        gas=100000,
    )

    print("\nSending approval transaction...")
    await tx_funcs[0].send_wait(WALLET_PRIVATE_KEY)

    print("\nSending deposit transaction...")
    await tx_funcs[1].send_wait(WALLET_PRIVATE_KEY)


async def limit_order_example(client: Client, market: Market) -> None:
    """Example of creating a limit order."""
    print_separator("Limit Order Example")

    # Current market price (or estimate)
    price = market.round_quote_to_ticks_int(market.tick_size)
    amount = market.round_base_to_lots_int(market.lot_size)

    print(f"Creating BUY limit order at price: {price}")
    tx_func = await client.execution.place_limit_order(
        market=market,
        side=Side.BUY,
        amount=amount,
        price=price,
        time_in_force=TimeInForce.GTC,
    )

    # Use async version for sending transaction
    order = await tx_func.send_wait(WALLET_PRIVATE_KEY)
    print(f"Order created: {order}")
    await get_order_status(client, market, order.order_id)

    print(f"Creating SELL limit order at price: {price}")
    tx_func = await client.execution.place_limit_order(
        market=market,
        side=Side.SELL,
        amount=amount,
        price=price,
        time_in_force=TimeInForce.GTC,
    )

    # Use async version for sending transaction
    order = await tx_func.send_wait(WALLET_PRIVATE_KEY)
    print(f"Order created: {order}")
    await get_order_status(client, market, order.order_id)


async def cancel_order_example(client: Client, market: Market, order_id: Optional[int] = None) -> Optional[TxReceipt]:
    """Example of cancelling an order."""
    print_separator("Cancel Order Example")

    if not order_id:
        print("No order ID provided, using example ID")
        order_id = 12345

    print(f"Creating cancel transaction for order ID {order_id}...")
    tx_func = await client.execution.cancel_order(
        market=market,
        order_id=order_id,
        gas=200000,
    )

    print("\nSending transaction...")
    receipt = await tx_func.send_wait(WALLET_PRIVATE_KEY)
    return receipt


async def get_order_status(client: Client, market: Market, order_id: int) -> None:
    """Get the status of an order."""
    print_separator("Order Status Example")

    try:
        order = await client.execution.get_order(market, order_id=order_id)

        print(f"Order ID: {order.order_id}")
        print(f"Market: {market.pair}")
        print(f"Side: {order.side.name}")
        print(f"Price: {order.price}")
        print(f"Amount: {order.amount}")
        print(f"Status: {order.status}")

    except Exception as e:
        print(f"Couldn't fetch on-chain order status: {str(e)}")


async def show_orders(client: Client, market: Market) -> None:
    """Show orders for the user."""
    print_separator("User Orders")

    try:
        orders = await client.execution.get_orders(market)

        print(f"Orders for market {market.pair}:")
        for order in orders:
            print(f"  ID: {order.order_id}")
            print(f"  Side: {order.side.name}")
            print(f"  Price: {order.price}")
            print(f"  Size: {getattr(order, 'size', order.amount)}")
            print(f"  Status: {order.status.name if hasattr(order, 'status') else 'N/A'}")

    except Exception as e:
        print(f"Couldn't fetch on-chain orders: {str(e)}")
        print("This feature requires AsyncWeb3 provider and a market with contract address")


async def display_recent_matches(client: Client, market: Market, block_range: int = 1000) -> None:
    """Fetch and display recent order matches for the market."""
    print_separator("Recent Order Matches")

    try:
        # Get current block number
        current_block = await client._web3.eth.block_number
        from_block = max(1, current_block - block_range)

        # Initialize the historical querier
        historical_querier = CLOBHistoricalQuerier(client._web3, market.address)

        # Fetch recent order matches
        matches = historical_querier.query_order_matched(from_block=from_block)

        if not matches:
            print(f"No order matches found in the last {block_range} blocks")
            return

        print(f"Found {len(matches)} recent order matches:")
        for i, match in enumerate(matches, 1):
            print(f"\nMatch #{i}:")
            print(f"  Block: {match.block_number}")

    except Exception as e:
        print(f"Error fetching recent order matches: {str(e)}")


async def main() -> None:
    """Run the on-chain trading examples."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(network.rpc_http))

    print("Connected to blockchain:")
    print(f"Chain ID: {await web3.eth.chain_id}")

    # Check for required environment variables
    if not WALLET_ADDRESS or not WALLET_PRIVATE_KEY:
        raise ValueError("WALLET_ADDRESS and WALLET_PRIVATE_KEY must be set in .env file")

    wallet_address = AsyncWeb3.to_checksum_address(WALLET_ADDRESS)

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, sender_address=wallet_address)

    # Get a market to work with
    market = await display_market_info(client, MARKET_ADDRESS)

    # Show balances
    await show_balances(client, market)
    # Display all orders
    await show_all_orders(client, market)

    # Display recent order matches
    await display_recent_matches(client, market)

    print("\nNOTE: For WETH wrapping and unwrapping examples, see wrap_weth.py")

    # Deposit tokens example
    await approve_and_deposit_example(client, market, amount=1, price=1)

    # Check balances after deposit
    await show_balances(client, market)

    # Order examples
    await limit_order_example(client, market)

    # Cancel an order
    await cancel_order_example(client, market, order_id=None)

    # Show all orders
    await show_orders(client, market)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
