"""Example of querying market information."""
import sys
sys.path.append(".")
import asyncio
from decimal import Decimal

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.constants import BTC_USD_CLOB

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config) as client:
        
        # Get all available markets
        all_markets = await client.info.get_all_markets()
        print("All available markets:")
        for market in all_markets:
            print(f"  {market.base.symbol}/{market.quote.symbol} - {market.address}")
        
        print("\n" + "="*50)
        
        # Get specific market information
        market = await client.info.get_market(BTC_USD_CLOB)
        print(f"Market: {market.base.symbol}/{market.quote.symbol}")
        print(f"Address: {market.address}")
        print(f"Market Type: {market.market_type}")
        print(f"Base Token: {market.base.symbol} ({market.base.address})")
        print(f"Quote Token: {market.quote.symbol} ({market.quote.address})")
        
        # Get orderbook
        orderbook = await client.info.get_orderbook(BTC_USD_CLOB)
        print(f"\nOrderbook:")
        print(f"Best bid: {orderbook.bids[0] if orderbook.bids else 'None'}")
        print(f"Best ask: {orderbook.asks[0] if orderbook.asks else 'None'}")
        
        # Get recent trades
        trades = await client.info.get_trades(BTC_USD_CLOB)
        print(f"\nRecent trades ({len(trades)} trades):")
        for trade in trades[:5]:  # Show first 5 trades
            print(f"  Price: {trade.price}, Size: {trade.size}, Side: {trade.side}")
        
        # Get market stats/ticker
        ticker = await client.info.get_market(BTC_USD_CLOB)
        print(f"\nMarket Stats:")
        print(f"  24h Volume: {ticker.get('volume24HrUsd', 'N/A')}")
        print(f"  24h Change: {ticker.get('priceChange24Hr', 'N/A')}")
        print(f"  Last Price: {ticker.get('priceUsd', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
