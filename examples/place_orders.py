"""Example of on-chain trading with the GTE client."""
import sys

sys.path.append(".")
import asyncio
import logging
from typing import Optional

from web3.types import TxReceipt

from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce, Market

from utils import (
    print_separator,
    display_market_info,
    show_balances,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
    MARKET_ADDRESS, show_live_orders
)


async def limit_order_example(client: Client, market: Market, quantity: float, price: float) -> list[int]:
    """Example of creating a limit order."""
    print_separator("Limit Order Example")
    order_futures = []
    for i in range(15):
        order = client.execution.place_limit_order(
            market=market,
            side=OrderSide.BUY,
            amount=market.base.convert_quantity_to_amount(quantity),
            price=market.quote.convert_quantity_to_amount(price),
            time_in_force=TimeInForce.GTC,
            gas=50 * 10000000
        )
        order_futures.append(order)
    # Wait for all orders to be created
    await asyncio.gather(*order_futures)

    return []
    results = []
    print(f"Creating BUY limit order at price: {price}")
    order = await client.execution.place_limit_order(
        market=market,
        side=OrderSide.BUY,
        amount=market.base.convert_quantity_to_amount(quantity),
        price=market.quote.convert_quantity_to_amount(price),
        time_in_force=TimeInForce.GTC,
        gas=50 * 10000000
    )
    print(f"Order created: {order}")
    if order:
        results.append(order.order_id)
        await get_order_status(client, market, order.order_id)

    print(f"Creating SELL limit order at price: {price}")
    order = await client.execution.place_limit_order(
        market=market,
        side=OrderSide.SELL,
        amount=market.base.convert_quantity_to_amount(quantity),
        price=market.quote.convert_quantity_to_amount(price),
        time_in_force=TimeInForce.GTC,
        gas=50 * 10000000
    )
    print(f"Order created: {order}")
    if order:
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
        order = await client.market.get_order(market, order_id=order_id)

        print(f"Order ID: {order.order_id}")
        print(f"Market: {market.pair}")
        print(f"Side: {order.side.name}")
        print(f"Price: {order.price}")
        print(f"Amount: {order.remaining_amount}")
        print(f"Status: {order.status}")

    except Exception as e:
        print(f"Couldn't fetch on-chain order status: {str(e)}")


async def display_recent_matches(client: Client, market: Market, block_range: int = 1000) -> None:
    """Fetch and display recent order matches for the market."""
    print_separator("Recent Order Matches")

    try:
        # Get current block number
        current_block = await client._web3.eth.block_number
        from_block = max(1, current_block - block_range)

        # Initialize the historical querier
        clob = client.clob.get_clob(market.address)

        # Fetch recent order matches
        matches = await clob.get_order_matched_events(from_block)

        if not matches:
            print(f"No order matches found in the last {block_range} blocks")
            return

        print(f"Found {len(matches)} recent order matches:")

        for i, match in enumerate(matches, 1):
            print(f"\nMatch #{i}:")
            print(f"  Block: {match.block_number}")
            print(f"  Transaction Hash: {match.tx_hash.to_0x_hex()}")
            print(f"  Maker Order ID: {match.maker_order_id}")
            print(f"  Taker Order ID: {match.taker_order_id}")
            print(f"  Maker Order: {match.maker_order}")
            print(f"  Taker Order: {match.taker_order}")
            print(f"  Traded Base: {match.traded_base}")


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
    await show_live_orders(client, market)

    # Display recent order matches
    # await display_recent_matches(client, market)

    print("\nNOTE: For WETH wrapping and unwrapping examples, see wrap_weth.py")

    bid, ask = await client.market.get_tob(market)
    price = market.base.convert_amount_to_quantity(bid)
    quantity = 1.0

    # Check balances after deposit
    await show_balances(client, market)

    order_ids = await limit_order_example(client, market, quantity=quantity, price=price)
    for order_id in order_ids:
        await cancel_order_example(client, market, order_id)

    # Show all orders
    # await show_all_orders(client, market)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
