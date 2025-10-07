"""Example of placing a market and limit order on a BTC market."""
from decimal import Decimal
import sys
sys.path.append(".")
from eth_account import Account
from web3 import Web3
import asyncio
from eth_utils.address import to_checksum_address
from eth_account.types import TransactionDictType
from typing import cast
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import WALLET_ADDRESS, WALLET_PRIVATE_KEY, print_separator
from gte_py.api.chain.structs import TiF, Side
from examples.constants import BTC_USD_CLOB

async def main():
    config = TESTNET_CONFIG

    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        # deposit tokens to AM
        tx = await client.execution.account_deposit(token=to_checksum_address("0xba881A0b1B01aBc545Ad80eB0D9bdD837e22D05f"), amount=int(Decimal(10**18) * (10**18)))
        print(tx)

        side = Side.BUY
        size = Decimal('0.01')
        
        market = await client.info.get_market("0xba881A0b1B01aBc545Ad80eB0D9bdD837e22D05f")
        
        # Place a market order
        order = await client.execution.spot_place_order(market, side, size, price=Decimal(0), time_in_force=TiF.GTC)
        
        print_separator(f"Market order placed: {order}")
        best_bid, best_ask = await client.execution.get_tob(market)
        print(f"Best bid: {best_bid}, Best ask: {best_ask}")    
        
        if side == Side.BUY:
            # For BUY orders, use the best bid price (highest buying price)
            price = best_bid+1
        else:
            # For SELL orders, use the best ask price (lowest selling price)
            price = best_ask-1
        
        print(f"TOB Price: {price}")

        # Place a limit order
        order = await client.execution.spot_place_order(market, side, size, price, time_in_force=TiF.GTC)
        
        print_separator(f"Limit order placed: {order}")

if __name__ == "__main__":
    asyncio.run(main())