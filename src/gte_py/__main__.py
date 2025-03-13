"""Command-line interface."""

import asyncio
import json
from typing import List, Optional
from datetime import datetime, timedelta
import typer
from pprint import pprint

from . import GteClient, GteMarketClient

app = typer.Typer(help="gte_py - A Python CLI for interacting with GTE API")


@app.command()
def hello(name: str = "World"):
    """Say hello to someone."""
    typer.echo(f"Hello {name}!")


@app.command()
def health():
    """Check the health of the GTE API."""
    async def _health():
        async with GteClient() as client:
            # Use the raw client directly for health check
            result = await client._rest_client.get_health()
            typer.echo(json.dumps(result, indent=2))
    
    asyncio.run(_health())


@app.command()
def assets(creator: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Get list of assets."""
    async def _assets():
        async with GteClient() as client:
            assets = await client.get_assets(creator=creator, limit=limit, offset=offset)
            # Convert to dict for JSON serialization
            assets_data = [
                {
                    "address": asset.address,
                    "name": asset.name,
                    "symbol": asset.symbol,
                    "decimals": asset.decimals,
                    "creator": asset.creator,
                    "totalSupply": asset.total_supply,
                    "mediaUri": asset.media_uri
                } for asset in assets
            ]
            typer.echo(json.dumps({"assets": assets_data, "total": len(assets)}, indent=2))
    
    asyncio.run(_assets())


@app.command()
def asset(address: str):
    """Get asset by address."""
    async def _asset():
        async with GteClient() as client:
            asset = await client.get_asset(address)
            # Convert to dict for JSON serialization
            asset_data = {
                "address": asset.address,
                "name": asset.name,
                "symbol": asset.symbol,
                "decimals": asset.decimals,
                "creator": asset.creator,
                "totalSupply": asset.total_supply,
                "mediaUri": asset.media_uri
            }
            typer.echo(json.dumps(asset_data, indent=2))
    
    asyncio.run(_asset())


@app.command()
def markets(
    limit: int = 100,
    offset: int = 0,
    market_type: Optional[str] = None,
    asset_address: Optional[str] = None,
    max_price: Optional[float] = None
):
    """Get list of markets."""
    async def _markets():
        async with GteClient() as client:
            markets = await client.get_markets(
                limit=limit,
                offset=offset,
                market_type=market_type,
                asset_address=asset_address,
                max_price=max_price
            )
            # Convert to dict for JSON serialization
            markets_data = [
                {
                    "address": market.address,
                    "marketType": market.market_type,
                    "baseAsset": {
                        "address": market.base_asset.address,
                        "name": market.base_asset.name,
                        "symbol": market.base_asset.symbol,
                        "decimals": market.base_asset.decimals
                    },
                    "quoteAsset": {
                        "address": market.quote_asset.address,
                        "name": market.quote_asset.name,
                        "symbol": market.quote_asset.symbol,
                        "decimals": market.quote_asset.decimals
                    },
                    "price": market.price,
                    "volume24hr": market.volume_24h,
                    "pair": market.pair
                } for market in markets
            ]
            typer.echo(json.dumps({"markets": markets_data, "total": len(markets)}, indent=2))
    
    asyncio.run(_markets())


@app.command()
def market(address: str):
    """Get market by address."""
    async def _market():
        async with GteClient() as client:
            market = await client.get_market(address)
            # Convert to dict for JSON serialization
            market_data = {
                "address": market.address,
                "marketType": market.market_type,
                "baseAsset": {
                    "address": market.base_asset.address,
                    "name": market.base_asset.name,
                    "symbol": market.base_asset.symbol,
                    "decimals": market.base_asset.decimals
                },
                "quoteAsset": {
                    "address": market.quote_asset.address,
                    "name": market.quote_asset.name,
                    "symbol": market.quote_asset.symbol,
                    "decimals": market.quote_asset.decimals
                },
                "price": market.price,
                "volume24hr": market.volume_24h,
                "pair": market.pair
            }
            typer.echo(json.dumps(market_data, indent=2))
    
    asyncio.run(_market())


@app.command()
def candles(
    market_address: str,
    interval: str = "1h",
    days: int = 1,
    limit: int = 500
):
    """Get historical candles for a market."""
    async def _candles():
        async with GteClient() as client:
            start_time = datetime.now() - timedelta(days=days)
            candles = await client.get_candles(
                market_address=market_address,
                interval=interval,
                start_time=start_time,
                limit=limit
            )
            # Convert to dict for JSON serialization
            candles_data = [
                {
                    "timestamp": candle.timestamp,
                    "datetime": candle.datetime.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume
                } for candle in candles
            ]
            typer.echo(json.dumps({"candles": candles_data, "total": len(candles)}, indent=2))
    
    asyncio.run(_candles())


@app.command()
def trades(market_address: str, limit: int = 50):
    """Get recent trades for a market."""
    async def _trades():
        async with GteClient() as client:
            trades = await client.get_recent_trades(market_address, limit)
            # Convert to dict for JSON serialization
            trades_data = [
                {
                    "timestamp": trade.timestamp,
                    "datetime": trade.datetime.isoformat(),
                    "price": trade.price,
                    "size": trade.size,
                    "side": trade.side,
                    "txHash": trade.tx_hash
                } for trade in trades
            ]
            typer.echo(json.dumps({"trades": trades_data, "total": len(trades)}, indent=2))
    
    asyncio.run(_trades())


@app.command()
def watch_market(
    market_address: str, 
    watch_trades: bool = True,
    watch_candles: bool = True,
    watch_orderbook: bool = False,
    candle_interval: str = "1m",
    duration: int = 60
):
    """Watch real-time market data.
    
    Args:
        market_address: Market address
        watch_trades: Watch trades
        watch_candles: Watch candles
        watch_orderbook: Watch orderbook
        candle_interval: Candle interval
        duration: Duration in seconds to watch
    """
    async def _watch_market():
        async with GteClient() as client:
            # Get market info first
            market = await client.get_market(market_address)
            typer.echo(f"Watching market: {market.pair} ({market.address})")
            
            # Get market client
            market_client = await client.get_market_client(market_address)
            
            # Define callbacks
            def on_trade(trade):
                typer.echo(f"[TRADE] {trade.datetime.isoformat()} | {trade.side.upper()} {trade.size} @ {trade.price}")
            
            def on_candle(candle):
                typer.echo(f"[CANDLE] {candle.datetime.isoformat()} | O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close} V:{candle.volume}")
            
            def on_orderbook(update):
                best_bid = update.best_bid['price'] if update.best_bid else "N/A"
                best_ask = update.best_ask['price'] if update.best_ask else "N/A"
                typer.echo(f"[ORDERBOOK] {update.datetime.isoformat()} | Bid: {best_bid} | Ask: {best_ask} | Spread: {update.spread}")
            
            # Subscribe to requested data
            if watch_trades:
                await market_client.subscribe_trades(on_trade)
                typer.echo("Subscribed to trades")
            
            if watch_candles:
                await market_client.subscribe_candles(candle_interval, on_candle)
                typer.echo(f"Subscribed to {candle_interval} candles")
            
            if watch_orderbook:
                await market_client.subscribe_orderbook(on_orderbook)
                typer.echo("Subscribed to orderbook")
            
            # Wait for specified duration
            typer.echo(f"Watching for {duration} seconds...")
            await asyncio.sleep(duration)
            
            # Clean up
            await market_client.close()
            typer.echo("Watching completed.")
    
    asyncio.run(_watch_market())


@app.command()
def user_assets(user_address: str, limit: int = 100):
    """Get assets held by a user."""
    async def _user_assets():
        async with GteClient() as client:
            assets = await client.get_user_assets(user_address, limit)
            # Convert to dict for JSON serialization
            assets_data = [
                {
                    "address": asset.address,
                    "name": asset.name,
                    "symbol": asset.symbol,
                    "decimals": asset.decimals,
                    "balance": asset.balance
                } for asset in assets
            ]
            typer.echo(json.dumps({"assets": assets_data, "total": len(assets)}, indent=2))
    
    asyncio.run(_user_assets())


@app.command()
def user_positions(user_address: str):
    """Get LP positions for a user."""
    async def _user_positions():
        async with GteClient() as client:
            positions = await client.get_positions(user_address)
            # Convert to dict for JSON serialization
            positions_data = [
                {
                    "market": {
                        "address": pos.market.address,
                        "pair": pos.market.pair
                    },
                    "token0Amount": pos.token0_amount,
                    "token1Amount": pos.token1_amount
                } for pos in positions
            ]
            typer.echo(json.dumps({"positions": positions_data, "total": len(positions)}, indent=2))
    
    asyncio.run(_user_positions())


def run():
    """Run the application."""
    app()


if __name__ == "__main__":
    run()
