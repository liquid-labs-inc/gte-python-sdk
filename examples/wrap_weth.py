
import asyncio
import os
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from web3 import AsyncWeb3

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG

load_dotenv()

WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")

if not WALLET_ADDRESS_RAW or not WALLET_PRIVATE_KEY_RAW:
    raise ValueError("Missing wallet credentials")

WALLET_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address(WALLET_ADDRESS_RAW)
WALLET_PRIVATE_KEY: HexStr = HexStr(WALLET_PRIVATE_KEY_RAW)


async def main():
    config = TESTNET_CONFIG
    
    async with GTEClient(config=config, wallet_address=WALLET_ADDRESS, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        weth_balance = await client.execution.get_weth_balance()
        if weth_balance < 10 ** 16:
            await client.execution.wrap_eth(amount=10 ** 16 - weth_balance, gas=50 * 10**6)

        weth_balance = await client.execution.get_weth_balance()
        await client.execution.unwrap_eth(amount=weth_balance, gas=50 * 10**6)
        
        return


if __name__ == "__main__":
    asyncio.run(main())
