"""Common utilities for GTE examples."""

import os
from typing import Optional, List

from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from tabulate import tabulate
from web3 import AsyncWeb3

from gte_py.clients import Client
from gte_py.models import Market, Order

# Load environment variables from .env file
load_dotenv()

# Common environment variables
WALLET_ADDRESS = AsyncWeb3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
WALLET_PRIVATE_KEY = HexStr(os.getenv("WALLET_PRIVATE_KEY"))
MARKET_ADDRESS = AsyncWeb3.to_checksum_address(
    os.getenv("MARKET_ADDRESS", "0x5ca9f32d4ce7cc0f782213c446c2ae14b754a623"))  # ETH/USD


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
                f"{market.volume_24hr_usd:.2f}" if market.volume_24hr_usd else "N/A",
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
    market = await client.info.get_market(market_address)

    print(f"Market: {market.pair}")
    print(f"Base token: {market.base.symbol} ({market.base.address})")
    print(f"Quote token: {market.quote.symbol} ({market.quote.address})")

    return market


async def show_balances(client: Client, market: Market) -> None:
    """Display token balances for a market."""
    print_separator("Token Balances")

    print(f"Getting balances for {market.base.symbol} and {market.quote.symbol}...")
    wei = await client.user.get_eth_balance()
    print("ETH balance:", AsyncWeb3.from_wei(wei, "ether"))

    await display_token_balances(client, market.base.address)

    await display_token_balances(client, market.quote.address)


async def display_token_balances(client: Client, token_address: ChecksumAddress, header: bool = True) -> None:
    """
    Display detailed balance information for a specific token.

    Args:
        client: Initialized GTE client
        token_address: Address of the token to check
    """
    if header:
        print_separator(f"Token Balance Details: {token_address}")

    try:
        # Get wallet and exchange balances
        token = client.token.get_erc20(token_address)
        exchange_balance = await client.user.get_token_balance(token_address)
        exchange_balance = await token.convert_amount_to_quantity(exchange_balance)

        token_balance = await token.balance_of(WALLET_ADDRESS)
        token_balance = await token.convert_amount_to_quantity(token_balance)
        allowance = await token.allowance(WALLET_ADDRESS, client.config.router_address)
        allowance = await token.convert_amount_to_quantity(allowance)
        print(f"Token Name:    {await token.name()}")
        print(f"Token Balance:    {token_balance:.6f}")
        print(f"Allowance:       {allowance:.6f}")
        print(f"Exchange Balance: {exchange_balance:.6f}")

    except Exception as e:
        print(f"Error retrieving token details: {e}")


async def show_live_orders(client: Client, market: Market):
    """Show live orders for a market and the account."""
    print_separator("All Orders")

    try:
        # Get all orders for the market
        orders: List[Order] = await client.execution.get_open_orders(market)

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
