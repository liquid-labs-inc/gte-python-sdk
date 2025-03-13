# gte-py

A Python project created with PyBuild.

GET is an decentralized exchange

## Introduction

GTE API provides access to static market data and metrics, user profile information, and token information. The API also enables off-chain smart routing to find the best liquidity across markets on GTE.

> Documentation is a work in progress and will be updated often until launch.

## API Reference

### REST API

The GTE API provides access to static market data and metrics, user profile information, and token information. The GTE API also enables off-chain smart routing to find the best liquidity across markets on GTE.

### WebSocket

The WebSocket Streams offer real-time data delivery for order books and trades, ensuring that users receive the most up-to-date market information. By maintaining a persistent connection, the WebSocket Streams provide low-latency updates, which are crucial for high-frequency trading, frontend applications, and market analysis. This service is designed to cater to the needs of market makers, traders, and developers who require immediate access to dynamic market data.

#### WebSocket Streams Introduction

Real-time updates for various market info streams including orderbook depth, OHLCV candles, and trades.

Developers can easily connect to the GTE WebSocket API to stream available market data. We recommend using a single connection to subscribe to multiple topics. Each subscription requires the following fields:

- **id**: An arbitrary identifier chosen by the developer to easily match WebSocket responses to their corresponding subscriptions.
- **method**: Specifies the topic to subscribe or unsubscribe from.
- **params**: Parameters specific to the subscription topic. When unsubscribing, the params must match the original subscription.

#### Trades

The trades channel provides real-time updates for trades of a specified market.

##### Request Format

**Trades Subscription Request**

```json
{
  "id": "<unique_id>",
  "method": "trades.subscribe",
  "params": {
    "markets": "Array<address>"
  }
}
```

**Trades Unsubscription Request**

```json
{
  "method": "trades.unsubscribe",
  "args": {
    "markets": "Array<address>"
  }
}
```

##### Response Format

The response structure is as follows:

**Trades Stream**

```json
{
  "s": "trades",
  "d": {
    "sd": "buy",
    "m": "<Market Address>",
    "px": "3442.0",
    "sz": "0.0995",
    "h": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "id": 2934702386,
    "t": 1721166232023
  }
}
```

- `s`: Stream type (always "trade" for this endpoint)
- `d`: Data object
  - `sd`: Side of the trade ("buy" or "sell")
  - `m`: Market address
  - `px`: Price of the trade
  - `sz`: Size of the trade
  - `h`: Transaction hash
  - `id`: Trade ID
  - `t`: Trade time (timestamp in milliseconds)

#### Candles

The candles channel provide OHLCV data.

##### Request Format

**Candles Subscription Request**

```json
{
  "id": "<unique_id>",
  "method": "candles.subscribe",
  "params": {
    "market": "<address>",
    "interval": "<interval>"
  }
}
```

**Candles Unsubscription Request**

```json
{
  "method": "candles.unsubscribe",
  "params": {
    "market": "<address>",
    "interval": "<interval>"
  }
}
```

