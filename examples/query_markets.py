"""Example of querying a specific market from GTE."""
import sys
sys.path.append(".")
import asyncio

from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market


MARKET_ADDRESS = to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")

async def display_market_info(client: GTEClient, market_address: ChecksumAddress) -> Market:
    """Get and display market information."""

    print(f"Using market: {market_address}")
    market = await client.info.get_market(market_address)

    print(f"Market type: {market['market_type']}")
    print(f"Base token: {market['base']['symbol']} ({market['base']['address']})")
    print(f"Quote token: {market['quote']['symbol']} ({market['quote']['address']})")

    return market

async def query_market_trades(client: GTEClient, market_address: ChecksumAddress) -> None:
    """Query trades for a specific market."""
    print("Market Trades Query")

    # Get trades for the market
    trades = await client.info.get_trades(market_address)

    # Display trade information
    print(f"Trades for market {market_address}:")
    for trade in trades:
        print('-' * 75)
        print(f"  Txn: {trade['tx_hash'].to_0x_hex()}")
        print(f"  Price: {trade['price']}")
        print(f"  Size: {trade['size']}")
        print(f"  Side: {trade['side']}")
        print(f"  Timestamp: {trade['timestamp']}")
    print('-' * 75)


async def main() -> None:
    """Run the market query example."""
    print("GTE Market Query Example")

    # Initialize client
    async with GTEClient(config=TESTNET_CONFIG) as client:
        
        market_address = MARKET_ADDRESS
        _ = await display_market_info(client, market_address)
        await query_market_trades(client, market_address)


if __name__ == "__main__":
    asyncio.run(main())
