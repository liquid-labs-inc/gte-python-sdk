"""Simple example demonstrating how to watch a market's orderbook using WebSocket subscription."""
import sys

from examples.utils import MARKET_ADDRESS

sys.path.append(".")
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG

import argparse
import asyncio
import logging
import os
from typing import Dict, Any
from eth_typing import ChecksumAddress

from rich.console import Console
from rich.table import Table
from web3 import AsyncWeb3

# Initialize console for rich text output
console = Console()


class OrderbookWatcher:
    """Simple class for watching and displaying a market's orderbook in real-time using WebSocket subscription."""

    def __init__(self, market_address: ChecksumAddress, depth=5):
        """
        Initialize the orderbook watcher.
        
        Args:
            market_address: Market address to watch
            depth: Number of levels to display on each side
        """
        self.market_address = market_address
        self.depth = depth
        self.orderbook_data: Dict[str, Any] | None = None
        self.last_trade = None
        self.update_count = 0

        # Initialize display table
        self.table = Table(title=f"Orderbook: {market_address}")
        self._setup_table()

        # Running state
        self.running = False

    def _setup_table(self):
        """Set up the table columns."""
        self.table.add_column("Bid Size", justify="right", style="cyan")
        self.table.add_column("Bid Price", justify="right", style="green")
        self.table.add_column("Ask Price", justify="left", style="red")
        self.table.add_column("Ask Size", justify="left", style="cyan")

    def orderbook_callback(self, data: Dict[str, Any]):
        """Callback function for orderbook updates from WebSocket."""
        if not self.running:
            return

        # Extract asks and bids, converting to (price, size) tuples as floats
        asks = [(float(entry["px"]), float(entry["sz"])) for entry in data.get("a", [])]
        bids = [(float(entry["px"]), float(entry["sz"])) for entry in data.get("b", [])]

        self.orderbook_data = {
            "asks": asks,
            "bids": bids,
            "timestamp": data.get("t"),
            "market": data.get("m"),
        }

        self.update_count += 1
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the display table with current data."""
        if not self.orderbook_data:
            return

        # Clear the console
        console.clear()
        
        # Extract orderbook data
        bids = self.orderbook_data.get('bids', [])
        asks = self.orderbook_data.get('asks', [])
        
        # Get top of book prices
        max_bid = bids[0][0] if bids else 0
        min_ask = asks[0][0] if asks else 0

        # Calculate spread
        spread = min_ask - max_bid if (min_ask > 0 and max_bid > 0) else None
        spread_percent = (spread / max_bid * 100) if spread and max_bid > 0 else None
        
        console.print(f"[bold blue]{self.market_address}[/bold blue] | "
                     f"TOB: [green]{max_bid}[/green]/[red]{min_ask}[/red] | "
                     f"Spread: {spread if spread else 'N/A'} "
                     f"({spread_percent:.2f}%)" if spread_percent else "")

        # Sort bids (highest to lowest) and asks (lowest to highest)
        sorted_bids = sorted(bids, key=lambda x: x[0], reverse=True) if bids else []
        sorted_asks = sorted(asks, key=lambda x: x[0]) if asks else []

        # Limit to specified depth
        bids_display = sorted_bids[:self.depth]
        asks_display = sorted_asks[:self.depth]

        # Re-create the table each time
        table = Table(title=f"Orderbook: {self.market_address}")
        table.add_column("Bid Size", justify="right", style="cyan")
        table.add_column("Bid Price", justify="right", style="green")
        table.add_column("Ask Price", justify="left", style="red")
        table.add_column("Ask Size", justify="left", style="cyan")
        
        # Create table rows
        max_rows = max(len(bids_display), len(asks_display))
        for i in range(max_rows):
            bid_price = bids_display[i][0] if i < len(bids_display) else ""
            bid_size = bids_display[i][1] if i < len(bids_display) else ""
            ask_price = asks_display[i][0] if i < len(asks_display) else ""
            ask_size = asks_display[i][1] if i < len(asks_display) else ""

            table.add_row(
                str(bid_size) if bid_size else "",
                str(bid_price) if bid_price else "",
                str(ask_price) if ask_price else "",
                str(ask_size) if ask_size else ""
            )

        # Display the table
        console.print(table)
        
        # Add update counter and last trade info
        console.print(f"[dim]Updates: {self.update_count}[/dim]")
        if self.last_trade:
            side = "BUY" if self.last_trade.get('taker_side', 0) == 0 else "SELL"
            price = self.last_trade.get('price', 0)
            amount = self.last_trade.get('amount', 0)
            console.print(f"[dim]Last trade: {side} {amount} @ {price}[/dim]")

    async def start(self, client: GTEClient):
        """Start watching the orderbook via WebSocket subscription."""
        self.running = True
        
        # Subscribe to orderbook updates
        await client.info.subscribe_orderbook(
            market=self.market_address,
            callback=self.orderbook_callback,
            limit=self.depth
        )
        
        console.print(f"[green]Subscribed to orderbook for {self.market_address}[/green]")


async def main():
    """Run the orderbook watcher example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GTE Orderbook Watcher (WebSocket)")
    parser.add_argument("--market", "-m", type=str, default=MARKET_ADDRESS,
                        help="Market address to watch")
    parser.add_argument("--depth", "-d", type=int, default=10,
                        help="Order book depth to display (default: 10)")
    parser.add_argument("--duration", "-t", type=int, default=60,
                        help="Duration to watch in seconds (default: 60)")
    args = parser.parse_args()

    console.print("[bold blue]GTE Orderbook Watcher (WebSocket)[/bold blue]\n")
    
    # Get market details
    market_address = AsyncWeb3.to_checksum_address(args.market)

    async with GTEClient(config=TESTNET_CONFIG) as client:
        # Create and start the watcher
        watcher = OrderbookWatcher(market_address, depth=args.depth)
        await watcher.start(client)

        # Display the orderbook live for specified duration
        console.print(f"[bold]Watching orderbook for {args.duration} seconds...[/bold]")
        console.print("[yellow]Press Ctrl+C to stop early[/yellow]\n")
        
        try:
            await asyncio.sleep(args.duration)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping early...[/yellow]")

        # Clean up - async context manager handles disconnection
        console.print("[green]Orderbook watch completed![/green]")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
