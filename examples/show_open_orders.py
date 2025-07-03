"""Example of on-chain trading with the GTE client."""
import asyncio
import os
import logging
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.api.rest.utils import paged_request

from examples.utils import display_market_info

WALLET_ADDRESS = to_checksum_address("0x95a1190b12f553A9c04cB36b76E3d0150E72770d")

MARKET_ADDRESS = to_checksum_address("0x0F3642714B9516e3d17a936bAced4de47A6FFa5F")

async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config) as client:
        _ = await display_market_info(client, MARKET_ADDRESS)
        open_orders = await paged_request(
            lambda limit, offset: client.info.get_user_open_orders(WALLET_ADDRESS, MARKET_ADDRESS, limit=limit, offset=offset), 50, 1000)
        print("Opening orders:")
        for open_order in open_orders:
            print(
                f"Order ID: {open_order['orderId']}, Price: {open_order['limitPrice']}, Amount: {open_order['originalSize']}, Side: {open_order['side']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
