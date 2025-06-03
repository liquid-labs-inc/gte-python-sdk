#!/usr/bin/env python
"""Example of automated WebSocket subscription with GTE client."""
import sys
sys.path.append(".")
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from gte_py.api.ws import WebSocketApi
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market

from utils import (
    print_separator,
    MARKET_ADDRESS
)


# Define pretty-print handler for order book updates
async def handle_orderbook_data(raw_data: dict, parsed_data: dict):
    """Handle and display parsed orderbook data."""
    print_separator("ORDER BOOK UPDATE")
    market = parsed_data["market"]
    timestamp = parsed_data["timestamp"]
    
    print(f"Market: {market}")
    print(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    # Display top asks (ordered from lowest to highest)
    print("\nTop 5 Asks (Sell Orders):")
    print("-------------------------")
    print("Price\t\tSize\t\tCount")
    for ask in parsed_data["asks"][:5]:  # Display top 5 asks
        print(f"{ask['price']:,.2f}\t\t{ask['size']:,.6f}\t\t{ask['count']}")
    
    # Display top bids (ordered from highest to lowest)
    print("\nTop 5 Bids (Buy Orders):")
    print("------------------------")
    print("Price\t\tSize\t\tCount")
    for bid in parsed_data["bids"][:5]:  # Display top 5 bids
        print(f"{bid['price']:,.2f}\t\t{bid['size']:,.6f}\t\t{bid['count']}")
    print("\n")


# Define pretty-print handler for trade updates
async def handle_trade_data(raw_data: dict, parsed_data: dict):
    """Handle and display parsed trade data."""
    print_separator("TRADE EXECUTED")
    side = parsed_data["side"].upper()
    price = parsed_data["price"]
    size = parsed_data["size"]
    timestamp = parsed_data["timestamp"]
    trade_id = parsed_data["trade_id"]
    
    # Add color formatting based on trade side
    side_fmt = f"\033[32m{side}\033[0m" if side == "BUY" else f"\033[31m{side}\033[0m"
    
    print(f"Trade ID: {trade_id}")
    print(f"Side: {side_fmt}")
    print(f"Price: {price:,.2f}")
    print(f"Size: {size:,.6f}")
    print(f"Value: {price * size:,.2f}")
    print(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"Tx Hash: {parsed_data['tx_hash'][:10]}...")
    print("\n")


# Define pretty-print handler for candle updates
async def handle_candle_data(raw_data: dict, parsed_data: dict):
    """Handle and display parsed candle data."""
    print_separator("CANDLE UPDATE")
    interval = parsed_data["interval"]
    timestamp = parsed_data["timestamp"]
    open_price = parsed_data["open"]
    close_price = parsed_data["close"]
    high_price = parsed_data["high"]
    low_price = parsed_data["low"]
    volume = parsed_data["volume"]
    trade_count = parsed_data["trade_count"]
    
    # Calculate price change and determine if it's up or down
    price_change = close_price - open_price
    price_change_pct = (price_change / open_price) * 100 if open_price > 0 else 0
    
    # Format with color based on price movement
    if price_change > 0:
        price_fmt = f"\033[32m+{price_change:.2f} (+{price_change_pct:.2f}%)\033[0m"
    elif price_change < 0:
        price_fmt = f"\033[31m{price_change:.2f} ({price_change_pct:.2f}%)\033[0m"
    else:
        price_fmt = f"{price_change:.2f} (0.00%)"
    
    print(f"Interval: {interval}")
    print(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Open: {open_price:.2f}")
    print(f"High: {high_price:.2f}")
    print(f"Low: {low_price:.2f}")
    print(f"Close: {close_price:.2f}")
    print(f"Change: {price_fmt}")
    print(f"Volume: {volume:.6f}")
    print(f"Trades: {trade_count}")
    print("\n")


async def main():
    """Connect to the WebSocket and automatically subscribe to all available data streams."""
    # Initialize configurations and web3 connection
    network = TESTNET_CONFIG
    
    # Get market information
    market = MARKET_ADDRESS
    
    # Initialize WebSocket connection
    print("\nConnecting to WebSocket API...")
    ws_api = WebSocketApi(ws_url=network.ws_url)
    await ws_api.connect()
    
    try:
        # Subscribe to all available data streams
        print("\nSubscribing to market data streams:")
        
        # 1. Subscribe to orderbook updates
        print("- Order book updates")
        await ws_api.subscribe_orderbook(
            market=market,
            limit=10,
            callback=handle_orderbook_data
        )
        
        # 2. Subscribe to trade updates
        print("- Trade execution updates")
        await ws_api.subscribe_trades(
            market=market,
            callback=handle_trade_data
        )
        
        # 3. Subscribe to candle updates with multiple intervals
        intervals = ["1m", "5m", "15m"]
        for interval in intervals:
            print(f"- Candle updates ({interval})")
            await ws_api.subscribe_candles(
                market=market,
                interval=interval,
                callback=handle_candle_data
            )
            
        print("\nSuccessfully subscribed to all data streams!")
        print_separator("REAL-TIME MARKET DATA")
        print("Listening for market updates... Press Ctrl+C to exit.")
        
        # Keep the script running to receive and display updates
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down WebSocket connections...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up and close connections
        if ws_api:
            await ws_api.close()
        print("WebSocket connection closed.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
