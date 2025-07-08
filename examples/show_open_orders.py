"""Example of on-chain trading with the GTE client."""
import sys
sys.path.append(".")
import asyncio
import logging
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

    print(f"Market type: {market.market_type}")
    print(f"Base token: {market.base.symbol} ({market.base.address})")
    print(f"Quote token: {market.quote.symbol} ({market.quote.address})")

    return market

async def main():
    config = TESTNET_CONFIG
    
    address_to_query = to_checksum_address("0x95a1190b12f553A9c04cB36b76E3d0150E72770d")
        
    async with GTEClient(config=config) as client:
        _ = await display_market_info(client, MARKET_ADDRESS)
        open_orders = await client.info.get_user_open_orders(address_to_query, MARKET_ADDRESS)
        print("Opening orders:")
        for open_order in open_orders:
            print(
                f"Order ID: {open_order['orderId']}, Price: {open_order['limitPrice']}, Amount: {open_order['originalSize']}, Side: {open_order['side']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
