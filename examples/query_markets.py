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

    return market


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


if __name__ == "__main__":
    asyncio.run(main())
