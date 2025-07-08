"""Example of wrapping and unwrapping ETH to WETH."""
import sys
sys.path.append(".")
import asyncio

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import WALLET_PRIVATE_KEY


async def main():
    config = TESTNET_CONFIG
    
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        # wrap eth to weth
        weth_balance = await client.execution.get_weth_balance()
        if weth_balance < 10 ** 16:
            await client.execution.wrap_eth(amount=10 ** 16 - weth_balance, gas=50 * 10**6)

        # unwrap weth to eth
        weth_balance = await client.execution.get_weth_balance()
        await client.execution.unwrap_eth(amount=weth_balance, gas=50 * 10**6)
        
        return


if __name__ == "__main__":
    asyncio.run(main())
