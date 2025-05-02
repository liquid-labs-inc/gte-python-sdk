"""Example of on-chain trading with the GTE client."""

import asyncio
import logging
from typing import Optional

from web3.types import TxReceipt

from examples.utils import show_all_orders
from gte_py.api.chain.iclob_historical import CLOBHistoricalQuerier
from gte_py.api.chain.utils import make_web3
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


async def approve_and_deposit_example(client: Client, market: Market, quantity: float, price: float) -> None:
    """Example of approving and depositing tokens to the exchange."""
    print_separator("Approve and Deposit Tokens Example")

    # Get the quote token address
    print(f"Creating transaction to approve and deposit {quantity} {market.quote.symbol}...")
    # Get deposit transactions - this returns a list containing [approve_tx, deposit_tx]
    await client.account.ensure_deposit(
        token_address=market.quote.address,
        amount=market.quote.convert_quantity_to_amount(quantity * price),
        gas=50 * 10000000
    )

    # Now deposit the base token
    print(f"Creating transaction to approve and deposit {quantity} {market.base.symbol}...")
    await client.account.ensure_deposit(
        token_address=market.base.address,
        amount=market.base.convert_quantity_to_amount(quantity),
        gas=50 * 10000000
    )


async def limit_order_example(client: Client, market: Market, quantity: float, price: float) -> list[int]:
    """Example of creating a limit order."""
    print_separator("Limit Order Example")

    results = []
    print(f"Creating BUY limit order at price: {price}")
    order = await client.execution.place_limit_order(
        market=market,
        side=Side.BUY,
        amount=market.base.convert_quantity_to_amount(quantity),
        price=market.quote.convert_quantity_to_amount(price),
        time_in_force=TimeInForce.GTC,
        gas=50 * 10000000
    )
    results.append(order.order_id)

    print(f"Order created: {order}")
    await get_order_status(client, market, order.order_id)

    print(f"Creating SELL limit order at price: {price}")
    order = await client.execution.place_limit_order(
        market=market,
        side=Side.SELL,
        amount=market.base.convert_quantity_to_amount(quantity),
        price=market.quote.convert_quantity_to_amount(price),
        time_in_force=TimeInForce.GTC,
        gas=50 * 10000000
    )
    results.append(order.order_id)

    await get_order_status(client, market, order.order_id)
    return results


async def cancel_order_example(client: Client, market: Market, order_id: int = None) -> Optional[TxReceipt]:
    """Example of cancelling an order."""
    print_separator("Cancel Order Example")

    print(f"Creating cancel transaction for order ID {order_id}...")
    await client.execution.cancel_order(
        market=market,
        order_id=order_id,
    )


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
        orders = await client.execution.get_open_orders(market)

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
        matches = await historical_querier.query_order_matched(from_block=from_block)

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
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)

    print("Connected to blockchain:")
    print(f"Chain ID: {await web3.eth.chain_id}")

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")

    client = Client(web3=web3, config=network, account=WALLET_ADDRESS)
    await client.init()
    # Get a market to work with
    market = await display_market_info(client, MARKET_ADDRESS)

    # Show balances
    await show_balances(client, market)
    # Display all orders
    # await show_all_orders(client, market)

    # Display recent order matches
    await display_recent_matches(client, market)

    print("\nNOTE: For WETH wrapping and unwrapping examples, see wrap_weth.py")

    bid, ask = await client.orderbook.get_tob(market)
    price = market.base.convert_amount_to_quantity(bid)
    amount = 0.1

    # Deposit tokens example
    await approve_and_deposit_example(client, market, quantity=amount, price=price)

    # Check balances after deposit
    await show_balances(client, market)

    # Order examples
    order_ids = await limit_order_example(client, market, quantity=amount, price=price)
    for order_id in order_ids:
        await cancel_order_example(client, market, order_id)

    # Show all orders
    await show_orders(client, market)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
