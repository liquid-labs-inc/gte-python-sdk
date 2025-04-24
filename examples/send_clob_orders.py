"""Example of on-chain trading with the GTE client."""

import asyncio
import os

from dotenv import load_dotenv
from eth_typing import HexStr
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce, Market

# Load environment variables from .env file
load_dotenv()

# Configure these variables through environment or directly
WALLET_ADDRESS = Web3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
WALLET_PRIVATE_KEY = HexStr(os.getenv("WALLET_PRIVATE_KEY"))
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS", "0xfaf0BB6F2f4690CA4319e489F6Dc742167B9fB10")  # MEOW/WETH


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def get_market_info(client, market_address):
    """Get market information."""
    if not market_address:
        raise ValueError("No market address provided. Set MARKET_ADDRESS in .env file.")

    print(f"Using configured market: {market_address}")
    market = client.get_market(market_address)

    print(f"Market: {market.pair}")
    print(f"Base token: {market.base_asset.symbol} ({market.base_token_address})")
    print(f"Quote token: {market.quote_asset.symbol} ({market.quote_token_address})")
    print(f"Tick size: {market.tick_size} {market.tick_size_in_quote}")
    print(f"Lot size: {market.lot_size} {market.lot_size_in_base}")

    return market


async def approve_and_deposit_example(client: Client, web3, market, amount):
    """Example of approving and depositing WETH to the exchange."""
    print_separator("Approve and Deposit WETH Example")

    # Get the quote token address (assuming it's WETH for this example)
    token_address = market.quote_token_address
    print(f"Creating transaction to approve and deposit {amount} {market.quote_asset.symbol}...")

    # Get deposit transactions - this returns a list containing [approve_tx, deposit_tx]
    tx_funcs = await client.deposit_to_market(
        token_address=token_address,
        amount=amount,
        gas=100000,
    )

    print("\nSending approval transaction...")
    approve_receipt = tx_funcs[0].send_wait(WALLET_PRIVATE_KEY)

    print("\nSending deposit transaction...")
    deposit_receipt = tx_funcs[1].send_wait(WALLET_PRIVATE_KEY)

    return approve_receipt, deposit_receipt


async def limit_order_example(client: Client, web3, market):
    """Example of creating a limit order."""
    print_separator("Limit Order Example")

    # Current market price (or estimate)
    price = market.price or market.tick_size
    amount = market.lot_size

    print(f"Limit order price: {price}")

    tx_func = await client.place_limit_order(
        market=market,
        side=OrderSide.BUY,
        amount=amount,
        price=price,
        time_in_force=TimeInForce.IOC,
    )

    print("\nSending transaction...")
    receipt = tx_func.send_wait(WALLET_PRIVATE_KEY)
    print(receipt)

    tx_func = await client.place_limit_order(
        market=market,
        side=OrderSide.SELL,
        amount=amount,
        price=price,
        time_in_force=TimeInForce.GTC,
    )
    print("\nSending transaction...")
    receipt = tx_func.send_wait(WALLET_PRIVATE_KEY)
    print(receipt)


async def cancel_order_example(client, web3, market, order_id=None, send_tx=False):
    """Example of cancelling an order."""
    print_separator("Cancel Order Example")

    # Use provided order ID or a fictional one
    order_id = order_id or 12345

    print(f"Creating cancel transaction for order ID {order_id}...")

    tx_func = await client.cancel_order(
        market=market,
        order_id=order_id,
        gas=200000,
    )

    print("\nSending transaction...")
    receipt = tx_func.send_wait(WALLET_PRIVATE_KEY)
    return receipt


async def show_balances(client: Client, market: Market):
    """Example of getting token balances."""
    print_separator("Token Balances Example")

    # Get balances for base and quote tokens
    base_token = market.base_token_address
    quote_token = market.quote_token_address

    print(f"Getting balances for {market.base_asset.symbol} and {market.quote_asset.symbol}...")

    base_wallet, base_exchange = await client.get_balance(base_token)
    quote_wallet, quote_exchange = await client.get_balance(quote_token)

    print(f"{market.base_asset.symbol} balances:")
    print(f"  Wallet: {base_wallet:.6f}")
    print(f"  Exchange: {base_exchange:.6f}")

    print(f"{market.quote_asset.symbol} balances:")
    print(f"  Wallet: {quote_wallet:.6f}")
    print(f"  Exchange: {quote_exchange:.6f}")


async def main():
    """Run the on-chain trading examples."""
    network = TESTNET_CONFIG

    print("Initializing Web3...")
    web3 = Web3(Web3.HTTPProvider(network.rpc_http))

    print("Connected to blockchain:")
    print(f"Chain ID: {web3.eth.chain_id}")

    # Initialize client with Web3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, sender_address=WALLET_ADDRESS)

    # Get a market to work with
    market = await get_market_info(client, MARKET_ADDRESS)

    # Show balances
    await show_balances(client, market)

    # Run the examples (set send_tx=True to actually send transactions)
    send_tx = True  # Safety default - change to True to send transactions

    print("\nNOTE: For WETH wrapping and unwrapping examples, see wrap_weth.py")

    # Deposit tokens example
    await approve_and_deposit_example(client, web3, market, amount=1)

    await show_balances(client, market)
    # Order examples
    await limit_order_example(client, web3, market)

    await cancel_order_example(client, web3, market, order_id=None, send_tx=send_tx)


if __name__ == "__main__":
    asyncio.run(main())
