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
```

## Missing API Requirements for Trading

The following endpoints are currently not documented but would be required for a complete trading experience on the GTE platform. These endpoints would enable trading functionality via both Central Limit Order Books (CLOB) and Automated Market Makers (AMM).

### Authentication

To access trading functionality, authentication would be required:

**POST** `/auth/login`

**Request Body**:
```json
{
  "walletAddress": "<string>",
  "signature": "<string>"
}
```

**Response 200**:
```json
{
  "token": "<JWT Token>",
  "expiresAt": 1234567890
}
```

All subsequent authenticated requests should include this token in the Authorization header:
```
Authorization: Bearer <JWT Token>
```

### Order Management (CLOB)

#### Create a new order

**POST** `/orders`

**Request Body**:
```json
{
  "marketAddress": "<string>",
  "side": "buy|sell",
  "type": "limit|market",
  "amount": 123.45,
  "price": 123.45,  // Required for limit orders
  "timeInForce": "GTC|IOC|FOK",  // Good-till-cancelled, Immediate-or-cancel, Fill-or-kill
  "clientOrderId": "<string>"  // Optional client-assigned ID
}
```

**Response 200**:
```json
{
  "id": "<string>",
  "marketAddress": "<string>",
  "side": "buy|sell",
  "type": "limit|market",
  "status": "open",
  "amount": 123.45,
  "price": 123.45,
  "timeInForce": "GTC|IOC|FOK",
  "filledAmount": 0,
  "avgFilledPrice": 0,
  "remainingAmount": 123.45,
  "clientOrderId": "<string>",
  "createdAt": 1234567890,
  "updatedAt": 1234567890
}
```

#### Cancel an order

**DELETE** `/orders/{order_id}`

**Path Parameters**:
- `order_id` (string, required): Order identifier

**Response 200**:
```json
{
  "success": true,
  "orderId": "<string>"
}
```

#### Cancel all orders

**DELETE** `/orders`

**Query Parameters**:
- `marketAddress` (string, optional): Cancel orders for specific market only

**Response 200**:
```json
{
  "success": true,
  "cancelledCount": 5
}
```

#### Get orders for a user

**GET** `/orders`

**Query Parameters**:
- `marketAddress` (string, optional): Filter by market
- `status` (string, optional): Filter by status (open, filled, canceled, all)
- `limit` (integer, default: 50): Maximum number of orders to return
- `before` (integer, optional): Return orders before this timestamp
- `after` (integer, optional): Return orders after this timestamp

**Response 200**:
```json
{
  "orders": [
    {
      "id": "<string>",
      "marketAddress": "<string>",
      "side": "buy|sell",
      "type": "limit|market",
      "status": "open|filled|canceled",
      "amount": 123.45,
      "price": 123.45,
      "timeInForce": "GTC|IOC|FOK",
      "filledAmount": 123.45,
      "avgFilledPrice": 123.45,
      "remainingAmount": 0,
      "clientOrderId": "<string>",
      "createdAt": 1234567890,
      "updatedAt": 1234567890
    }
  ],
  "total": 123
}
```

#### Get order by ID

**GET** `/orders/{order_id}`

**Path Parameters**:
- `order_id` (string, required): Order identifier

**Response 200**:
```json
{
  "id": "<string>",
  "marketAddress": "<string>",
  "side": "buy|sell",
  "type": "limit|market",
  "status": "open|filled|canceled",
  "amount": 123.45,
  "price": 123.45,
  "timeInForce": "GTC|IOC|FOK",
  "filledAmount": 123.45,
  "avgFilledPrice": 123.45,
  "remainingAmount": 0,
  "clientOrderId": "<string>",
  "createdAt": 1234567890,
  "updatedAt": 1234567890
}
```

#### Get order fills

**GET** `/orders/{order_id}/fills`

**Path Parameters**:
- `order_id` (string, required): Order identifier

**Response 200**:
```json
{
  "fills": [
    {
      "id": "<string>",
      "orderId": "<string>",
      "marketAddress": "<string>",
      "price": 123.45,
      "amount": 123.45,
      "side": "buy|sell",
      "fee": 1.23,
      "feeAsset": "<string>",
      "timestamp": 1234567890
    }
  ],
  "total": 123
}
```

### Batch Order Operations

#### Place multiple orders at once

**POST** `/orders/batch`

**Request Body**:
```json
{
  "orders": [
    {
      "marketAddress": "<string>",
      "side": "buy|sell",
      "type": "limit|market",
      "amount": 123.45,
      "price": 123.45,
      "timeInForce": "GTC|IOC|FOK",
      "clientOrderId": "<string>"
    }
  ]
}
```

**Response 200**:
```json
{
  "orders": [
    {
      "id": "<string>",
      "clientOrderId": "<string>",
      "status": "open"
    }
  ],
  "errors": []
}
```

#### Cancel multiple orders

**POST** `/orders/cancel-batch`

**Request Body**:
```json
{
  "orderIds": ["<string>", "<string>"]
}
```

**Response 200**:
```json
{
  "cancelledIds": ["<string>", "<string>"],
  "failedIds": []
}
```

### Asset Management

#### Get balances for user

**GET** `/balances`

**Response 200**:
```json
{
  "balances": [
    {
      "asset": {
        "address": "<string>",
        "symbol": "<string>"
      },
      "free": 123.45,
      "locked": 1.25,
      "total": 124.70
    }
  ]
}
```

#### Convert asset (Swap)

**POST** `/convert`

**Request Body**:
```json
{
  "fromAsset": "<string>",
  "toAsset": "<string>",
  "amount": 123.45,
  "minAmountOut": 45.67,
  "deadline": 1234567890
}
```

**Response 200**:
```json
{
  "success": true,
  "transactionHash": "<string>",
  "fromAmount": 123.45,
  "toAmount": 45.67,
  "rate": 0.37,
  "fee": 0.2,
  "timestamp": 1234567890
}
```

### AMM Pool Operations

#### Get all pools

**GET** `/pools`

**Query Parameters**:
- `token` (string, optional): Filter pools containing this token
- `limit` (integer, default: 100): Maximum number of pools to return
- `offset` (integer, default: 0): Pagination offset

**Response 200**:
```json
{
  "pools": [
    {
      "address": "<string>",
      "token0": {
        "address": "<string>",
        "symbol": "<string>"
      },
      "token1": {
        "address": "<string>",
        "symbol": "<string>"
      },
      "fee": 0.003,
      "totalLiquidity": 123.45,
      "volume24h": 123.45,
      "apr": 12.34
    }
  ],
  "total": 123
}
```

#### Get pool information

**GET** `/pools/{pool_address}`

**Path Parameters**:
- `pool_address` (string, required): AMM pool address

**Response 200**:
```json
{
  "address": "<string>",
  "token0": {
    "address": "<string>",
    "symbol": "<string>",
    "name": "<string>",
    "decimals": 18,
    "reserve": 123.45
  },
  "token1": {
    "address": "<string>",
    "symbol": "<string>",
    "name": "<string>",
    "decimals": 6,
    "reserve": 123456.78
  },
  "fee": 0.003,  // 0.3%
  "totalLiquidity": 123.45,  // In USD
  "volume24h": 123.45,
  "volume7d": 123.45,
  "fees24h": 1.23,
  "apr": 12.34,  // Annual percentage rate
  "createdAt": 1234567890
}
```

#### Get pool reserves history

**GET** `/pools/{pool_address}/history`

**Path Parameters**:
- `pool_address` (string, required): Pool address

**Query Parameters**:
- `interval` (string, default: "1d"): Data interval (1h, 4h, 1d, 1w)
- `limit` (integer, default: 30): Number of data points

**Response 200**:
```json
{
  "history": [
    {
      "timestamp": 1234567890,
      "reserve0": 123.45,
      "reserve1": 456.78,
      "totalLiquidityUsd": 10000.00,
      "volume": 5000.00,
      "fees": 15.00
    }
  ]
}
```

#### Add liquidity to a pool

**POST** `/pools/{pool_address}/add`

**Path Parameters**:
- `pool_address` (string, required): AMM pool address

**Request Body**:
```json
{
  "token0Amount": 123.45,
  "token1Amount": 123.45,
  "slippageTolerance": 0.005  // 0.5%
}
```

**Response 200**:
```json
{
  "transactionHash": "<string>",
  "poolAddress": "<string>",
  "token0": {
    "address": "<string>",
    "amount": 123.45
  },
  "token1": {
    "address": "<string>",
    "amount": 123.45
  },
  "lpTokens": 123.45,
  "timestamp": 1234567890
}
```

#### Remove liquidity from a pool

**POST** `/pools/{pool_address}/remove`

**Path Parameters**:
- `pool_address` (string, required): AMM pool address

**Request Body**:
```json
{
  "lpTokenAmount": 123.45,  // Amount of LP tokens to burn
  "minToken0Amount": 123.45, // Minimum amount of token0 to receive
  "minToken1Amount": 123.45  // Minimum amount of token1 to receive
}
```

**Response 200**:
```json
{
  "transactionHash": "<string>",
  "poolAddress": "<string>",
  "token0": {
    "address": "<string>",
    "amount": 123.45
  },
  "token1": {
    "address": "<string>",
    "amount": 123.45
  },
  "lpTokensBurned": 123.45,
  "timestamp": 1234567890
}
```

#### Get price quote for a token swap

**GET** `/quote`

**Query Parameters**:
- `fromToken` (string, required): Address of token to sell
- `toToken` (string, required): Address of token to buy
- `amount` (number, required): Amount of fromToken to sell
- `side` (string, default: "sell"): "sell" or "buy" (if "buy", amount is the desired amount of toToken)

**Response 200**:
```json
{
  "fromToken": {
    "address": "<string>",
    "symbol": "<string>",
    "amount": 123.45
  },
  "toToken": {
    "address": "<string>",
    "symbol": "<string>",
    "amount": 456.78
  },
  "exchangeRate": 3.7,
  "priceImpact": 0.0042,  // 0.42%
  "fee": 0.37,
  "route": [
    {
      "type": "amm",
      "poolAddress": "<string>",
      "fromToken": "<string>",
      "toToken": "<string>",
      "share": 1.0
    }
  ],
  "validUntil": 1234567890
}
```

### Market Making

#### Create or update market making strategy

**POST** `/market-maker/strategies`

**Request Body**:
```json
{
  "marketAddress": "<string>",
  "enabled": true,
  "bidSpread": 0.005,  // 0.5%
  "askSpread": 0.005,  // 0.5%
  "orderSize": 1.0,
  "orderCount": 3,
  "priceGap": 0.003,   // 0.3%
  "rebalanceThreshold": 0.01,  // 1%
  "maxExposure": 10.0
}
```

**Response 200**:
```json
{
  "id": "<string>",
  "marketAddress": "<string>",
  "enabled": true,
  "bidSpread": 0.005,
  "askSpread": 0.005,
  "orderSize": 1.0,
  "orderCount": 3,
  "priceGap": 0.003,
  "rebalanceThreshold": 0.01,
  "maxExposure": 10.0,
  "createdAt": 1234567890,
  "updatedAt": 1234567890
}
```

#### Get market making strategies

**GET** `/market-maker/strategies`

**Response 200**:
```json
{
  "strategies": [
    {
      "id": "<string>",
      "marketAddress": "<string>",
      "enabled": true,
      "bidSpread": 0.005,
      "askSpread": 0.005,
      "orderSize": 1.0,
      "orderCount": 3,
      "priceGap": 0.003,
      "rebalanceThreshold": 0.01,
      "maxExposure": 10.0,
      "createdAt": 1234567890,
      "updatedAt": 1234567890
    }
  ]
}
```

#### Delete market making strategy

**DELETE** `/market-maker/strategies/{strategy_id}`

**Path Parameters**:
- `strategy_id` (string, required): Strategy identifier

**Response 200**:
```json
{
  "success": true
}
```

## WebSocket API for CLOB (Order Book Updates)

In addition to the orderbook endpoint already documented, the following WebSocket message types would be needed for complete CLOB functionality:

### Order Updates

Subscribe to receive updates about your own orders:

**Subscribe Request**:
```json
{
  "id": "<unique_id>",
  "method": "orders.subscribe",
  "params": {}
}
```

**Order Update Stream**:
```json
{
  "s": "orderUpdate",
  "d": {
    "id": "<string>",
    "m": "<market_address>",
    "status": "open|filled|partiallyFilled|canceled",
    "filledAmount": 123.45,
    "remainingAmount": 123.45,
    "avgFilledPrice": 123.45,
    "t": 1721166232023
  }
}
```

### User Trade Updates

Subscribe to receive real-time updates about your trades:

**Subscribe Request**:
```json
{
  "id": "<unique_id>",
  "method": "userTrades.subscribe",
  "params": {}
}
```

**User Trade Stream**:
```json
{
  "s": "userTrade",
  "d": {
    "id": "<string>",
    "m": "<market_address>",
    "orderId": "<string>",
    "sd": "buy|sell",
    "px": 3442.0,
    "sz": 0.0995,
    "fee": 0.12,
    "feeAsset": "<string>",
    "t": 1721166232023
  }
}
```

### User Balance Updates

Subscribe to receive balance updates:

**Subscribe Request**:
```json
{
  "id": "<unique_id>",
  "method": "balances.subscribe",
  "params": {}
}
```

**Balance Update Stream**:
```json
{
  "s": "balanceUpdate",
  "d": {
    "asset": "<string>",
    "free": 123.45,
    "locked": 1.23,
    "t": 1721166232023
  }
}
```

### AMM Pool Updates

Subscribe to receive updates about pool reserves and liquidity:

**Subscribe Request**:
```json
{
  "id": "<unique_id>",
  "method": "pools.subscribe",
  "params": {
    "pools": ["<pool_address_1>", "<pool_address_2>"]
  }
}
```

**Pool Update Stream**:
```json
{
  "s": "poolUpdate",
  "d": {
    "address": "<string>",
    "reserve0": 123.45,
    "reserve1": 456.78,
    "liquidityUsd": 10000.00,
    "t": 1721166232023
  }
}
```

## Implementation Note

The GTE-py library includes placeholder implementations for trading functionality that simulate these endpoints. In a production environment, these methods would need to be updated to call the actual API endpoints once they are available.


