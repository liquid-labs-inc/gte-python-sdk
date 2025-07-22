"""example of swapping towken on AMM"""
from decimal import Decimal
import sys
sys.path.append(".")
import asyncio
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import WALLET_PRIVATE_KEY

# BTC/ETH AMM
MARKET_ADDRESS = to_checksum_address("0x6bba3ff4b359392decd0b77239b7e795269fb550")

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        
        market = await client.info.get_market(MARKET_ADDRESS)
        print(market.quote)
        amount_in = Decimal('0.01')
        
        # get quote for amount in
        quote = await client.execution.get_swap_quote(
            token_in=market.base,
            token_out=market.quote,
            amount_in=amount_in,
        )
        print(quote)
        
        # use quote for exact amount out
        txn = await client.execution.swap_tokens_for_exact_output(
            token_in=market.base,
            token_out=market.quote,
            amount_out=quote[0],
            slippage_tolerance=0.001,
        )
        print(txn)
        
        # swap tokens
        txn = await client.execution.swap_tokens(
            token_in=market.base,
            token_out=market.quote,
            amount_in=amount_in,
            slippage_tolerance=0.05,
        )
        print(txn)


if __name__ == "__main__":
    asyncio.run(main())