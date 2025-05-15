"""Simple example demonstrating how to watch a market's orderbook using WebSocket ETH RPC."""
from dotenv import load_dotenv

from gte_py.api.chain.clob import ICLOB
from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client, OrderbookClient
from gte_py.configs import TESTNET_CONFIG

load_dotenv()
import argparse
import asyncio
import logging
import os
import time

from rich.console import Console
from rich.table import Table
from web3 import AsyncWeb3

from gte_py.models import OrderBookSnapshot

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

        # Also initialize MarketClient for REST API access
        self.market_address = clob.address
        self.orderbook_client: OrderbookClient | None = None  # Will be set in start() method
        self.streamer = None
        self.depth = depth
        self.poll_interval = poll_interval
        self.ob: OrderBookSnapshot | None = None

        self.last_trade = None

        # Get market symbol information
        self.base_token = None
        self.quote_token = None
        self.market_symbol = None
        # Initialize display table
        self.table = Table(title=f"Orderbook: {self.market_symbol}")
        self._setup_table()

        # Running state
        self.running = False
        self.task = None

    async def init(self):
        self.base_token = await self.clob.get_base_token()
        self.quote_token = await self.clob.get_quote_token()
        self.market_symbol = f"{self.base_token[-4:]}_{self.quote_token[-4:]}"

    def _setup_table(self):
        """Set up the table columns."""
        self.table.add_column("Bid Size", justify="right", style="cyan")
        self.table.add_column("Bid Price", justify="right", style="green")
        self.table.add_column("Ask Price", justify="left", style="red")
        self.table.add_column("Ask Size", justify="left", style="cyan")

    def update_book(self, snapshot: OrderBookSnapshot):
        """Update orderbook data from a snapshot."""
        self.ob = snapshot
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
        tob = asyncio.run(self.clob.get_tob())
        max_bid, min_ask = tob

        # Update title with market info
        spread = min_ask - max_bid if (min_ask > 0 and max_bid > 0) else None
        print(
            f"{self.market_symbol} | "
            f"TOB: {max_bid}/{min_ask} | "
            f"Spread: {spread if spread else 'N/A'} | "
            f"Last update: {time.strftime('%H:%M:%S')}"
        )

        # Sort bids (highest to lowest) and asks (lowest to highest)
        sorted_bids = sorted(self.ob.bids, key=lambda x: x[0], reverse=True) if self.ob.bids else []
        sorted_asks = sorted(self.ob.asks, key=lambda x: x[0]) if self.ob.asks else []

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

            print(str(bid_size), str(bid_price), str(ask_price), str(ask_size))

        # Add last trade info as a footer
        if self.last_trade:
            side = "BUY" if self.last_trade.get('taker_side', 0) == 0 else "SELL"
            price = self.last_trade.get('price', 0)
            amount = self.last_trade.get('amount', 0)
            print(f"Last trade: {side} {amount} @ {price}")

    async def start(self, client: Client | None = None):
        """Start watching the orderbook."""
        await self.init()
        self.running = True
        market = await client.info.get_market(self.market_address)
        self.orderbook_client = client.orderbook
        # Initialize MarketClient if we have a client
        async def refresh_snapshot():
            while self.running:
                snapshot = await self.orderbook_client.get_order_book_snapshot(market, self.depth)
                self.update_book(snapshot)
                await asyncio.sleep(self.poll_interval)

        asyncio.create_task(refresh_snapshot())

    async def stop(self):
        """Stop watching the orderbook."""
        self.running = False
        if self.orderbook_client:
            await self.orderbook_client.close()


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
    web3 = await make_web3(TESTNET_CONFIG)

    # Initialize GTE client for market info
    client = Client(web3=web3, config=TESTNET_CONFIG)

    # Get market details
    market_address = AsyncWeb3.to_checksum_address(args.market)

    # Initialize ICLOB contract
    clob = client.clob.get_clob(market_address)

    # Create and start the watcher
    watcher = OrderbookWatcher(clob, depth=args.depth)
    await watcher.start(client)  # Pass client for REST API access

    # Display the orderbook live for specified duration
    console.print(f"[bold]Watching orderbook for {args.duration} seconds...[/bold]")
    await asyncio.sleep(args.duration)

    # Clean up
    await watcher.stop()
    console.print("[green]Orderbook watch completed![/green]")

    # Close client
    await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
