"""Example of placing an order on a WETH market."""
import sys
sys.path.append(".")
import asyncio
from decimal import Decimal
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from examples.utils import WALLET_PRIVATE_KEY
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.constants import LAUNCHPAD_TOKEN_ADDRESS

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        launch_data = await client.info.get_market(LAUNCHPAD_TOKEN_ADDRESS)
        print(launch_data)
        
        eth_amount = Decimal("0.001")
        
        order = await client.execution.launchpad_buy_exact_quote(
            launch_token=launch_data.base,
            quote_token=launch_data.quote,
            quote_amount_in=Decimal(eth_amount),
            slippage_tolerance=0.05,
        )
        print(f"Order posted: {order}")
        print('-' * 50)
        
        # get quote for base amount to sell to get quote amount
        quote = await client.execution.get_launchpad_quote_buy(
            launch_token=launch_data.base,
            quote_token=launch_data.quote,
            quote_amount=eth_amount,
        )
        print(f"Quote: {quote}")

        # sell base amount (launch token)to get quote amount
        order = await client.execution.launchpad_sell_exact_base(
            launch_token=launch_data.base,
            quote_token=launch_data.quote,
            base_amount_in=quote[0],
            slippage_tolerance=0.05,
        )
        
        print(f"Order posted: {order}")
        print('-' * 50)
        
        # unwrap weth if you want to get eth back
        weth_balance = await client.execution.get_weth_balance()
        if weth_balance > 0:
            _ = await client.execution.unwrap_eth(amount=weth_balance)
        
    return


if __name__ == "__main__":
    asyncio.run(main())
