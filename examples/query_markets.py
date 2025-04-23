"""Example of querying all available markets from GTE."""

import asyncio

from eth_utils import to_checksum_address
from tabulate import tabulate
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.models import Market


# Configure these variables through environment or directly


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def format_price(price: float | None) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    return f"{price:.8f}"


def format_market_table(markets: list[Market], title: str):
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
                "Yes" if market.contract_address else "No",
            ]
        )

    # Print table
    headers = ["#", "Pair", "Address", "Type", "Price", "24h Volume", "On-chain"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"Total: {len(markets)} markets")


def format_chain_market_table(markets: list[Market], title: str):
    """Format and print a table of on-chain markets."""
    print_separator(title)

    if not markets:
        print("No on-chain markets found!")
        return

    # Prepare table rows
    rows = []
    for i, market in enumerate(markets, 1):
        rows.append(
            [
                i,
                f"{market.contract_address[:10]}...",
                f"{market.base_token[:10]}...",
                f"{market.quote_token[:10]}...",
                market.base_decimals,
                market.quote_decimals,
                market.tick_size_in_quote,
            ]
        )

    # Print table
    headers = ["#", "Contract", "Base Token", "Quote Token", "Base Dec", "Quote Dec", "Tick Size"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"Total: {len(markets)} on-chain markets")


async def query_markets(client: Client):
    """Query markets from the API."""
    # Get all markets
    print("Fetching all markets from API...")
    markets = await client.get_markets(limit=100)
    format_market_table(markets, "All Markets")

    # Get markets by type
    amm_markets = await client.get_markets(limit=50, market_type="amm")
    format_market_table(amm_markets, "AMM Markets")

    launchpad_markets = await client.get_markets(limit=50, market_type="launchpad")
    format_market_table(launchpad_markets, "Launchpad Markets")

    # Filter by price
    high_value_markets = await client.get_markets(limit=50, max_price=1000.0)
    format_market_table(high_value_markets, "Markets with price < 1000")

    # Find markets with on-chain contracts
    onchain_markets = [m for m in markets if m.address]
    format_market_table(onchain_markets, "Markets with On-chain Contracts")

    # Demonstrate pagination
    print_separator("Pagination Example")
    page_size = 20
    for i in range(3):  # Get 3 pages
        offset = i * page_size
        page = await client.get_markets(limit=page_size, offset=offset)
        print(f"Page {i + 1}: Retrieved {len(page)} markets (offset: {offset})")
        if not page:
            break



async def query_market_details(client: Client, market: Market):
    """Query detailed information for a specific market."""
    print_separator("Market Details Example")

    # Display detailed market information
    print(f"Market: {market.pair} ({market.address})")
    print(f"Type: {market.market_type.value}")
    print(f"Price: {format_price(market.price)}")
    print(f"24h Volume: {market.volume_24h if market.volume_24h else 'N/A'}")

    # Base asset details
    print("\nBase Asset:")
    print(f"  Symbol: {market.base_asset.symbol}")
    print(f"  Address: {market.base_asset.address}")
    print(f"  Decimals: {market.base_asset.decimals}")

    # Quote asset details
    print("\nQuote Asset:")
    print(f"  Symbol: {market.quote_asset.symbol}")
    print(f"  Address: {market.quote_asset.address}")
    print(f"  Decimals: {market.quote_asset.decimals}")

    # On-chain details if available
    if market.address:
        print("\nOn-chain Details:")
        print(f"  Contract: {market.address}")
        print(f"  Base Token: {market.base_token_address}")
        print(f"  Quote Token: {market.quote_token_address}")
        print(f"  Tick Size: {market.tick_size_in_quote}")
        print(f"  Lot Size: {market.lot_size_in_base}")


async def main():
    """Run the market query examples."""
    print("GTE Market Query Example")

    # Initialize Web3 if configuration is available
    web3 = Web3(Web3.HTTPProvider(TESTNET_CONFIG.rpc_http))

    # Initialize client
    client = Client(
        web3=web3,
        config=TESTNET_CONFIG
    )

    try:
        # Run examples
        # await query_markets(client)
        market = client.get_market(to_checksum_address('0xfaf0bb6f2f4690ca4319e489f6dc742167b9fb10'))
        await query_market_details(client, market)

    except Exception as e:
        print(f"Error during examples: {str(e)}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
