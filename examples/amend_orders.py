"""Example of on-chain trading with the GTE client."""
import sys

from gte_py.api.chain.structs import Settlement

sys.path.append(".")
import asyncio
import logging

# from examples.utils import show_all_orders
from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce

from utils import (
    display_market_info,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
    MARKET_ADDRESS
)


async def main() -> None:
    """Run the on-chain trading examples."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")

    client = Client(web3=web3, config=network, account=WALLET_ADDRESS)
    await client.init()
    # Get a market to work with
    market = await display_market_info(client, MARKET_ADDRESS)

    bid, ask = await client.market.get_tob(market)
    bid_price = market.quote.convert_amount_to_quantity(bid)
    quantity = 20 / bid_price

    order = await client.execution.place_limit_order(
        market=market,
        side=OrderSide.BUY,
        amount=market.base.convert_quantity_to_amount(quantity),
        price=bid,
        time_in_force=TimeInForce.POST_ONLY,
        settlement=Settlement.ACCOUNT,
        gas=50 * 10000000
    )
    print(f"Placed order: {order.order_id} at price {bid * 0.8} for {quantity} {market.base.symbol}")
    amend_order = await client.execution.amend_order(
        market=market,
        order_id=order.order_id,
        new_price=bid,
        new_amount=market.base.convert_quantity_to_amount(quantity * 0.5),
        gas=50 * 10000000
    )
    print(f"Amended order: {amend_order.args['orderId']} to new price {bid} and amount {quantity * 2} {market.base.symbol}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
