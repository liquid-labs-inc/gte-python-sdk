"""Example of placing a market and limit order on a BTC market."""
import sys
sys.path.append(".")
import asyncio
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market, OrderSide, TimeInForce
from examples.utils import WALLET_PRIVATE_KEY

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
        
        # 0.01 BTC
        size = 10 ** 16
        
        
        market = await client.info.get_market(MARKET_ADDRESS)
        
        # Place a market order
        order = await client.execution.place_market_order(market, side, size, slippage=0.05, gas=50 * 10 ** 6)
        
        print_separator(f"Market order placed: {order}")
        
        order_book = await client.info.get_order_book(MARKET_ADDRESS)
        print(order_book)
        
        if side == OrderSide.BUY:
            # For BUY orders, use the best ask price (lowest selling price)
            price = market.quote.convert_quantity_to_amount(float(order_book['bids'][0]['price'])-1000)
        else:
            # For SELL orders, use the best bid price (highest buying price)
            price = market.quote.convert_quantity_to_amount(float(order_book['asks'][0]['price'])+1000)
        
        print(f"TOB Price: {price}")
        token = client.execution._token_client.get_erc20(market.quote.address)
        # approve quote token
        
        
        # Place a limit order
        order = await client.execution.place_limit_order(market, side, size, price, time_in_force=TimeInForce.GTC, gas=50 * 10 ** 6)
        
        print_separator(f"Limit order placed: {order}")
    
    return
    

if __name__ == "__main__":
    asyncio.run(main())
