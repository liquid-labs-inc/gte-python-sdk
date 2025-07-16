"""Example of placing a market and limit order on a BTC market."""
import sys
sys.path.append(".")
import asyncio
from eth_utils.address import to_checksum_address
import time
import logging
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market, OrderSide, TimeInForce
from examples.utils import WALLET_PRIVATE_KEY
import cProfile
import pstats


MARKET_ADDRESS = to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")

def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        
        side = OrderSide.BUY
        size = 0.01
        
        market = await client.info.get_market(MARKET_ADDRESS)
        
        # Place a market order
        order = await client.execution.place_market_order(market, side, size, amount_is_raw=False, slippage=0.05, gas=50 * 10 ** 6)
        
        print_separator(f"Market order placed: {order}")
        
        order_book = await client.info.get_order_book(MARKET_ADDRESS)
        print(order_book)
        
        if side == OrderSide.BUY:
            # For BUY orders, use the best ask price (lowest selling price)
            price = market.quote.convert_quantity_to_amount(float(order_book['bids'][0]['price'])-10)
        else:
            # For SELL orders, use the best bid price (highest buying price)
            price = market.quote.convert_quantity_to_amount(float(order_book['asks'][0]['price'])+10)
        
        print(f"TOB Price: {price}")
        
        # Place a limit order
        order = await client.execution.place_limit_order(market, side, size, price, amount_is_raw=False, time_in_force=TimeInForce.GTC, gas=50 * 10 ** 6)
        
        print_separator(f"Limit order placed: {order}")
    

if __name__ == "__main__":
    asyncio.run(main())