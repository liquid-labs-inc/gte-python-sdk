"""Example demonstrating how to watch a market's orderbook in real-time."""

import asyncio

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.table import Table

from gte_py import Client
from gte_py.models import OrderbookUpdate

# Load environment variables from .env file
load_dotenv()

# Initialize rich console
console = Console()


class OrderbookWatcher:
    """Class for watching and displaying a market's orderbook in real-time."""

    def __init__(self, market, depth=5, refresh_rate=0.5):
        """
        Initialize the orderbook watcher.

        Args:
            market: Market object
            depth: Number of levels to display on each side
            refresh_rate: How often to refresh the display (in seconds)
        """
        self.market = market
        self.depth = depth
        self.refresh_rate = refresh_rate
        self.last_update = None
        self.bids = []
        self.asks = []
        self.update_count = 0
        self.table = Table(title=f"Orderbook: {market.pair}")
        self._setup_table()

    def _setup_table(self):
        """Set up the table structure."""
        self.table.add_column("Quantity", justify="right", style="cyan", no_wrap=True)
        self.table.add_column("Bid Price", justify="right", style="green", no_wrap=True)
        self.table.add_column("Ask Price", justify="right", style="red", no_wrap=True)
        self.table.add_column("Quantity", justify="left", style="cyan", no_wrap=True)

    def update(self, orderbook: OrderbookUpdate):
        """
        Process an orderbook update.

        Args:
            orderbook: The orderbook update
        """
        self.last_update = orderbook
        self.bids = orderbook.bids
        self.asks = orderbook.asks
        self.update_count += 1
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the display table with current orderbook data."""
        # Clear existing rows
        self.table.rows = []

        # Get spread and mid price
        spread = self.last_update.spread if self.last_update else None
        mid_price = self.last_update.mid_price if self.last_update else None

        # Update table title with market info
        timestamp = self.last_update.datetime.strftime("%H:%M:%S") if self.last_update else "N/A"
        self.table.title = (
            f"{self.market.pair} Orderbook | "
            f"Updates: {self.update_count} | "
            f"Last: {timestamp} | "
            f"Spread: {spread:.8f if spread else 'N/A'} | "
            f"Mid: {mid_price:.8f if mid_price else 'N/A'}"
        )

        # Sort bids (highest to lowest) and asks (lowest to highest)
        sorted_bids = sorted(self.bids, key=lambda x: x.price, reverse=True) if self.bids else []
        sorted_asks = sorted(self.asks, key=lambda x: x.price) if self.asks else []

        # Limit to specified depth
        bids = sorted_bids[: self.depth]
        asks = sorted_asks[: self.depth]

        # Pad with empty rows if needed
        while len(bids) < self.depth:
            bids.append(None)
        while len(asks) < self.depth:
            asks.append(None)

        # Add rows to table
        for i in range(self.depth):
            bid = bids[i]
            ask = asks[i]

            bid_size = f"{bid.size:.6f}" if bid else ""
            bid_price = f"{bid.price:.8f}" if bid else ""
            ask_price = f"{ask.price:.8f}" if ask else ""
            ask_size = f"{ask.size:.6f}" if ask else ""

            # Add colored row based on price change
            self.table.add_row(bid_size, bid_price, ask_price, ask_size)

    def generate_table(self):
        """
        Generate the table for display.

        Returns:
            Rich table object
        """
        return self.table


async def watch_orderbook(client, market_address, depth=5, duration=60):
    """
    Watch a market's orderbook in real-time.

    Args:
        client: GTE client instance
        market_address: Market address to watch
        depth: Number of levels to display on each side
        duration: How long to watch (in seconds)
    """
    # Get market details
    market = await client.get_market(market_address)
    console.print(f"[bold]Watching orderbook for {market.pair}[/bold]")

    # Create market client
    market_client = await client.get_market_client(market.address)

    # Create orderbook watcher
    watcher = OrderbookWatcher(market, depth=depth)

    # Set up the live display
    with Live(watcher.generate_table(), refresh_per_second=4):
        # Subscribe to orderbook updates
        await market_client.subscribe_orderbook(callback=watcher.update)

        # Keep watching for specified duration
        for i in range(duration):
            await asyncio.sleep(1)

            # Print a message every 10 seconds
            if i > 0 and i % 10 == 0:
                print(f"Watching orderbook... {i}s elapsed")

    # Clean up
    await market_client.unsubscribe_orderbook()
    await market_client.close()

    console.print("[green]Orderbook watch completed![/green]")


async def main():
    """Main function to run the example."""
    console.print("[bold blue]GTE Orderbook Watcher Example[/bold blue]\n")

    # Initialize client
    client = Client()

    try:
        # Get available markets
        console.print("Fetching available markets...")
        markets = await client.get_markets(limit=5)

        if not markets:
            console.print("[red]No markets available![/red]")
            return

        # Display available markets
        console.print("\n[bold]Available Markets:[/bold]")
        for i, market in enumerate(markets, 1):
            price = f"{market.price:.8f}" if market.price else "N/A"
            console.print(f"{i}. {market.pair} - Price: {price}")

        # Select first market for watching
        selected_market = markets[0]
        console.print(f"\nSelected market: [bold]{selected_market.pair}[/bold]")

        # Watch orderbook for 30 seconds
        console.print("\n[bold]Starting orderbook watch (30 seconds)...[/bold]")
        await watch_orderbook(client, selected_market.address, depth=7, duration=30)

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")

    finally:
        await client.close()


if __name__ == "__main__":
    try:
        import rich
    except ImportError:
        print("This example requires the 'rich' library for better display.")
        print("Install it using: pip install rich")
        exit(1)

    asyncio.run(main())
