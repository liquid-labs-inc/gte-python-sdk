"""Command-line interface."""

import asyncio
import json
import typer
from typing import List, Optional

from .raw import GTERestClient, GTEWebSocketClient

app = typer.Typer(help="gte_py - A Python CLI for interacting with GTE API")


@app.command()
def hello(name: str = "World"):
    """Say hello to someone."""
    typer.echo(f"Hello {name}!")


@app.command()
def health():
    """Check the health of the GTE API."""
    async def _health():
        async with GTERestClient() as client:
            result = await client.get_health()
            typer.echo(json.dumps(result, indent=2))
    
    asyncio.run(_health())


@app.command()
def assets(creator: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Get list of assets."""
    async def _assets():
        async with GTERestClient() as client:
            result = await client.get_assets(creator=creator, limit=limit, offset=offset)
            typer.echo(json.dumps(result, indent=2))
    
    asyncio.run(_assets())


@app.command()
def asset(address: str):
    """Get asset by address."""
    async def _asset():
        async with GTERestClient() as client:
            result = await client.get_asset(address)
            typer.echo(json.dumps(result, indent=2))
    
    asyncio.run(_asset())


@app.command()
def markets(
    limit: int = 100,
    offset: int = 0,
    market_type: Optional[str] = None,
    asset: Optional[str] = None,
    price: Optional[float] = None
):
    """Get list of markets."""
    async def _markets():
        async with GTERestClient() as client:
            result = await client.get_markets(
                limit=limit,
                offset=offset,
                market_type=market_type,
                asset=asset,
                price=price
            )
            typer.echo(json.dumps(result, indent=2))
    
    asyncio.run(_markets())


@app.command()
def market(address: str):
    """Get market by address."""
    async def _market():
        async with GTERestClient() as client:
            result = await client.get_market(address)
            typer.echo(json.dumps(result, indent=2))
    
    asyncio.run(_market())


@app.command()
def watch_trades(market_addresses: List[str], duration: int = 60):
    """Watch trades for specified markets.
    
    Args:
        market_addresses: List of market addresses
        duration: Duration in seconds to watch trades
    """
    async def _watch_trades():
        ws_client = GTEWebSocketClient()
        
        async def handle_trade(data):
            typer.echo(json.dumps(data, indent=2))
        
        await ws_client.connect()
        await ws_client.subscribe_trades(market_addresses, handle_trade)
        
        try:
            await asyncio.sleep(duration)
        finally:
            await ws_client.close()
    
    asyncio.run(_watch_trades())


@app.command()
def watch_candles(market_address: str, interval: str = "1m", duration: int = 60):
    """Watch candles for a market.
    
    Args:
        market_address: Market address
        interval: Candle interval
        duration: Duration in seconds to watch candles
    """
    async def _watch_candles():
        ws_client = GTEWebSocketClient()
        
        async def handle_candle(data):
            typer.echo(json.dumps(data, indent=2))
        
        await ws_client.connect()
        await ws_client.subscribe_candles(market_address, interval, handle_candle)
        
        try:
            await asyncio.sleep(duration)
        finally:
            await ws_client.close()
    
    asyncio.run(_watch_candles())


def run():
    """Run the application."""
    app()


if __name__ == "__main__":
    run()
