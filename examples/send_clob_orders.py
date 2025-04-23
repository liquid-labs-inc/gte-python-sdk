"""Example of on-chain trading with the GTE client."""

import asyncio
import os
from decimal import Decimal

from dotenv import load_dotenv
from eth_typing import ChecksumAddress
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.models import OrderSide, OrderType, TimeInForce

# Load environment variables from .env file
load_dotenv()

# Configure these variables through environment or directly
WALLET_ADDRESS = Web3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
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
    print(f"Tick size: {market.tick_size}")
    
    return market


async def sign_and_send_tx(web3, tx, private_key):
    """Sign and send a transaction."""
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent: {web3.to_hex(tx_hash)}")
    
    # Wait for transaction receipt
    receipt = await wait_for_transaction(web3, tx_hash)
    print(f"Transaction confirmed in block {receipt['blockNumber']}")
    print(f"Gas used: {receipt['gasUsed']}")
    
    return receipt


async def wait_for_transaction(web3, tx_hash, timeout=120):
    """Wait for a transaction to be mined."""
    start_time = asyncio.get_event_loop().time()
    while True:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt is not None:
                return receipt
        except Exception:
            pass
        
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"Transaction not mined after {timeout} seconds")
        
        await asyncio.sleep(2)


async def limit_order_example(client, web3, market, send_tx=False):
    """Example of creating a limit order."""
    print_separator("Limit Order Example")

    # Current market price (or estimate)
    price = market.price or 100.0
    # Place a bid 5% below current price
    bid_price = price * 0.95
    
    print(f"Current market price: {price}")
    print(f"Creating limit buy order at price: {bid_price}")

    tx_func = await client.place_limit_order(
        market=market,
        side=OrderSide.BUY,
        amount=0.01,  # Small amount for testing
        price=bid_price,
        time_in_force=TimeInForce.GTC,
        gas=300000,
    )

    # Convert to transaction dictionary
    tx = tx_func.build_transaction()
    
    print("Transaction created:")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    if send_tx and WALLET_PRIVATE_KEY:
        print("\nSending transaction...")
        receipt = await sign_and_send_tx(web3, tx, WALLET_PRIVATE_KEY)
        return receipt
    else:
        print("\nNOTE: This is a demonstration only. No transaction was sent.")
        print("Set send_tx=True and provide WALLET_PRIVATE_KEY to send transactions.")
        return None


async def market_order_example(client, web3, market, send_tx=False):
    """Example of creating a market order."""
    print_separator("Market Order Example")

    # Current market price (or estimate)
    price = market.price or 100.0
    
    print(f"Current market price: {price}")
    print(f"Creating market buy order")

    tx_func = await client.place_market_order(
        market=market,
        side=OrderSide.BUY,
        amount=0.01,  # Small amount for testing
        amount_is_base=True,
        gas=300000,
    )

    # Convert to transaction dictionary
    tx = tx_func.build_transaction()
    
    print("Transaction created:")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    if send_tx and WALLET_PRIVATE_KEY:
        print("\nSending transaction...")
        receipt = await sign_and_send_tx(web3, tx, WALLET_PRIVATE_KEY)
        return receipt
    else:
        print("\nNOTE: This is a demonstration only. No transaction was sent.")
        print("Set send_tx=True and provide WALLET_PRIVATE_KEY to send transactions.")
        return None


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

    # Convert to transaction dictionary
    tx = tx_func.build_transaction()
    
    print("Transaction created:")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    if send_tx and WALLET_PRIVATE_KEY:
        print("\nSending transaction...")
        receipt = await sign_and_send_tx(web3, tx, WALLET_PRIVATE_KEY)
        return receipt
    else:
        print("\nNOTE: This is a demonstration only. No transaction was sent.")
        print("Set send_tx=True and provide WALLET_PRIVATE_KEY to send transactions.")
        return None


async def show_balances_example(client, market):
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

    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC node at {network.rpc_http}")

    print("Connected to blockchain:")
    print(f"Chain ID: {web3.eth.chain_id}")

    # Initialize client with Web3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, sender_address=WALLET_ADDRESS)

    # Get a market to work with
    market = await get_market_info(client, MARKET_ADDRESS)

    # Show balances
    await show_balances_example(client, market)

    # Run the examples (set send_tx=True to actually send transactions)
    send_tx = False  # Safety default - change to True to send transactions
    
    # Example: Place a limit order
    limit_receipt = await limit_order_example(client, web3, market, send_tx)
    
    # If the limit order was sent and mined, we'll have the receipt with the order ID
    # For now, we'll continue with the examples
    
    # Example: Place a market order
    market_receipt = await market_order_example(client, web3, market, send_tx)
    
    # Example: Cancel an order
    # We could extract the order ID from the limit order receipt if we had it
    cancel_receipt = await cancel_order_example(client, web3, market, order_id=None, send_tx=send_tx)


if __name__ == "__main__":
    asyncio.run(main())
