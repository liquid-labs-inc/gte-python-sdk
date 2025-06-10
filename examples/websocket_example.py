#!/usr/bin/env python
"""Example of automated WebSocket subscription with GTE client."""
import sys
sys.path.append(".")
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from gte_py.api.ws import WebSocketApi, CandleData, TradeData, OrderBookData
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market

from utils import (
    print_separator,
    MARKET_ADDRESS
)


# Define pretty-print handler for order book updates
async def handle_orderbook_data(raw_data: OrderBookData):
    """Handle and display parsed orderbook data."""
    print_separator("ORDER BOOK UPDATE")
    market = raw_data['m']
    timestamp = datetime.fromtimestamp(raw_data['t'] / 1000)  # Convert milliseconds to seconds
    
    print(f"Market: {market}")
    print(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    # Display top asks (ordered from lowest to highest)
    print("\nTop 5 Asks (Sell Orders):")
    print("-------------------------")
    print("Price\t\tSize\t\tCount")
    for ask in raw_data["a"][:5]:  # Display top 5 asks
        print(f"{ask['px']}\t\t{ask['sz']}\t\t{ask['n']}")
    
    # Display top bids (ordered from highest to lowest)
    print("\nTop 5 Bids (Buy Orders):")
    print("------------------------")
    print("Price\t\tSize\t\tCount")
    for bid in raw_data["b"][:5]:
        print(f"{bid['px']}\t\t{bid['sz']}\t\t{bid['n']}")
    print("\n")


# Define pretty-print handler for trade updates
async def handle_trade_data(raw_data: TradeData):
    """Handle and display parsed trade data."""
    print_separator("TRADE EXECUTED")
    side = raw_data["sd"].upper()
    price = float(raw_data["px"])
    size = float(raw_data["sz"])
    timestamp = datetime.fromtimestamp(raw_data["t"] // 1000)
    trade_id = raw_data["id"]
    tx_hash = raw_data['h']
    
    # Add color formatting based on trade side
    side_fmt = f"\033[32m{side}\033[0m" if side == "BUY" else f"\033[31m{side}\033[0m"
    
    print(f"Market: {raw_data['m']}")
    print(f"Trade ID: {trade_id}")
    print(f"Side: {side_fmt}")
    print(f"Price: {price:,.2f}")
    print(f"Size: {size:,.6f}")
    print(f"Value: {price * size:,.2f}")
    print(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print("\n")


# Define pretty-print handler for candle updates
async def handle_candle_data(raw_data: CandleData):
    """Handle and display parsed candle data."""
    print_separator("CANDLE UPDATE")
    interval = raw_data["i"]
    timestamp = datetime.fromtimestamp(raw_data["t"] // 1000)
    open_price = float(raw_data["o"])
    close_price = float(raw_data["c"])
    high_price = float(raw_data["h"])
    low_price = float(raw_data["l"])
    volume = float(raw_data["v"])
    trade_count = raw_data["n"]
    
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
