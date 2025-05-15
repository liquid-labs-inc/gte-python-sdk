# GTE-PY

A Python SDK for interacting with the GTE decentralized exchange on MegaETH.

`pip install gte-py`

## Overview

gte-py provides a robust interface to interact with GTE's decentralized exchange protocol, allowing developers to:

- Query market information
- Execute trades
- Manage token operations
- Monitor orderbooks
- Interact with CLOB (Central Limit Order Book) contracts
- Listen to blockchain events

## What is GTE?

GTE is the world's fastest decentralized exchange, covering the entire lifecycle of a token – from its initial launch to sophisticated perpetuals trading – all on a single, high-performance platform. Unlike traditional approaches that force users to navigate separate launchpads (like PumpFun), DEXs (like Raydium), and CLOBs (like Binance or Hyperliquid) for different stages of an asset's journey, GTE unifies these critical market structures.

This integration is achieved through:

- **Token Launchpad & Launcher**: The starting point for new tokens, bootstrapping initial liquidity.
- **Classic AMM**: Facilitating price discovery and trading for newer or long-tail assets.
- **Spot and Perpetual CLOBs**: Offering CEX-level liquidity and advanced trading features for more established assets, powered by a crankless onchain design.
- **Best-Price Aggregator**: Ensuring optimal trade execution across GTE's integrated venues (AMM & CLOB) and potentially the wider MegaETH ecosystem.

By unifying these components, GTE eliminates the fragmentation and friction common in the crypto space. Users no longer need to bridge assets or manage accounts across disparate protocols. They can seamlessly follow a token's journey from a fair launch, through AMM price discovery, onto the spot CLOB, and finally trade its perpetuals contract (priced off the GTE spot index) — all within the unified GTE interface.

## What is MegaETH?

GTE is built on MegaETH. MegaETH is the first real-time blockchain. As an EVM-compatible Layer-2 on Ethereum, it achieves unparalleled performance through:

- Streamlined consensus with a single real-time sequencer for fast, reliable transaction ordering
- Parallel transaction processing for maximum throughput
- EigenDA integration for secure, decentralized data availability, preventing any single point of failure

These optimizations result in 100,000 transactions per second and single-digit millisecond latency, making MegaETH the fastest blockchain with Ethereum-level security.

### Why MegaETH?

MegaETH's architecture enables GTE to offer unique advantages:

- **CEX-level performance, onchain**: MegaETH's 100k TPS and 1ms block times allow GTE to run a fully onchain order book that matches centralized exchange speeds.
- **True market efficiency**: Extremely cheap gas enables GTE's crankless design. Market makers can place and cancel orders freely, leading to tighter spreads and more liquid markets.
- **Fair and familiar trading**: MegaETH's centralized sequencer allows GTE to implement true price-time-priority matching, mirroring traditional markets.
- **Ecosystem integration**: As an Ethereum L2, GTE's smart contracts on MegaETH are EVM-compatible, maximizing composability with other DeFi protocols.

## Installation

You can install the package directly from github:

```bash
# Clone the repository
git clone https://github.com/liquid-labs-inc/gte-python-sdk/
cd gte-py

# Install the package
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

Or include it in your `requirements.txt`:

```plaintext
git+https://github.com/liquid-labs-inc/gte-python-sdk#egg=gte-py
```

Or include it in your `pyproject.toml`:

```toml
dependencies = [
  "gte_py@git+https://github.com/liquid-labs-inc/gte-python-sdk#egg=gte-py"
]
```

## Project Structure

The SDK is organized into two main layers:

### Low-Level API

Located in `src/gte_py/api/`:

- **Chain API** (`api/chain/`): Direct blockchain interactions using Web3.py
- **REST API** (`api/rest/`): HTTP-based API interactions
- **WebSocket API** (`api/ws/`): WebSocket-based real-time data streams
- **OpenAPI** (`api/openapi/`): Auto-generated OpenAPI client

### High-Level Clients

Located in `src/gte_py/clients/`:

- **Account**: User account management
- **CLOB**: Central Limit Order Book operations
- **Token**: ERC20 token operations
- **Trades**: Trading functions
- **Info**: Market information
- **Orderbook**: Order book queries and monitoring
- **Execution**: Order execution handling

## Quick Start

```python
import asyncio
from web3 import AsyncWeb3
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.api.chain.utils import make_web3

WALLET_ADDRESS = to_checksum_address("0xYourWalletAddress")
PRIVATE_KEY = HexBytes("0xYourPrivateKey")


async def main():
    # Initialize AsyncWeb3
    config = TESTNET_CONFIG

    web3 = await make_web3(config, WALLET_ADDRESS, PRIVATE_KEY)

    # Initialize the client
    client = Client(
        web3=web3,
        config=config
    )

    # Query available markets
    markets = await client.clob.get_markets()
    print(f"Available markets: {len(markets)}")

    # Get more information
    for market in markets[:3]:  # Print first 3 markets
        market_info = await client.clob.get_market_info(market.address)
        print(f"Market: {market_info.name} ({market_info.symbol})")
        print(f"  Address: {market_info.address}")
        print(f"  Base token: {market_info.base_token_symbol}")
        print(f"  Quote token: {market_info.quote_token_symbol}")


if __name__ == "__main__":
    asyncio.run(main())
```

Check the `examples/` directory for more sample code.

## Configuration

The SDK uses the `NetworkConfig` class for configuration settings:

```python
from gte_py.configs import TESTNET_CONFIG

# Default config for MegaETH Testnet is provided
print(TESTNET_CONFIG.name)  # "MegaETH Testnet"
print(TESTNET_CONFIG.chain_id)  # 6342

# You can customize RPC endpoints using environment variables
# MEGAETH_TESTNET_RPC_HTTP and MEGAETH_TESTNET_RPC_WS
```

## Development

For detailed development instructions, please refer to the [Developer Guide](docs/Develop.md).

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Type Checking

```bash
pyright
```

## License

[License information]

## Contributing

Contributions are welcome! Please check out our [Developer Guide](docs/Develop.md) for details.
