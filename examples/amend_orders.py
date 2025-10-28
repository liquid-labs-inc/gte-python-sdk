"""Example of amending an order with the GTE client."""
import sys
sys.path.append(".")
import asyncio
from decimal import Decimal

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.api.chain.structs import Side, TiF

from examples.utils import WALLET_PRIVATE_KEY
from examples.constants import BTC_USD_CLOB

MARKET_ADDRESS = BTC_USD_CLOB


async def main() -> None:
    """Run the on-chain trading examples."""
    config = TESTNET_CONFIG

    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        market = await client.info.get_market(MARKET_ADDRESS)
        
        # Place a limit order of 1 BTC at $50,000 per BTC
        order = await client.execution.spot_place_order(
            market_address=market.address,
            side=Side.BUY,
            amount=Decimal("1.0"),
            price=Decimal("50_000.0"),
            time_in_force=TiF.GTC,
            return_order=True
        )
        
        print(f"Placed order: {order}")
        await asyncio.sleep(5)
        
        # Since the price is low, we need to amend the order to $100,000 per BTC
        amended_order = await client.execution.spot_amend_order(
            market_address=market.address,
            order_id=int(order.get('args', {}).get('orderId', 0)),
            side=Side.BUY,
            new_amount=Decimal("1.0"),
            new_price=Decimal("100_000.0"),
        )
        print(f"Amended order: {amended_order}")


if __name__ == "__main__":
    asyncio.run(main())
