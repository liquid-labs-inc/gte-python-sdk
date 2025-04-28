"""Common utilities for GTE examples."""

import os
from typing import Optional, List

from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from tabulate import tabulate
from web3 import AsyncWeb3

from gte_py import Client, Order
from gte_py.models import Market

# Load environment variables from .env file
load_dotenv()

# Common environment variables
WALLET_ADDRESS = AsyncWeb3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
WALLET_PRIVATE_KEY = HexStr(os.getenv("WALLET_PRIVATE_KEY"))
MARKET_ADDRESS = AsyncWeb3.to_checksum_address(
    os.getenv("MARKET_ADDRESS", "0xfaf0BB6F2f4690CA4319e489F6Dc742167B9fB10"))  # MEOW/WETH


def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    return f"{price:.8f}"


def format_market_table(markets: List[Market], title: str) -> None:
    """Format and print a table of markets."""
    print_separator(title)

    if not markets:
        print("No markets found!")
        return

    # Prepare table rows
    rows = []
    for i, market in enumerate(markets, 1):
        rows.append(
            [
                i,
                market.pair,
                market.address[:10] + "...",
                market.market_type.value if hasattr(market, "market_type") else "N/A",
                format_price(market.price),
                f"{market.volume_24h:.2f}" if market.volume_24h else "N/A",
                "Yes" if market.address else "No",
            ]
        )

    # Print table
    headers = ["#", "Pair", "Address", "Type", "Price", "24h Volume", "On-chain"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"Total: {len(markets)} markets")


def get_web3_wallet() -> str:
    """Create a AsyncWeb3 instance and get wallet address."""
    if not WALLET_ADDRESS:
        raise ValueError("WALLET_ADDRESS not found in environment")

    return AsyncWeb3.to_checksum_address(WALLET_ADDRESS)


async def display_market_info(client: Client, market_address: ChecksumAddress) -> Market:
    """Get and display market information."""

    print(f"Using market: {market_address}")
    market = await client.get_market(market_address)

    print(f"Market: {market.pair}")
    print(f"Base token: {market.base_asset.symbol} ({market.base_token_address})")
    print(f"Quote token: {market.quote_asset.symbol} ({market.quote_token_address})")
    print(f"Tick size: {market.tick_size_in_quote}")
    print(f"Lot size: {market.lot_size_in_base}")

    return market


async def show_balances(client: Client, market: Market) -> None:
    """Display token balances for a market."""
    print_separator("Token Balances")

    # Get balances for base and quote tokens
    base_token = market.base_token_address
    quote_token = market.quote_token_address

    print(f"Getting balances for {market.base_asset.symbol} and {market.quote_asset.symbol}...")

    base_wallet, base_exchange = await client.get_balance(base_token)
    quote_wallet, quote_exchange = await client.get_balance(quote_token)

    print(f"{market.base_asset.symbol} balances:")
    print(f"  Wallet: {base_wallet:.6f}")
    print(f"  Exchange: {base_exchange:.6f}")

    print(f"{market.quote_asset.symbol} balances:")
    print(f"  Wallet: {quote_wallet:.6f}")
    print(f"  Exchange: {quote_exchange:.6f}")


async def show_all_orders(client: Client, market: Market):
    """Show all orders for a market."""
    print_separator("All Orders")

    try:
        # Get all orders for the market
        orders: List[Order] = await client.execution.get_live_orders(market)

        # Display order details
        for order in orders:
            print(f"Order ID: {order.order_id}")
            print(f"  Owner: {order.owner}")
            print(f"  Side: {order.side}")
            print(f"  Price: {order.price}")
            print(f"  Amount: {order.amount}")
            print(f"  Status: {order.status}")
            print(f"  Order Type: {order.order_type}")
            print(f"  Timestamp: {order.created_at}")
            print("-" * 20)

    except Exception as e:
        print(f"Couldn't fetch on-chain orders: {str(e)}")
        print("This feature requires AsyncWeb3 provider and a market with contract address")
