"""Example of placing a market and limit order on a BTC market."""
from decimal import Decimal
import sys

from eth_account import account
sys.path.append(".")
import asyncio

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce
from examples.utils import WALLET_ADDRESS, print_separator
from examples.constants import BTC_USD_CLOB

async def main():
    config = TESTNET_CONFIG

    
    async with GTEClient(config=config, wallet_address=WALLET_ADDRESS) as client:
        
        side = OrderSide.BUY
        size = Decimal('0.01')
        
        market = await client.info.get_market(BTC_USD_CLOB)
        
        # Place a market order
        order = await client.execution.place_market_order(market, side, size, slippage=0.05, return_built_tx=True)
        print(order)
        
        best_bid, best_ask = await client.execution.get_tob(market)
        print(f"Best bid: {best_bid}, Best ask: {best_ask}")    
        
        if side == OrderSide.BUY:
            # For BUY orders, use the best bid price (highest buying price)
            price = best_bid+1
        else:
            # For SELL orders, use the best ask price (lowest selling price)
            price = best_ask-1
        
        print(f"TOB Price: {price}")

        # Place a limit order
        order = await client.execution.place_limit_order(market, side, size, price, time_in_force=TimeInForce.GTC, return_built_tx=True)
        print(order)

if __name__ == "__main__":
    asyncio.run(main())