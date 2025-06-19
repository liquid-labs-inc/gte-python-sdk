"""Simple example demonstrating how to watch a market's orderbook using WebSocket ETH RPC."""
import sys

sys.path.append(".")

from examples.utils import MARKET_ADDRESS

from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG

import asyncio
import logging


async def main():
    """Run the orderbook watcher example."""
    web3 = await make_web3(TESTNET_CONFIG)

    # Initialize GTE client for market info
    client = Client(web3=web3, config=TESTNET_CONFIG)

    # Get market details
    market_address = MARKET_ADDRESS
    market = await client.info.get_market(market_address)

    # Create and start the watcher
    await client.market.subscribe_trades(market, lambda x: print(x))

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
