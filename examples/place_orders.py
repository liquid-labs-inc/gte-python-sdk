import asyncio
import os
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market, OrderSide, TimeInForce

load_dotenv()

WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")

if not WALLET_ADDRESS_RAW or not WALLET_PRIVATE_KEY_RAW:
    raise ValueError("Missing wallet credentials")

WALLET_ADDRESS: ChecksumAddress = to_checksum_address(WALLET_ADDRESS_RAW)
WALLET_PRIVATE_KEY: HexStr = HexStr(WALLET_PRIVATE_KEY_RAW)

MARKET_ADDRESS = to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")

def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_address=WALLET_ADDRESS, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        side = OrderSide.BUY
        
        # 0.01 BTC
        size = 10 ** 16
        
        market = Market.from_api(await client.info.get_market(MARKET_ADDRESS))
        
        # Place a market order
        order = await client.execution.place_market_order(market, side, size, slippage=0.05, gas=50 * 10 ** 6)
        
        print_separator(f"Market order placed: {order}")
        
        order_book = await client.info.get_order_book(MARKET_ADDRESS)
        
        if side == OrderSide.BUY:
            price = market.quote.convert_quantity_to_amount(float(order_book['bids'][0]['price']))
        else:
            price = market.quote.convert_quantity_to_amount(float(order_book['asks'][0]['price']))
        
        print(f"TOB Price: {price}")
        
        # Place a limit order
        order = await client.execution.place_limit_order(market, side, size, price, time_in_force=TimeInForce.GTC, gas=50 * 10 ** 6)
        
        print_separator(f"Limit order placed: {order}")
    
    return
    

if __name__ == "__main__":
    asyncio.run(main())
