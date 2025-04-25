"""Simple example demonstrating how to watch a market's orderbook using WebSocket ETH RPC."""
from dotenv import load_dotenv

load_dotenv()
import argparse
import asyncio
import logging
import os
import time

from rich.console import Console
from rich.live import Live
from rich.table import Table
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.contracts.iclob import ICLOB
from gte_py.contracts.iclob_streaming import CLOBEventStreamer

# Initialize console for rich text output
console = Console()

# Default market address - replace with your market of interest
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS", "0xfaf0BB6F2f4690CA4319e489F6Dc742167B9fB10")  # MEOW/WETH


class OrderbookWatcher:
    """Simple class for watching and displaying a market's orderbook in real-time."""

    def __init__(self, clob: ICLOB, depth=5, poll_interval=0.5):
        """
        Initialize the orderbook watcher.
        
        Args:
            clob: ICLOB instance
            depth: Number of levels to display on each side
            poll_interval: How often to update the order book in seconds
        """
        # Initialize CLOB contract and streamer
        self.clob = clob
        self.streamer = CLOBEventStreamer(clob, poll_interval=poll_interval)

        self.depth = depth
        self.poll_interval = poll_interval
        self.bids = []
        self.asks = []
        self.last_trade = None

        # Get market symbol information
        self.base_token = self.clob.get_base_token()
        self.quote_token = self.clob.get_quote_token()
        self.market_symbol = f"{self.base_token[-4:]}_{self.quote_token[-4:]}"

        # Initialize display table
        self.table = Table(title=f"Orderbook: {self.market_symbol}")
        self._setup_table()

        # Running state
        self.running = False
        self.task = None

    def _setup_table(self):
        """Set up the table columns."""
        self.table.add_column("Bid Size", justify="right", style="cyan")
        self.table.add_column("Bid Price", justify="right", style="green")
        self.table.add_column("Ask Price", justify="left", style="red")
        self.table.add_column("Ask Size", justify="left", style="cyan")

    def update_book(self, snapshot):
        """Update orderbook data from a snapshot."""
        self.bids = snapshot['bids']
        self.asks = snapshot['asks']
        self._refresh_table()

    def update_trade(self, trade):
        """Update last trade info."""
        self.last_trade = trade
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the display table with current data."""
        # Clear existing rows
        self.table.rows = []

        # Get top of book prices
        tob = self.clob.get_tob()
        max_bid, min_ask = tob

        # Update title with market info
        spread = min_ask - max_bid if (min_ask > 0 and max_bid > 0) else None
        self.table.title = (
            f"{self.market_symbol} | "
            f"TOB: {max_bid}/{min_ask} | "
            f"Spread: {spread if spread else 'N/A'} | "
            f"Last update: {time.strftime('%H:%M:%S')}"
        )

        # Sort bids (highest to lowest) and asks (lowest to highest)
        sorted_bids = sorted(self.bids, key=lambda x: x[0], reverse=True) if self.bids else []
        sorted_asks = sorted(self.asks, key=lambda x: x[0]) if self.asks else []

        # Limit to specified depth
        bids = sorted_bids[:self.depth]
        asks = sorted_asks[:self.depth]

        # Pad with empty rows if needed
        max_rows = max(len(bids), len(asks))
        for i in range(max_rows):
            bid_price = bids[i][0] if i < len(bids) else ""
            bid_size = bids[i][1] if i < len(bids) else ""
            ask_price = asks[i][0] if i < len(asks) else ""
            ask_size = asks[i][1] if i < len(asks) else ""

            self.table.add_row(str(bid_size), str(bid_price), str(ask_price), str(ask_size))

        # Add last trade info as a footer
        if self.last_trade:
            side = "BUY" if self.last_trade.get('taker_side', 0) == 0 else "SELL"
            price = self.last_trade.get('price', 0)
            amount = self.last_trade.get('amount', 0)
            self.table.caption = f"Last trade: {side} {amount} @ {price}"

    def start(self):
        """Start watching the orderbook."""
        self.running = True

        # Register callbacks for different data types
        self.streamer.on_orderbook(self.update_book)
        self.streamer.on_trades(self.update_trade)

        # Initial data fetch
        book = self.streamer.get_order_book_snapshot(self.depth)
        self.update_book(book)

        # Start streams in background
        self.streamer.stream_order_book(depth=self.depth)
        self.streamer.stream_trades()

    def stop(self):
        """Stop watching the orderbook."""
        self.running = False


async def main():
    """Run the orderbook watcher example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GTE Orderbook Watcher")
    parser.add_argument("--market", "-m", type=str, default=MARKET_ADDRESS,
                        help="Market address to watch")
    parser.add_argument("--depth", "-d", type=int, default=10,
                        help="Order book depth to display (default: 10)")
    parser.add_argument("--duration", "-t", type=int, default=60,
                        help="Duration to watch in seconds (default: 60)")
    parser.add_argument("--use-http", action="store_true",
                        help="Use HTTP provider instead of WebSocket")
    args = parser.parse_args()

    console.print("[bold blue]GTE Orderbook Watcher[/bold blue]\n")

    # Connect to Ethereum node
    if args.use_http or True:
        console.print(f"Connecting to MegaETH Testnet via HTTP: {TESTNET_CONFIG.rpc_http}")
        web3 = Web3(Web3.HTTPProvider(TESTNET_CONFIG.rpc_http))
    else:
        console.print(f"Connecting to MegaETH Testnet via WebSocket: {TESTNET_CONFIG.rpc_ws}")
        web3 = Web3(Web3.LegacyWebSocketProvider(TESTNET_CONFIG.rpc_ws))

    if not web3.is_connected():
        console.print("[red]Failed to connect to Ethereum node![/red]")
        return


    # Initialize GTE client for market info
    client = Client(web3=web3, config=TESTNET_CONFIG)

    # Get market details
    market_address = Web3.to_checksum_address(args.market)

    # Initialize ICLOB contract
    clob = ICLOB(web3, market_address)

    # Create and start the watcher
    watcher = OrderbookWatcher(clob, depth=args.depth)
    watcher.start()

    # Display the orderbook live for specified duration
    console.print(f"[bold]Watching orderbook for {args.duration} seconds...[/bold]")
    with Live(watcher.table, refresh_per_second=2):
        time.sleep(args.duration)

    # Clean up
    watcher.stop()
    console.print("[green]Orderbook watch completed![/green]")

    # Close client
    await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
