"""Example of querying a specific market from GTE."""

import asyncio
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.models import Market

from utils import print_separator, format_price, MARKET_ADDRESS


async def query_specific_market(client: Client, market_address: str):
    """Query a specific market by address."""
    print_separator("Specific Market Query")

    # Get a specific market by address
    print(f"Fetching market with address: {market_address}")
    market = client.get_market(market_address)

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


async def query_market_orderbook(client: Client, market: Market):
    """Query the orderbook for a market."""
    print_separator("Market Orderbook")

    try:
        # Get orderbook for the market
        orderbook = await client.get_orderbook(market)
        
        # Display bids
        print("Bids:")
        if not orderbook.bids:
            print("  No bids found")
        else:
            for i, bid in enumerate(orderbook.bids[:5], 1):  # Display top 5 bids
                print(f"  {i}. Price: {bid.price}, Amount: {bid.amount}")
        
        # Display asks
        print("\nAsks:")
        if not orderbook.asks:
            print("  No asks found")
        else:
            for i, ask in enumerate(orderbook.asks[:5], 1):  # Display top 5 asks
                print(f"  {i}. Price: {ask.price}, Amount: {ask.amount}")
                
        # Display the spread
        if orderbook.bids and orderbook.asks:
            spread = orderbook.asks[0].price - orderbook.bids[0].price
            spread_percentage = (spread / orderbook.bids[0].price) * 100
            print(f"\nSpread: {spread:.8f} ({spread_percentage:.2f}%)")
            
    except Exception as e:
        print(f"Error fetching orderbook: {str(e)}")


async def query_market_trades(client: Client, market: Market):
    """Query recent trades for a market."""
    print_separator("Recent Trades")

    try:
        # Get recent trades for the market
        trades = await client.get_trades(market, limit=5)
        
        if not trades:
            print("No recent trades found")
            return
            
        print(f"Recent trades for {market.pair}:")
        for i, trade in enumerate(trades, 1):
            side = "BUY" if trade.is_buy else "SELL"
            timestamp = trade.timestamp if hasattr(trade, "timestamp") else "N/A"
            print(f"  {i}. Side: {side}, Price: {trade.price}, Amount: {trade.amount}, Time: {timestamp}")
            
    except Exception as e:
        print(f"Error fetching trades: {str(e)}")


async def main():
    """Run the market query example."""
    print("GTE Market Query Example")

    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(TESTNET_CONFIG.rpc_http))

    # Initialize client
    client = Client(
        web3=web3,
        config=TESTNET_CONFIG
    )

    try:
        # Query a specific market
        market_address = MARKET_ADDRESS
        market = await query_specific_market(client, market_address)
        
        # Query orderbook
        await query_market_orderbook(client, market)
        
        # Query trades
        await query_market_trades(client, market)

    except Exception as e:
        print(f"Error during query: {str(e)}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
