import asyncio
import os
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from eth_utils.address import to_checksum_address
from web3 import AsyncWeb3
from eth_utils.currency import to_wei
import time

# from examples.utils import show_all_orders
from gte_py.clients import GTEClient
from gte_py.api.chain.structs import OrderSide
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import TimeInForce, Token, Market, OrderType

load_dotenv()

WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")
MARKET_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address("0x5ca9f32d4ce7cc0f782213c446c2ae14b754a623")
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

        market = await client.info.get_market(MARKET_ADDRESS)
        print(market)
        
        # if using an eth clob market you have to wrap before selling eth and unwrap after buying eth
        # wrap the eth
        weth_balance = await client.execution.get_weth_balance()
        if weth_balance < 10 ** 16:
            await client.execution.wrap_eth(amount=10 ** 16 - weth_balance, gas=50 * 10**6)
        
        # buy eth
        order = await client.execution.place_market_order(  # type: ignore
            market=market,
            side=OrderSide.BUY,
            amount=10 ** 16,
            amount_is_raw=True,
            amount_is_base=True,
            slippage=0.05,
            gas=50 * 10**6
        )
        
        weth_balance = await client.execution.get_weth_balance()
        await client.execution.unwrap_eth(amount=weth_balance, gas=50 * 10**6)

        
        print_separator(f"Order posted: {order}")
        
        return


if __name__ == "__main__":
    asyncio.run(main())
