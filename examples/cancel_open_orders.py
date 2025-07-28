"""Example of canceling open orders with the GTE client."""
import sys
sys.path.append(".")
import asyncio

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import WALLET_PRIVATE_KEY, WALLET_ADDRESS

from examples.constants import BTC_USD_CLOB

MARKET_ADDRESS = BTC_USD_CLOB


async def main():
    config = TESTNET_CONFIG
    weth_address = config.weth_address
    if not weth_address:
        raise ValueError("WETH address not configured")
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        open_orders = await client.info.get_user_open_orders(WALLET_ADDRESS, MARKET_ADDRESS)
        print(f"Open orders: {open_orders}")
        
        market = await client.info.get_market(MARKET_ADDRESS)
        
        # convert to order model
        for order in open_orders:
            print(await client.execution.cancel_order(market, int(order["orderId"]), gas=50 * 10**6))
        
        return
    
    
if __name__ == "__main__":
    asyncio.run(main())