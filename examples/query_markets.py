"""Example of querying all available markets from GTE."""

import asyncio
import os
from datetime import datetime
from web3 import Web3
from dotenv import load_dotenv
from tabulate import tabulate  # pip install tabulate
from typing import List, Optional

from gte_py import Client
from gte_py.models import Market, MarketInfo, MarketType


# Load environment variables from .env file
load_dotenv()

# Configure these variables through environment or directly
RPC_URL = os.getenv("RPC_URL", "https://rpc-testnet.example.com")
ROUTER_ADDRESS = os.getenv("ROUTER_ADDRESS")


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    return f"{price:.8f}"


def format_market_table(markets: List[Market], title: str):
    """Format and print a table of markets."""
    print_separator(title)
    
    if not markets:
        print("No markets found!")
        return
    
    # Prepare table rows
    rows = []
    for i, market in enumerate(markets, 1):
        rows.append([
            i,
            market.pair,
            market.address[:10] + "...",
            market.market_type.value if hasattr(market, 'market_type') else "N/A",
            format_price(market.price),
            f"{market.volume_24h:.2f}" if market.volume_24h else "N/A",
            "Yes" if market.contract_address else "No"
        ])
    
    # Print table
    headers = ["#", "Pair", "Address", "Type", "Price", "24h Volume", "On-chain"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"Total: {len(markets)} markets")


def format_chain_market_table(markets: List[MarketInfo], title: str):
    """Format and print a table of on-chain markets."""
    print_separator(title)
    
    if not markets:
        print("No on-chain markets found!")
        return
    
    # Prepare table rows
    rows = []
    for i, market in enumerate(markets, 1):
        rows.append([
            i,
            f"{market.contract_address[:10]}...",
            f"{market.base_token[:10]}...",
            f"{market.quote_token[:10]}...",
            market.base_decimals,
            market.quote_decimals,
            market.tick_size
        ])
    
    # Print table
    headers = ["#", "Contract", "Base Token", "Quote Token", "Base Dec", "Quote Dec", "Tick Size"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print(f"Total: {len(markets)} on-chain markets")


async def query_api_markets(client: Client):
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
    onchain_markets = [m for m in markets if m.contract_address]
    format_market_table(onchain_markets, "Markets with On-chain Contracts")
    
    # Demonstrate pagination
    print_separator("Pagination Example")
    page_size = 20
    for i in range(3):  # Get 3 pages
        offset = i * page_size
        page = await client.get_markets(limit=page_size, offset=offset)
        print(f"Page {i+1}: Retrieved {len(page)} markets (offset: {offset})")
        if not page:
            break


async def query_onchain_markets(client: Client):
    """Query markets directly from the blockchain."""
    try:
        if not hasattr(client, 'get_available_onchain_markets') or client._web3 is None:
            print("Web3 provider not configured. Skipping on-chain market queries.")
            return
            
        print("\nFetching markets directly from blockchain...")
        onchain_markets = client.get_available_onchain_markets()
        format_chain_market_table(onchain_markets, "On-chain Markets")
        
        # Get market details
        if onchain_markets:
            market = onchain_markets[0]
            print_separator(f"Details for Market {market.contract_address[:10]}...")
            print(f"Contract: {market.contract_address}")
            print(f"Base Token: {market.base_token}")
            print(f"Quote Token: {market.quote_token}")
            print(f"Base Decimals: {market.base_decimals}")
            print(f"Quote Decimals: {market.quote_decimals}")
            print(f"Tick Size: {market.tick_size}")
            print(f"Base Atoms Per Lot: {market.base_atoms_per_lot}")
    except Exception as e:
        print(f"Error fetching on-chain markets: {str(e)}")


async def query_market_details(client: Client):
    """Query detailed information for a specific market."""
    print_separator("Market Details Example")
    
    # Get all markets
    markets = await client.get_markets(limit=100)
    
    # Select a market to examine
    if not markets:
        print("No markets found!")
        return
        
    selected_market = markets[0]  # Use the first market
    
    # Get detailed information
    market = await client.get_market(selected_market.address)
    
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
    if market.contract_address:
        print("\nOn-chain Details:")
        print(f"  Contract: {market.contract_address}")
        print(f"  Base Token: {market.base_token_address}")
        print(f"  Quote Token: {market.quote_token_address}")
        print(f"  Tick Size: {market.tick_size}")
        print(f"  Base Atoms Per Lot: {market.base_atoms_per_lot}")


async def main():
    """Run the market query examples."""
    print("GTE Market Query Example")
    
    # Initialize Web3 if configuration is available
    web3 = None
    if RPC_URL and RPC_URL != "https://rpc-testnet.example.com":
        try:
            web3 = Web3(Web3.HTTPProvider(RPC_URL))
            print(f"Web3 Connected: {web3.is_connected()}")
        except Exception as e:
            print(f"Couldn't initialize Web3: {e}")
    
    # Initialize client
    client = Client(
        web3_provider=web3,
        router_address=ROUTER_ADDRESS if web3 and web3.is_connected() else None
    )
    
    try:
        # Run examples
        await query_api_markets(client)
        await query_onchain_markets(client)
        await query_market_details(client)
    
    except Exception as e:
        print(f"Error during examples: {str(e)}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
