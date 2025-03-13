"""Example of using the trading functionality of the GTE client."""

import asyncio
import json
from datetime import datetime, timedelta
from pprint import pprint

from gte_py import GteClient


async def trading_example():
    """Demonstrate trading functionality."""
    print("\n" + "=" * 50)
    print("GTE Trading Example")
    print("=" * 50)
    
    async with GteClient() as client:
        # Get markets
        print("Getting markets...")
        markets = await client.get_markets(limit=1)
        
        if not markets:
            print("No markets found!")
            return
        
        # Select first market for examples
        market = markets[0]
        print(f"Selected market: {market.pair} ({market.address})")
        
        # Get current price
        market_client = await client.get_market_client(market.address)
        await asyncio.sleep(2)  # Wait to receive some data
        
        # Get market data
        current_price = market.price or 100  # Fallback price if none available
        print(f"Current price: {current_price}")
        
        # Calculate order prices
        buy_price = current_price * 0.95  # 5% below current price
        sell_price = current_price * 1.05  # 5% above current price
        
        # Create limit orders (these are simulations)
        print("\nCreating limit orders...")
        
        buy_order = await client.buy_limit(
            market_address=market.address,
            amount=1.0,
            price=buy_price
        )
        print(f"Created buy limit order: {buy_order.amount} @ {buy_order.price}")
        
        sell_order = await client.sell_limit(
            market_address=market.address,
            amount=0.5,
            price=sell_price
        )
        print(f"Created sell limit order: {sell_order.amount} @ {sell_order.price}")
        
        # Cancel one of the orders
        print("\nCancelling buy order...")
        cancelled = await client.cancel_order(buy_order.id)
        print(f"Cancellation{'successful' if cancelled else 'failed'}")
        
        # Add liquidity example
        print("\nAdding liquidity...")
        liquidity_result = await client.add_liquidity(
            market_address=market.address,
            token0_amount=1.0,
            token1_amount=current_price * 1.0  # Match based on price
        )
        print(f"Liquidity addition: {liquidity_result['success']}")
        
        # Close the market client
        await market_client.close()


if __name__ == "__main__":
    asyncio.run(trading_example())
