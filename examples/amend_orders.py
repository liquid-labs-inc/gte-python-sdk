"""Example of on-chain trading with the GTE client."""
import sys
sys.path.append(".")
import asyncio
import logging

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market, OrderSide, TimeInForce

from examples.utils import (
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
)

MARKET_ADDRESS = "0x0F3642714B9516e3d17a936bAced4de47A6FFa5F"

async def main() -> None:
    """Run the on-chain trading examples."""
    config = TESTNET_CONFIG

    async with GTEClient(config=config, wallet_address=WALLET_ADDRESS, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        raw_market = await client.info.get_market(MARKET_ADDRESS)
        market = Market.from_api(raw_market)       
        
        # place a low limit order
        order = await client.execution.place_limit_order(
            market=market,
            side=OrderSide.BUY,
            amount= 10**18,
            price=market.quote.convert_quantity_to_amount(50_000.0),
            time_in_force=TimeInForce.GTC,
            gas=50 * 10**6
        )
        
        print(f"Placed order: {order}")
        
        await asyncio.sleep(5)
        
        # Price is only 1000, so we need to amend the order
        amended_order = await client.execution.amend_order(
            market=market,
            order_id=order.order_id,
            new_price=market.quote.convert_quantity_to_amount(100_000.0),
            gas=50 * 10**6
        )
        print(f"Amended order: {amended_order}")


if __name__ == "__main__":
    asyncio.run(main())
