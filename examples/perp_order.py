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

        # deposit capUSD to perp manager
        # tx = await client.execution.perp_deposit(Decimal(10**6)) # 1 million capUSD
        # print(tx)
        # add margin
        # check perp account balance
        perp_account_balance = await client.execution._chain_client.perp_manager.get_free_collateral_balance(client.execution.wallet_address)
        print_separator(f"Perp account balance: {perp_account_balance / (10**18)}")
        # i have 3 million capUSD in free collateral 

        # tx = await client.execution.perp_add_margin(subaccount=1, amount=Decimal(10**6))
        # print(tx)
        # contract_func = client.execution._chain_client.perp_manager.add_margin(account=client.execution.wallet_address, subaccount=1, amount=(3*10**6)* (10 **18))
        # tx = await client.execution._scheduler.send(contract_func)
        # print(tx)

        market_name = "FAKEBTC"
        # convert to bytes32 and pad to 32 bytes
        market_id = market_name.encode("utf-8").ljust(32, b"\0")
        market_id = HexBytes(market_id.hex())
        print(market_id)

        # add margin to subaccount 1
        tx = await client.execution.perp_add_margin(subaccount=1, amount=Decimal(10**5))
        print(tx)

        await asyncio.sleep(1)

        # get margin balance
        margin_balance = await client.execution.perp_get_margin_balance(1)
        print_separator(f"Margin balance: {margin_balance / (10**18)}")

        # check if market is active
        market_status = await client.execution._chain_client.perp_manager.get_market_status(market_id)
        print_separator(f"Market status: {market_status}")

        # cancel all existing orders
        # cancel_response = await client.execution.perp_cancel_limit_orders(market_id, subaccount=1, order_ids=[71])
        # print(cancel_response)

        # Check if market exists and get its status

        mark_price = await client.execution.perp_get_mark_price(market_id)
        print_separator(f"Mark price: {mark_price / 10**18}")

        # Check margin balance before placing order
        margin_balance = await client.execution.perp_get_margin_balance(0)
        print_separator(f"Margin balance before order: {margin_balance / (10**18)}")

        # buy .1 btc at $100,000 (much higher than mark price to ensure it's a limit order)
        tx = await client.execution.perp_place_order(market_id, Side.SELL, Decimal(0.1), Decimal(100_000), subaccount=1, tif=TiF.GTC)
        print(tx)
        print("✅ Order placed successfully!")

        # update leverage
        await client.execution.perp_update_leverage(market_id, subaccount=0, leverage=Decimal(1))
        position = await client.execution.perp_get_position(market_id, subaccount=1)
        print_separator("Position Details")
        print(f"Is Long: {position[0]}")
        print(f"Amount: {position[1] / 10**18:.6f} BTC")
        print(f"Open Notional: {position[2] / 10**18:.2f} USD")
        print(f"Current Leverage: {position[3] / 10**18:.1f}x")
        print(f"Last Cumulative Funding: {position[4] / 10**18:.6f}")

        # get my margin balance
        margin_balance = await client.execution.perp_get_margin_balance(0)
        print_separator(f"Margin balance: {margin_balance / (10**18)}")
        

if __name__ == "__main__":
    asyncio.run(main())