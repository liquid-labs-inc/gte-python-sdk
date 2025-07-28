"""Example of subscribing to trades on a market."""
import sys
sys.path.append(".")
import asyncio
from typing import Any

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG

from examples.constants import BTC_USD_CLOB

# BTC/USD market address
MARKET_ADDRESS = BTC_USD_CLOB


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
