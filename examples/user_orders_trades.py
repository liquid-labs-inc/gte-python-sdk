"""Example of fetching user orders and trades."""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from web3 import Web3

from gte_py import Client

# Load environment variables from .env file
load_dotenv()

# Configure these variables through environment or directly
RPC_URL = os.getenv("RPC_URL", "https://rpc-testnet.example.com")
ROUTER_ADDRESS = os.getenv("ROUTER_ADDRESS")
USER_ADDRESS = os.getenv("WALLET_ADDRESS", "0x1234567890abcdef1234567890abcdef12345678")


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def format_timestamp(timestamp_ms):
    """Format a millisecond timestamp as a human-readable datetime."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def show_user_orders(client, user_address, market_address=None):
    """Show user orders."""
    print_separator("User Orders")

    # Get open orders
    open_orders = await client.get_user_orders(
        user_address=user_address, market_address=market_address, status="open"
    )

    print(f"Found {len(open_orders)} open orders")
    for i, order in enumerate(open_orders, 1):
        print(f"\nOrder {i}:")
        print(f"  ID: {order.order_id}")
        print(f"  Market: {order.market_address}")
        print(f"  Type: {order.order_type.name} {order.side.name}")
        print(f"  Price: {order.price}")
        print(f"  Amount: {order.amount}")
        print(f"  Time: {format_timestamp(order.created_at)}")
        print(f"  Status: {order.status.name}")

    # Get filled orders
    filled_orders = await client.get_user_orders(
        user_address=user_address, market_address=market_address, status="filled"
    )

    print(f"\nFound {len(filled_orders)} filled orders")
    for i, order in enumerate(filled_orders, 1):
        print(f"\nOrder {i}:")
        print(f"  ID: {order.order_id}")
        print(f"  Market: {order.market_address}")
        print(f"  Type: {order.order_type.name} {order.side.name}")
        print(f"  Price: {order.price}")
        print(f"  Amount: {order.amount}")
        print(f"  Filled: {order.filled_amount} @ {order.filled_price}")
        print(f"  Time: {format_timestamp(order.created_at)}")
        print(f"  Status: {order.status.name}")


async def show_user_trades(client, user_address, market_address=None):
    """Show user trades."""
    print_separator("User Trades")

    trades = await client.get_user_trades(user_address=user_address, market_address=market_address)

    print(f"Found {len(trades)} trades")
    for i, trade in enumerate(trades, 1):
        print(f"\nTrade {i}:")
        print(f"  ID: {trade.trade_id}")
        print(f"  Market: {trade.market_address}")
        print(f"  Side: {trade.side.name}")
        print(f"  Price: {trade.price}")
        print(f"  Size: {trade.size}")
        print(f"  Time: {format_timestamp(trade.timestamp)}")
        print(f"  Transaction: {trade.tx_hash}")


async def show_order_book(client, market_address):
    """Show order book snapshot."""
    print_separator("Order Book Snapshot")

    try:
        # This only works with Web3 provider and contract address
        book = await client.get_order_book_snapshot(market_address, depth=5)

        print("Asks (Sell Orders):")
        for i, ask in enumerate(reversed(book["asks"]), 1):
            print(
                f"  {i}. Price: {ask['price']} | Size: {ask['size']} | Orders: {ask['orderCount']}"
            )

        print("\nBids (Buy Orders):")
        for i, bid in enumerate(book["bids"], 1):
            print(
                f"  {i}. Price: {bid['price']} | Size: {bid['size']} | Orders: {bid['orderCount']}"
            )

    except Exception as e:
        print(f"Couldn't fetch on-chain order book: {str(e)}")
        print("This feature requires Web3 provider and a market with contract address")


async def show_user_balances(client, user_address, market_address):
    """Show user balances in the CLOB."""
    print_separator("User CLOB Balances")

    try:
        # This only works with Web3 provider and contract address
        balances = await client.get_user_balances(
            user_address=user_address, market_address=market_address
        )

        market = await client.get_market(market_address)

        base_balance = balances["baseBalance"] / (10**market.base_decimals)
        quote_balance = balances["quoteBalance"] / (10**market.quote_decimals)

        print(f"Base Token ({market.base_asset.symbol}): {base_balance}")
        print(f"Quote Token ({market.quote_asset.symbol}): {quote_balance}")

    except Exception as e:
        print(f"Couldn't fetch on-chain balances: {str(e)}")
        print("This feature requires Web3 provider and a market with contract address")


async def main():
    """Run the example."""
    print("GTE User Orders & Trades Example")
    print_separator("Configuration")
    print(f"User Address: {USER_ADDRESS}")

    # Initialize client
    web3 = None
    if RPC_URL and RPC_URL != "https://rpc-testnet.example.com":
        try:
            web3 = Web3(Web3.HTTPProvider(RPC_URL))
            print(f"Web3 Connected: {web3.is_connected()}")
        except Exception as e:
            print(f"Couldn't initialize Web3: {e}")
            web3 = None

    client = Client(web3=web3, router_address=ROUTER_ADDRESS)

    try:
        # Get a market for examples
        markets = await client.get_markets(limit=1)
        if not markets:
            print("No markets found!")
            return

        market = markets[0]
        print(f"Using market: {market.pair} ({market.address})")

        # Run examples
        await show_user_orders(client, USER_ADDRESS, market.address)
        await show_user_trades(client, USER_ADDRESS, market.address)

        # These only work with on-chain markets
        if web3 and web3.is_connected() and market.contract_address:
            await show_order_book(client, market.address)
            await show_user_balances(client, USER_ADDRESS, market.address)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
