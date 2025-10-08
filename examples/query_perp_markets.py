"""Example of querying market information."""
import logging
import sys
sys.path.append(".")
import asyncio
from decimal import Decimal

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.constants import BTC_USD_CLOB, FAKEBTCUSD


async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config) as client:
        
        # Get all available markets
        all_markets = await client.info.get_perp_markets()
        print("All available markets: ", all_markets)
        for market in all_markets:
            print(market)
            market_details = await client.info.get_perp_market_by_id(market)
            print(market_details)

        print("\n" + "="*50)

        # FIXME: Get specific market information
        # book = await client.info.get_perp_book(FAKEBTCUSD)
        # print(book)

        # Get recent trades: no trades so far
        trades = await client.info.get_perp_trades(FAKEBTCUSD)
        print(f"\nRecent trades ({len(trades)} trades):")
        for trade in trades[:5]:  # Show first 5 trades
            print(f"  Price: {trade.price}, Size: {trade.size}, Side: {trade.side}")

        await client.execution.perp_deposit(Decimal("1.0"))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
