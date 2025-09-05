"""Example of placing a market and limit order on a BTC market."""
from decimal import Decimal
import sys
sys.path.append(".")
import asyncio
from eth_utils.address import to_checksum_address
from hexbytes import HexBytes

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.api.chain.structs import TiF, Side
from examples.utils import WALLET_PRIVATE_KEY, print_separator

async def main():
    config = TESTNET_CONFIG
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        # approve capUSD for perp manager
        capUSD_address = to_checksum_address("0xe9b6e75c243b6100ffcb1c66e8f78f96feea727f")
        
        # capUSD = await client.execution.get_erc20(capUSD_address)
        # await client.execution.approve_token(capUSD, config.perp_manager_address)

        # # deposit capUSD to perp manager
        # await client.execution.perp_deposit(10**18 * 5 * 10**6) # 5 million capUSD

        market_name = "FAKEBTC-USD"
        # convert to bytes32 and pad to 32 bytes
        market_id = market_name.encode("utf-8").ljust(32, b"\0")
        market_id = HexBytes(market_id.hex())
        print(market_id)

        # cancel all existing orders
        # cancel_response = await client.execution.perp_cancel_limit_orders(market_id, subaccount=1, order_ids=[71])
        # print(cancel_response)

        mark_price = await client.execution.perp_get_mark_price(market_id)
        print_separator(f"Mark price: {mark_price / 10**18}")


        # buy .2 btc
        # await client.execution.perp_place_order(market_id, Side.SELL, Decimal(0.019), Decimal(100_000), subaccount=1, tif=TiF.IOC)

        # update leverage
        await client.execution.perp_update_leverage(market_id, subaccount=1, leverage=Decimal(1))
        position = await client.execution.perp_get_position(market_id, subaccount=1)
        print_separator("Position Details")
        print(f"Is Long: {position[0]}")
        print(f"Amount: {position[1] / 10**18:.6f} BTC")
        print(f"Open Notional: {position[2] / 10**18:.2f} USD")
        print(f"Current Leverage: {position[3] / 10**18:.1f}x")
        print(f"Last Cumulative Funding: {position[4] / 10**18:.6f}")

        # get my margin balance
        margin_balance = await client.execution.perp_get_margin_balance(1)
        print_separator(f"Margin balance: {margin_balance / (10**18)}")
        

if __name__ == "__main__":
    asyncio.run(main())