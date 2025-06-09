"""Example of on-chain trading with the GTE client."""
import sys

sys.path.append(".")
import asyncio
import logging

# from examples.utils import show_all_orders
from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG

from utils import (
    display_market_info,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
    MARKET_ADDRESS
)


async def main() -> None:
    """Run the on-chain trading examples."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")

    client = Client(web3=web3, config=network, account=WALLET_ADDRESS)
    await client.init()
    # Get a market to work with
    market = await display_market_info(client, MARKET_ADDRESS)
    open_orders = await client.user.get_open_orders(market)
    print("Opening orders:")
    for open_order in open_orders:
        print(
            f"Order ID: {open_order.order_id}, Price: {open_order.price}, Amount: {open_order.amount}, Side: {open_order.side}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
