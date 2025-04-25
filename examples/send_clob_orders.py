"""Example of on-chain trading with the GTE client."""

import asyncio
import logging
from eth_typing import HexStr
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce, Market, Order

from utils import (
    print_separator, 
    display_market_info, 
    show_balances, 
    WALLET_ADDRESS, 
    WALLET_PRIVATE_KEY, 
    MARKET_ADDRESS
)


async def approve_and_deposit_example(client: Client, market, amount):
    """Example of approving and depositing tokens to the exchange."""
    print_separator("Approve and Deposit Tokens Example")

    # Get the quote token address
    quote = market.quote_token_address
    print(f"Creating transaction to approve and deposit {amount} {market.quote_asset.symbol}...")

    # Get deposit transactions - this returns a list containing [approve_tx, deposit_tx]
    tx_funcs = await client.deposit_to_market(
        token_address=quote,
        amount=amount,
        gas=100000,
    )

    print("\nSending approval transaction...")
    tx_funcs[0].send_wait(WALLET_PRIVATE_KEY)

    print("\nSending deposit transaction...")
    tx_funcs[1].send_wait(WALLET_PRIVATE_KEY)

    # Now deposit the base token
    base = market.base_token_address
    print(f"Creating transaction to approve and deposit {amount} {market.base_asset.symbol}...")
    tx_funcs = await client.deposit_to_market(
        token_address=base,
        amount=amount,
        gas=100000,
    )
    
    print("\nSending approval transaction...")
    tx_funcs[0].send_wait(WALLET_PRIVATE_KEY)
    
    print("\nSending deposit transaction...")
    tx_funcs[1].send_wait(WALLET_PRIVATE_KEY)


async def limit_order_example(client: Client, market):
    """Example of creating a limit order."""
    print_separator("Limit Order Example")

    # Current market price (or estimate)
    price = market.price or market.tick_size
    amount = market.lot_size

    print(f"Creating BUY limit order at price: {price}")
    tx_func = await client.place_limit_order(
        market=market,
        side=OrderSide.BUY,
        amount=amount,
        price=price,
        time_in_force=TimeInForce.GTC,
    )

    order = tx_func.send_wait(WALLET_PRIVATE_KEY)
    print(f"Order created: {order}")
    await get_order_status(client, market, order.order_id)

    print(f"Creating SELL limit order at price: {price}")
    tx_func = await client.place_limit_order(
        market=market,
        side=OrderSide.SELL,
        amount=amount,
        price=price,
        time_in_force=TimeInForce.GTC,
    )

    order = tx_func.send_wait(WALLET_PRIVATE_KEY)
    print(f"Order created: {order}")
    await get_order_status(client, market, order.order_id)


async def cancel_order_example(client, market, order_id=None):
    """Example of cancelling an order."""
    print_separator("Cancel Order Example")

    if not order_id:
        print("No order ID provided, using example ID")
        order_id = 12345

    print(f"Creating cancel transaction for order ID {order_id}...")
    tx_func = await client.cancel_order(
        market=market,
        order_id=order_id,
        gas=200000,
    )

    print("\nSending transaction...")
    receipt = tx_func.send_wait(WALLET_PRIVATE_KEY)
    return receipt


async def get_order_status(client: Client, market: Market, order_id: int):
    """Get the status of an order."""
    print_separator("Order Status Example")

    try:
        order = await client.get_order(market, order_id=order_id)

        print(f"Order ID: {order.order_id}")
        print(f"Market: {market.pair}")
        print(f"Side: {order.side.name}")
        print(f"Price: {order.price}")
        print(f"Amount: {order.amount}")
        print(f"Status: {getattr(order, 'status', 'N/A')}")

    except Exception as e:
        print(f"Couldn't fetch on-chain order status: {str(e)}")


async def show_orders(client: Client, market):
    """Show orders for the user."""
    print_separator("User Orders")

    try:
        orders = await client.get_orders(market_address=market.address)

        print(f"Orders for market {market.pair}:")
        for order in orders:
            print(f"  ID: {order.order_id}")
            print(f"  Side: {order.side.name}")
            print(f"  Price: {order.price}")
            print(f"  Size: {getattr(order, 'size', order.amount)}")
            print(f"  Status: {order.status.name if hasattr(order, 'status') else 'N/A'}")

    except Exception as e:
        print(f"Couldn't fetch on-chain orders: {str(e)}")
        print("This feature requires Web3 provider and a market with contract address")


async def main():
    """Run the on-chain trading examples."""
    network = TESTNET_CONFIG

    print("Initializing Web3...")
    web3 = Web3(Web3.HTTPProvider(network.rpc_http))

    print("Connected to blockchain:")
    print(f"Chain ID: {web3.eth.chain_id}")

    # Check for required environment variables
    if not WALLET_ADDRESS or not WALLET_PRIVATE_KEY:
        raise ValueError("WALLET_ADDRESS and WALLET_PRIVATE_KEY must be set in .env file")

    wallet_address = Web3.to_checksum_address(WALLET_ADDRESS)
    
    # Initialize client with Web3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, sender_address=wallet_address)

    try:
        # Get a market to work with
        market = await display_market_info(client, MARKET_ADDRESS)

        # Show balances
        await show_balances(client, market)

        print("\nNOTE: For WETH wrapping and unwrapping examples, see wrap_weth.py")

        # Deposit tokens example
        await approve_and_deposit_example(client, market, amount=1)

        # Check balances after deposit
        await show_balances(client, market)
        
        # Order examples
        await limit_order_example(client, market)

        # Cancel an order
        await cancel_order_example(client, market, order_id=None)
        
        # Show all orders
        await show_orders(client, market)
        
    except Exception as e:
        print(f"Error during examples: {str(e)}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
