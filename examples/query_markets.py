"""Example of querying a specific market from GTE."""

import asyncio

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from utils import print_separator, MARKET_ADDRESS, display_market_info


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
    market = await display_market_info(client, market_address)
    await query_market_trades(client, market_address)


if __name__ == "__main__":
    asyncio.run(main())
