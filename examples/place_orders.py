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

        # # approve capUSD for account manager
        # capUSD_address = to_checksum_address("0xe9b6e75c243b6100ffcb1c66e8f78f96feea727f")
        # await client.execution.approve_token(capUSD_address, config.account_manager_address)

        # # withdraw capUSD from perp manager
        # tx = await client.execution.perp_withdraw(amount=Decimal(10**6))
        # print(tx)

        side = Side.SELL
        size = Decimal('0.001')
        market_address = to_checksum_address("0x120637A748B07D99f86Ce2357CA720F299dB198E")
        
        # # Place a market order
        for i in range(20):
            order = await client.execution.spot_place_order(market_address, side, size, price=Decimal(100_000+i), time_in_force=TiF.GTC)
        
            print_separator(f"Market order placed: {order}")
        side = Side.BUY
        order = await client.execution.spot_place_order(market_address, side, size*5, price=Decimal(0), time_in_force=TiF.IOC)
        print_separator(f"Market order placed: {order}")
        order = await client.execution.spot_place_order(market_address, side, size*5, price=Decimal(0), time_in_force=TiF.IOC)
        print_separator(f"Market order placed: {order}")

        await asyncio.sleep(1)

        best_bid, best_ask = await client.execution.get_tob(market_address)
        print(f"Best bid: {best_bid}, Best ask: {best_ask}")

        # Place a limit order
        # order = await client.execution.spot_place_order(market, side, size, price, time_in_force=TiF.GTC)
        
        # print_separator(f"Limit order placed: {order}")

if __name__ == "__main__":
    asyncio.run(main())