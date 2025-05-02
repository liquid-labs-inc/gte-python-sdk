"""Example of querying a specific market from GTE."""

import asyncio

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

import gte_py.models
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from utils import print_separator, format_price, MARKET_ADDRESS


async def query_specific_market(client: Client, market_address: ChecksumAddress) -> gte_py.models.Market:
    """Query a specific market by address."""
    print_separator("Specific Market Query")

    # Get a specific market by address
    print(f"Fetching market with address: {market_address}")
    market = await client.info.get_market(market_address)

    # Display market information
    print(f"Market: {market.pair} ({market.address})")
    if hasattr(market, 'market_type'):
        print(f"Type: {market.market_type.value}")
    print(f"Price: {format_price(market.price)}")
    print(f"24h Volume: {market.volume_24h if market.volume_24h else 'N/A'}")

    # Base asset details
    print("\nBase Asset:")
    print(f"  Symbol: {market.base.symbol}")
    print(f"  Address: {market.base.address}")
    print(f"  Decimals: {market.base.decimals}")

    # Quote asset details
    print("\nQuote Asset:")
    print(f"  Symbol: {market.quote.symbol}")
    print(f"  Address: {market.quote.address}")
    print(f"  Decimals: {market.quote.decimals}")

    # On-chain details if available
    if market.address:
        print("\nOn-chain Details:")
        print(f"  Contract: {market.address}")
        print(f"  Base Token: {market.base.address}")
        print(f"  Quote Token: {market.quote.address}")
        print(f"  Tick Size: {market.tick_size}")
        print(f"  Lot Size: {market.lot_size}")

    return market


async def query_market_trades(client: Client, market_address: ChecksumAddress) -> None:
    """Query trades for a specific market."""
    print_separator("Market Trades Query")

    # Get trades for the market
    trades = await client.trades.get_trades(market_address)

    # Display trade information
    print(f"Trades for market {market_address}:")
    for trade in trades:
        print(f"  Trade ID: {trade.id}")
        print(f"  Price: {trade.price}")
        print(f"  Amount: {trade.amount}")
        print(f"  Side: {trade.side.value}")
        print(f"  Timestamp: {trade.timestamp}")


async def main() -> None:
    """Run the market query example."""
    print("GTE Market Query Example")

    # Initialize AsyncWeb3
    web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(TESTNET_CONFIG.rpc_http))

    # Initialize client
    client = Client(
        web3=web3,
        config=TESTNET_CONFIG
    )

    market_address = MARKET_ADDRESS
    market = await query_specific_market(client, market_address)
    # await query_market_trades(client, market_address)


if __name__ == "__main__":
    asyncio.run(main())
