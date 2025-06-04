# GTE WebSocket API Documentation

This document provides information on how to use the GTE WebSocket API for real-time market data.

## Overview

The WebSocket API allows you to receive real-time market data including:

- Order book updates (L2 market depth)
- Trade execution events
- OHLCV candle updates

## Connection

The WebSocket endpoint is available at:

- Testnet: `wss://ws-testnet.gte.io/v1`
- Mainnet: `wss://ws.gte.io/v1`

## Message Format

### Subscription Request

All subscription requests follow this format:

```json
{
  "id": "unique-request-id",
  "method": "topic.subscribe",
  "params": {
    // Topic-specific parameters
  }
}
```

### Subscription Response

The server responds to subscription requests with:

```json
{
  "id": "unique-request-id",
  "status": 0
}
```

## Available Feeds

### Order Book (L2 Market Depth)

#### Subscribe

```json
{
  "id": "book-sub-1",
  "method": "book.subscribe",
  "params": {
    "market": "0xMarketAddress",
    "limit": 10
  }
}
```

#### Unsubscribe

```json
{
  "method": "book.unsubscribe",
  "params": {
    "market": "0xMarketAddress",
    "limit": 10
  }
}
```

#### Message Format

```json
{
  "s": "book",
  "d": {
    "a": [{"px": "3442.5", "sz": "0.5", "n": 2}],
    "b": [{"px": "3441.5", "sz": "1.2", "n": 3}],
    "t": 1721166232023,
    "m": "0xMarketAddress"
  }
}
```

Where:
- `s`: Stream type ("book")
- `d.a`: Array of asks (offer to sell), sorted from lowest to highest price
- `d.b`: Array of bids (offer to buy), sorted from highest to lowest price
- `px`: Price
- `sz`: Size
- `n`: Number of orders at this price level
- `t`: Timestamp
- `m`: Market address

### Trades

#### Subscribe

```json
{
  "id": "trades-sub-1",
  "method": "trades.subscribe",
  "params": {
    "market": "0xMarketAddress"
  }
}
```

#### Unsubscribe

```json
{
  "method": "trades.unsubscribe",
  "params": {
    "market": "0xMarketAddress"
  }
}
```

#### Message Format

```json
{
  "s": "trades",
  "d": {
    "sd": "buy",
    "m": "0xMarketAddress",
    "px": "3442.0",
    "sz": "0.0995",
    "h": "0x...",
    "id": 2934702386,
    "t": 1721166232023
  }
}
```

Where:
- `s`: Stream type ("trades")
- `d.sd`: Side ("buy" or "sell")
- `d.m`: Market address
- `d.px`: Price
- `d.sz`: Size
- `d.h`: Transaction hash
- `d.id`: Trade ID
- `d.t`: Timestamp

### Candles (OHLCV)

#### Subscribe

```json
{
  "id": "candles-sub-1",
  "method": "candles.subscribe",
  "params": {
    "market": "0xMarketAddress",
    "interval": "1m"
  }
}
```

Supported intervals: `1s`, `30s`, `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `4h`, `6h`, `8h`, `12h`, `1d`, `1w`

#### Unsubscribe

```json
{
  "method": "candles.unsubscribe",
  "params": {
    "market": "0xMarketAddress",
    "interval": "1m"
  }
}
```

#### Message Format

```json
{
  "s": "candle",
  "d": {
    "m": "0xMarketAddress",
    "t": 1672515780000,
    "i": "1m",
    "o": "3442.9",
    "h": "3456.3",
    "l": "3421.2",
    "c": "3432.4",
    "v": "1.2569",
    "n": 2
  }
}
```

Where:
- `s`: Stream type ("candle")
- `d.m`: Market address
- `d.t`: Candle start time
- `d.i`: Interval
- `d.o`: Open price
- `d.c`: Close price
- `d.h`: High price
- `d.l`: Low price
- `d.v`: Volume
- `d.n`: Number of trades

## Error Handling

If there's an error with your request, you'll receive:

```json
{
  "id": "your-request-id",
  "status": 1,
  "error": "Error message description"
}
```

## Using the GTE Python Client

The GTE Python client provides a convenient wrapper around the WebSocket API:

```python
from gte_py.api.ws import WebSocketApi
from gte_py.configs import TESTNET_CONFIG

# Initialize WebSocket API
ws_api = WebSocketApi(ws_url=TESTNET_CONFIG.ws_url)
await ws_api.connect()

# Subscribe to orderbook updates
await ws_api.subscribe_orderbook(
    market="0xMarketAddress",
    limit=10,
    callback=your_callback_function
)

# Subscribe to trade updates
await ws_api.subscribe_trades(
    market="0xMarketAddress",
    callback=your_callback_function
)

# Subscribe to candle updates
await ws_api.subscribe_candles(
    market="0xMarketAddress",
    interval="1m",
    callback=your_callback_function
)

# Unsubscribe examples
await ws_api.unsubscribe_orderbook(market="0xMarketAddress")
await ws_api.unsubscribe_trades(market="0xMarketAddress")
await ws_api.unsubscribe_candles(market="0xMarketAddress", interval="1m")

# Close connection when done
await ws_api.close()
```

See the `examples/websocket_example.py` file for complete usage examples.
