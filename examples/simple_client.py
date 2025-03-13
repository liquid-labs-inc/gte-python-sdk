"""Example of using the GTE API client."""

import asyncio
import json
from gte_py.raw import GTERestClient, GTEWebSocketClient


async def rest_example():
    """Example of using the REST API client."""
    async with GTERestClient() as client:
        # Get API health status
        health = await client.get_health()
        print("API Health:")
        print(json.dumps(health, indent=2))
        print()

        # Get list of markets
        markets = await client.get_markets(limit=5)
        print("Markets:")
        print(json.dumps(markets, indent=2))
        print()


async def websocket_example():
    """Example of using the WebSocket client."""
    # This is a placeholder - you'll need actual market addresses
    market_addresses = ["0x1234567890abcdef1234567890abcdef12345678"]
    
    ws_client = GTEWebSocketClient()
    
    async def handle_trade(data):
        print("Trade received:")
        print(json.dumps(data, indent=2))
    
    await ws_client.connect()
    
    # Subscribe to trades
    await ws_client.subscribe_trades(market_addresses, handle_trade)
    
    # Keep the connection open for 30 seconds
    try:
        print("Watching trades for 30 seconds...")
        await asyncio.sleep(30)
    finally:
        # Unsubscribe and close connection
        await ws_client.unsubscribe_trades(market_addresses)
        await ws_client.close()


async def main():
    """Run the examples."""
    print("REST API Example")
    print("===============")
    await rest_example()
    
    print("\nWebSocket Example")
    print("================")
    await websocket_example()


if __name__ == "__main__":
    asyncio.run(main())
