"""Example of on-chain trading with the GTE client."""
import sys
sys.path.append(".")
import asyncio
import logging

from gte_py.api.chain.utils import make_web3
from gte_py.configs import TESTNET_CONFIG
from utils import (
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY
)


async def main() -> None:
    """Run the on-chain trading examples."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
