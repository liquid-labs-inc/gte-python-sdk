"""Example of placing a market and limit order on a BTC market."""
from decimal import Decimal
import sys
sys.path.append(".")
import asyncio
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce
from examples.utils import WALLET_PRIVATE_KEY, print_separator

# BTC CLOB
MARKET_ADDRESS = to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        
        side = OrderSide.BUY
        size = Decimal('0.01')
        
        market = await client.info.get_market(MARKET_ADDRESS)
        
        # Place a market order
        order = await client.execution.place_market_order(market, side, size, slippage=0.05)
        
        print_separator(f"Market order placed: {order}")
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
        order = await client.execution.place_limit_order(market, side, size, price, time_in_force=TimeInForce.GTC)
        
        print_separator(f"Limit order placed: {order}")

if __name__ == "__main__":
    asyncio.run(main())