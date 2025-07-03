import asyncio
import os
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from web3 import AsyncWeb3

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market

load_dotenv()

WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")
MARKET_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")
# BTC CLOB: 0x0F3642714B9516e3d17a936bAced4de47A6FFa5F
# ETH CLOB: 0x5ca9f32d4ce7cc0f782213c446c2ae14b754a623

if not WALLET_ADDRESS_RAW or not WALLET_PRIVATE_KEY_RAW:
    raise ValueError("Missing wallet credentials")

WALLET_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address(WALLET_ADDRESS_RAW)
WALLET_PRIVATE_KEY: HexStr = HexStr(WALLET_PRIVATE_KEY_RAW)


def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def main():
    config = TESTNET_CONFIG
    weth_address = config.weth_address
    if not weth_address:
        raise ValueError("WETH address not configured")
        
    async with GTEClient(config=config, wallet_address=WALLET_ADDRESS, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        open_orders = await client.info.get_user_open_orders(WALLET_ADDRESS, MARKET_ADDRESS)
        print_separator(f"Open orders: {open_orders}")
        
        market = await client.info.get_market(MARKET_ADDRESS)
        
        # convert to order model
        for order in open_orders:
            _ = await client.execution.cancel_order(market, int(order["orderId"]), gas=50 * 10**6)
        
        return
    
    
if __name__ == "__main__":
    asyncio.run(main())