The supported intervals are: `1s`, `30s`, `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `4h`, `6h`, `8h`, `12h`, `1d`, `1w`

##### Response Format

The response structure is as follows:

```json
{
  "s": "candle",
  "d": {
    "m": "<address>",
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

- `s`: Stream type (always "candle" for this endpoint)
- `d`: Data object
  - `m`: Market address
  - `t`: Candle start time (timestamp in milliseconds)
  - `i`: Interval (e.g., "1m" for 1 minute)
  - `o`: Open price
  - `c`: Close price
  - `h`: High price
  - `l`: Low price
  - `v`: Volume (base unit)
  - `n`: Number of trades

#### Orderbook [Coming Soon]

The orderbook channel provides real-time updates for the order book of a specified trading pair.

##### Request Format

**Orderbook Subscription Request**

```json
{
  "method": "subscribe",
  "subscription": "orderbook",
  "args": {
    "pair": "ETH-USDC"
  }
}
```

**Orderbook Unsubscription Request**

```json
{
  "method": "unsubscribe",
  "subscription": "orderbook",
  "args": {
    "pair": "ETH-USDC"
  }
}
```

##### Response Format

The response structure is as follows:

**Orderbook Stream**

```json
{
  "s": "orderbook",
  "d": {
    "m": "ETHUSD",
    "t": 1672515782136,
    "b": [
      {
        "px": "price",
        "sz": "size",
        "n": "number of orders"
      }
    ],
    "a": [
      {
        "px": "price",
        "sz": "size",
        "n": "number of orders"
      }
    ]
  }
}
```

- `s`: Stream type (always "orderbook" for this endpoint)
- `d`: Data object
  - `m`: Market pair (e.g., "ETHUSD")
  - `t`: Event time (timestamp in milliseconds)
  - `b`: Array of bid updates
  - `a`: Array of ask updates
    - `px`: Price level
    - `sz`: Size at this price level
    - `n`: Number of orders at this price level

#### Error Handling

In case of an error, the following structure will be returned:

**Error Response**

```json
{
  "id": "<unique_id>",
  "status": 1,
  "error": "<error_message>"
}
```

- `id`: Unique identifier for the request
- `status`: Always 1 for error messages
- `error`: Description of the error

## REST API Endpoints

### Health

#### Get API health status

**GET** `/health`

**Response 200**:
```json
{
  "status": "ok",
  "timestamp": "2023-11-07T05:31:56Z"
}
```

**Response Fields**:
- `status` (enum): Status of the API (Available options: ok, error)
- `timestamp` (string): Timestamp of the response

### Assets

#### Get list of assets

**GET** `/assets`

**Query Parameters**:
- `creator` (string): Returns assets created by the given user address
- `limit` (integer, default: 100): Range 1-1000
- `offset` (integer, default: 0): Min value 0

**Response 200**:
```json
{
  "assets": [
    {
      "address": "<string>",
      "decimals": 123,
      "name": "<string>",
      "symbol": "<string>",
      "creator": "<string>",
      "totalSupply": 123,
      "mediaUri": "<string>"
    }
  ],
  "total": 123
}
```

#### Get asset by address

**GET** `/assets/{asset_address}`

**Path Parameters**:
- `asset_address` (string, required): EVM address

**Response 200**:
```json
{
  "address": "<string>",
  "decimals": 123,
  "name": "<string>",
  "symbol": "<string>",
  "creator": "<string>",
  "totalSupply": 123,
  "mediaUri": "<string>"
}
```

### Markets

#### Get list of markets

**GET** `/markets`

**Query Parameters**:
- `limit` (integer, default: 100): Range 1-1000
- `offset` (integer, default: 0): Min value 0
- `marketType` (enum): Filter by market type. If null, all markets will be returned. Options: amm, launchpad
- `asset` (string): Address of the base asset to filter by
- `price` (number): Returns markets with price less than given value. Range 0-1000000000

**Response 200**:
```json
{
  "markets": [
    {
      "marketType": "amm",
      "address": "<string>",
      "baseAsset": {
        "address": "<string>",
        "decimals": 123,
        "name": "<string>",
        "symbol": "<string>",
        "creator": "<string>",
        "totalSupply": 123,
        "mediaUri": "<string>"
      },
      "quoteAsset": {
        "address": "<string>",
        "decimals": 123,
        "name": "<string>",
        "symbol": "<string>",
        "creator": "<string>",
        "totalSupply": 123,
        "mediaUri": "<string>"
      },
      "price": 123,
      "volume24hr": 123
    }
  ],
  "total": 123
}
```

#### Get market by address

**GET** `/markets/{market_address}`

**Path Parameters**:
- `market_address` (string, required): EVM address

**Response 200**:
```json
{
  "marketType": "amm",
  "address": "<string>",
  "baseAsset": {
    "address": "<string>",
    "decimals": 123,
    "name": "<string>",
    "symbol": "<string>",
    "creator": "<string>",
    "totalSupply": 123,
    "mediaUri": "<string>"
  },
  "quoteAsset": {
    "address": "<string>",
    "decimals": 123,
    "name": "<string>",
    "symbol": "<string>",
    "creator": "<string>",
    "totalSupply": 123,
    "mediaUri": "<string>"
  },
  "price": 123,
  "volume24hr": 123
}
```

#### Get candles for a market

**GET** `/markets/{market_address}/candles`

**Path Parameters**:
- `market_address` (string, required)

**Query Parameters**:
- `interval` (enum, required): Interval of the candle. Options: 1s, 30s, 1m, 3m, 5m, 15m, 30m, 1h, 4h, 6h, 8h, 12h, 1d, 1w
- `startTime` (integer, required)
- `endTime` (integer): If not supplied, the current time will be used
- `limit` (integer, default: 500): Range 1-1000

**Response 200**:
```json
{
  "candles": [
    {
      "timestamp": 123,
      "open": 123,
      "high": 123,
      "low": 123,
      "close": 123,
      "volume": 123
    }
  ],
  "total": 123
}
```

#### Get trades for a market

**GET** `/markets/{market_address}/trades`

**Path Parameters**:
- `market_address` (string, required)

**Query Parameters**:
- `limit` (integer, default: 100): Range 1-1000
- `offset` (integer, default: 0): Min value 0

**Response 200**:
```json
{
  "trades": [
    {
      "timestamp": 123,
      "transactionHash": "<string>",
      "maker": "<string>",
      "taker": "<string>",
      "price": 123,
      "size": 123,
      "side": "buy"
    }
  ],
  "total": 123
}
```

### Users

#### Get LP positions for a user

**GET** `/users/{user_address}/positions`

**Path Parameters**:
- `user_address` (string, required)

**Response 200**:
```json
{
  "positions": [
    {
      "market": {
        "marketType": "amm",
        "address": "<string>",
        "baseAsset": {
          "address": "<string>",
          "decimals": 123,
          "name": "<string>",
          "symbol": "<string>",
          "creator": "<string>",
          "totalSupply": 123,
          "mediaUri": "<string>"
        },
        "quoteAsset": {
          "address": "<string>",
          "decimals": 123,
          "name": "<string>",
          "symbol": "<string>",
          "creator": "<string>",
          "totalSupply": 123,
          "mediaUri": "<string>"
        },
        "price": 123,
        "volume24hr": 123
      },
      "user": "<string>",
      "token0Amount": 123,
      "token1Amount": 123
    }
  ],
  "total": 123
}
```

#### Get assets held by a user

**GET** `/users/{user_address}/assets`

**Path Parameters**:
- `user_address` (string, required)

**Query Parameters**:
- `limit` (integer, default: 100): Range 1-1000
- `offset` (integer, default: 0): Min value 0

**Response 200**:
```json
{
  "assets": [
    {
      "address": "<string>",
      "decimals": 123,
      "name": "<string>",
      "symbol": "<string>",
      "creator": "<string>",
      "totalSupply": 123,
      "mediaUri": "<string>",
      "balance": 123
    }
  ],
  "totalUsdBalance": 123,
  "total": 123
}


