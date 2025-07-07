"""Example of subscribing to trades on a market."""
import sys
sys.path.append(".")
import asyncio
from typing import Any
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG

# BTC/USD market address
MARKET_ADDRESS = to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")


async def handle_trade_data(raw_data: dict[str, Any]):
    """Handle trade data."""
    print(raw_data)
    

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config) as client:

        # Subscribe to trades
        await client.info.subscribe_trades(MARKET_ADDRESS, handle_trade_data)

        # Wait for 30 seconds
        await asyncio.sleep(30)

    # Context manager will close the connection
    print("Connection closed")
    

if __name__ == "__main__":
    asyncio.run(main())
