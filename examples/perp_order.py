"""Example of placing a market and limit order on a BTC market."""
from decimal import Decimal
import sys
sys.path.append(".")
import asyncio
from eth_utils.address import to_checksum_address
from hexbytes import HexBytes

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce
from examples.utils import WALLET_PRIVATE_KEY, print_separator

async def main():
    config = TESTNET_CONFIG
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        # approve capUSD for perp manager
        capUSD_address = to_checksum_address("0xe9b6e75c243b6100ffcb1c66e8f78f96feea727f")
        
        capUSD = await client.execution.get_erc20(capUSD_address)
        await client.execution.approve_token(capUSD, config.perp_manager_address)

        # deposit capUSD to perp manager
        await client.execution.perp_deposit(10**18 * 10**6) # 1 million capUSD

        market_name = "FAKEBTC-USD"
        # convert to bytes32 and pad to 32 bytes
        market_id = market_name.encode("utf-8").ljust(32, b"\0")
        market_id = HexBytes(market_id)
        
        # place a limit order
        order = await client.execution.perp_place_limit_order(market_id, OrderSide.BUY, 10**17, 10**20, subaccount=1)
        print_separator(f"Limit order placed: {order}")
        
        

if __name__ == "__main__":
    asyncio.run(main())