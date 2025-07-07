"""Example of amending an order with the GTE client."""
import sys
sys.path.append(".")
import asyncio

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce

from examples.utils import WALLET_PRIVATE_KEY

MARKET_ADDRESS = "0x0F3642714B9516e3d17a936bAced4de47A6FFa5F"


async def main() -> None:
    """Run the on-chain trading examples."""
    config = TESTNET_CONFIG

    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        market = await client.info.get_market(MARKET_ADDRESS)
        
        # Place a limit order of 1 BTC at $50,000 per BTC
        order = await client.execution.place_limit_order(
            market=market,
            side=OrderSide.BUY,
            amount= 10**18,
            price=market.quote.convert_quantity_to_amount(50_000.0),
            time_in_force=TimeInForce.GTC,
            gas=50 * 10**6
        )
        
        print(f"Placed order: {order}")
        
        # Wait for 5 seconds
        await asyncio.sleep(5)
        
        # Since the price is low, we need to amend the order to $100,000 per BTC
        amended_order = await client.execution.amend_order(
            market=market,
            order_id=order.order_id,
            new_price=market.quote.convert_quantity_to_amount(100_000.0),
            gas=50 * 10**6
        )
        print(f"Amended order: {amended_order}")


if __name__ == "__main__":
    asyncio.run(main())
