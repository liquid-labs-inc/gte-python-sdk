"""Example of placing an order on a WETH market."""
import sys
sys.path.append(".")
import asyncio
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
import time
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
        
        eth_amount = 0.001
        eth_amount_wei = market.base.convert_quantity_to_amount(eth_amount)
        
        # if using an eth clob market you have to wrap before selling eth and unwrap after buying eth
        
        # wrap the eth
        weth_balance = await client.execution.get_weth_balance()
        if weth_balance < eth_amount_wei*2:
            await client.execution.wrap_eth(amount=eth_amount_wei*2 - weth_balance, gas=50 * 10**6)
        
        # buy eth
        # if you want to use quote units, you can set amount_is_base=False
        # amount is accepted in raw units (atoms, wei, etc.) unless you set amount_is_raw=False
        order = await client.execution.place_market_order(  # type: ignore
            market=market,
            side=OrderSide.BUY,
            amount=eth_amount_wei,
            slippage=0.05,
            gas=50 * 10**6
        )
        
        print(f"Order posted: {order}")
        print('-' * 50)
        
        # or if you want to use amount in base units
        order = await client.execution.place_market_order(  # type: ignore
            market=market,
            side=OrderSide.BUY,
            amount=eth_amount,
            amount_is_raw=False,
            slippage=0.05,
            gas=50 * 10**6
        )
        
        weth_balance = await client.execution.get_weth_balance()
        await client.execution.unwrap_eth(amount=weth_balance, gas=50 * 10**6)

        print(f"Order posted: {order}")
        
    return


if __name__ == "__main__":
    asyncio.run(main())
