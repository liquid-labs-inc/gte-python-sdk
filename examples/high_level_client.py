"""Example of using the high-level GTE client."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pprint import pprint

from gte_py import GteClient, Trade, Candle, OrderbookUpdate


# Print helper function
def print_separator(title):
    """Print a separator with title."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def basic_client_example():
    """Demonstrate basic client functionality."""
    print_separator("Basic GTE Client Example")
    
    async with GteClient() as client:
        # Get markets
        print("Getting markets...")
        markets = await client.get_markets(limit=5)
        print(f"Found {len(markets)} markets")
        
        if not markets:
            print("No markets found!")
            return
        
        # Select first market for examples
        market = markets[0]
        print(f"Selected market: {market.pair} ({market.address})")
        
        # Get historical candles
        print("\nGetting historical candles...")
        start_time = datetime.now() - timedelta(days=1)
        candles = await client.get_candles(
            market_address=market.address,
            interval="1h",
            start_time=start_time,
            limit=24
        )
        print(f"Got {len(candles)} candles")
        if candles:
            print("Latest candle:")
            pprint(vars(candles[-1]))
        
        # Get recent trades
        print("\nGetting recent trades...")
        trades = await client.get_recent_trades(market.address, limit=5)
        print(f"Got {len(trades)} trades")
        if trades:
            print("Latest trade:")
            pprint(vars(trades[0]))


async def market_client_example():
    """Demonstrate market client functionality."""
    print_separator("Real-time Market Data Example")
    
    async with GteClient() as client:
        # Get markets
        markets = await client.get_markets(limit=5)
        if not markets:
            print("No markets found!")
            return
        
        # Select first market for examples
        market = markets[0]
        print(f"Selected market: {market.pair} ({market.address})")
        
        # Get dedicated market client
        print("\nConnecting to market websocket...")
        market_client = await client.get_market_client(market.address)
        
        # Define callback handlers
        def on_trade(trade: Trade):
            print(f"\n[TRADE] {trade.side.upper()} {trade.size} @ {trade.price}")
        
        def on_candle(candle: Candle):
            print(f"\n[CANDLE] O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close} V:{candle.volume}")
        
        def on_orderbook(update: OrderbookUpdate):
            best_bid = update.best_bid['price'] if update.best_bid else "N/A"
            best_ask = update.best_ask['price'] if update.best_ask else "N/A"
            print(f"\n[ORDERBOOK] Bid: {best_bid} | Ask: {best_ask} | Spread: {update.spread}")
        
        # Subscribe to all data types
        await market_client.subscribe_all(
            trade_callback=on_trade,
            candle_callback=on_candle,
            orderbook_callback=on_orderbook,
            candle_interval="1m"
        )
        
        print("\nListening for real-time updates for 30 seconds...")
        print("(Note: You may not see all event types if market is not active)")
        
        # Wait and listen for events
        for i in range(30):
            await asyncio.sleep(1)
            # Print a periodic marker if no events
            if i % 5 == 0 and i > 0:
                print(".", end="", flush=True)
        
        # Clean up
        print("\n\nClosing market client...")
        await market_client.close()


async def main():
    """Run example functions."""
    try:
        await basic_client_example()
        await market_client_example()
    except Exception as e:
        print(f"Error during examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
