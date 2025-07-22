"""Example of placing an order on a WETH market."""
import sys
sys.path.append(".")
import asyncio
from decimal import Decimal
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from examples.utils import WALLET_PRIVATE_KEY
from gte_py.clients import GTEClient
from gte_py.api.chain.structs import OrderSide
from gte_py.configs import TESTNET_CONFIG

MARKET_ADDRESS: ChecksumAddress = AsyncWeb3.to_checksum_address("0x5ca9f32d4ce7cc0f782213c446c2ae14b754a623")
# BTC CLOB: 0x0F3642714B9516e3d17a936bAced4de47A6FFa5F
# ETH CLOB: 0x5ca9f32d4ce7cc0f782213c446c2ae14b754a623


async def main():
    config = TESTNET_CONFIG
    weth_address = config.weth_address
    if not weth_address:
        raise ValueError("WETH address not configured")
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        market = await client.info.get_market(MARKET_ADDRESS)
        print(market)
        print('-' * 50)
        
        eth_amount = 0.001
        
        # if using an eth clob market you have to wrap before selling eth and unwrap after buying eth
        order = await client.execution.place_market_order(
            market=market,
            side=OrderSide.BUY,
            amount=Decimal(eth_amount),
            slippage=0.05,
        )
        
        print(f"Order posted: {order}")
        print('-' * 50)
        
        # or if you want to use amount in base units
        order = await client.execution.place_market_order(
            market=market,
            side=OrderSide.BUY,
            amount=Decimal(eth_amount),
            slippage=0.05,
        )
        
        # unwrap weth
        weth_balance = await client.execution.get_weth_balance()
        if weth_balance > 0:
            _ = await client.execution.unwrap_eth(amount=weth_balance)

        print(f"Order posted: {order}")
        
    return


if __name__ == "__main__":
    asyncio.run(main())
