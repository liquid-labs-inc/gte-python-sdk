"""Example of on-chain trading with the GTE client."""

import asyncio
import os

from dotenv import load_dotenv
from web3 import Web3

from gte_py import Client
from gte_py.contracts.iclob import ICLOB
from gte_py.models import OrderSide, OrderType, TimeInForce

# Load environment variables from .env file
load_dotenv()

# Configure these variables through environment or directly
RPC_URL = os.getenv("RPC_URL", "https://rpc-testnet.example.com")
ROUTER_ADDRESS = os.getenv("ROUTER_ADDRESS")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def check_config():
    """Check if required configuration is present."""
    missing = []
    if not RPC_URL or RPC_URL == "https://rpc-testnet.example.com":
        missing.append("RPC_URL")
    if not ROUTER_ADDRESS:
        missing.append("ROUTER_ADDRESS")
    if not WALLET_ADDRESS:
        missing.append("WALLET_ADDRESS")
    if not PRIVATE_KEY:
        missing.append("PRIVATE_KEY")

    if missing:
        print(f"Missing configuration: {', '.join(missing)}")
        print("Please set these in environment variables or .env file")
        return False
    return True


async def get_market_info(client):
    """Get market information."""
    if MARKET_ADDRESS:
        # Use specified market
        print(f"Using configured market: {MARKET_ADDRESS}")
        market = await client.get_market(MARKET_ADDRESS)
        return market

    # Try to get from on-chain markets
    try:
        print("Looking for on-chain markets...")
        markets = client.get_available_onchain_markets()
        if markets:
            print(f"Found {len(markets)} on-chain markets")
            return markets[0]
    except Exception as e:
        print(f"Error getting on-chain markets: {e}")

    # Fall back to API markets
    print("Looking for API markets...")
    markets = await client.get_markets(limit=10)
    if not markets:
        raise ValueError("No markets found")

    # Find a market with a contract address
    for market in markets:
        if market.contract_address:
            print(f"Found market with contract address: {market.address}")
            return market

    # Just use any market
    print("Using first available market")
    return markets[0]


async def sign_and_send_tx(web3, tx, private_key):
    """Sign and send a transaction."""
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent: {web3.to_hex(tx_hash)}")

    print("Waiting for transaction receipt...")
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"Transaction confirmed: Block {receipt['blockNumber']}")
    print(f"Gas used: {receipt['gasUsed']}")

    if receipt["status"] == 1:
        print("Transaction succeeded")
    else:
        print("Transaction failed")

    return receipt


async def deposit_example(client, web3, market):
    """Example of depositing tokens to CLOB."""
    print_separator("Deposit Example")

    if not market.contract_address:
        print("Market does not have a contract address")
        return

    # Get the CLOB contract
    clob = ICLOB(web3=web3, contract_address=market.contract_address)

    # Get the base token
    base_token = clob.get_base_token()
    print(f"Base token: {base_token}")

    # Create deposit transaction (for demonstration - don't actually send)
    deposit_amount = 0.1 * (10**market.base_decimals)  # 0.1 tokens
    print(f"Creating deposit transaction for {deposit_amount / (10**market.base_decimals)} tokens")

    tx = clob.deposit(
        token_address=base_token,
        amount=int(deposit_amount),
        sender_address=WALLET_ADDRESS,
        gas=200000,
    )

    print("Transaction created (not sent):")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    # In a real application, you would need to:
    # 1. Approve the CLOB contract to spend your tokens
    # 2. Sign and send the deposit transaction
    # 3. Wait for confirmation
    #
    # For this example, we'll just show the transaction object
    print("\nNOTE: This is a demonstration only. No transaction was sent.")


async def limit_order_example(client, web3, market):
    """Example of creating a limit order."""
    print_separator("Limit Order Example")

    # Create a limit order
    print("Creating limit order transaction...")

    # Current market price (or estimate)
    price = market.price or 100.0
    # Place a bid 5% below current price
    bid_price = price * 0.95

    tx = await client.create_order(
        market_address=market.address,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        amount=0.01,  # Small amount for testing
        price=bid_price,
        time_in_force=TimeInForce.GTC,
        sender_address=WALLET_ADDRESS,
        use_contract=True,
        use_router=True,
        gas=300000,
    )

    print("Transaction created (not sent):")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    # To actually send the transaction:
    # await sign_and_send_tx(web3, tx, PRIVATE_KEY)
    print("\nNOTE: This is a demonstration only. No transaction was sent.")


async def market_order_example(client, web3, market):
    """Example of creating a market order."""
    print_separator("Market Order Example")

    # Create a market order with a limit price
    print("Creating market order transaction...")

    # Current market price (or estimate)
    price = market.price or 100.0
    # Set a limit price 10% above current price for a buy order
    limit_price = price * 1.1

    tx = await client.create_order(
        market_address=market.address,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=0.01,  # Small amount for testing
        price=limit_price,  # Maximum price willing to pay
        time_in_force=TimeInForce.IOC,
        sender_address=WALLET_ADDRESS,
        use_contract=True,
        use_router=True,
        gas=300000,
    )

    print("Transaction created (not sent):")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    print("\nNOTE: This is a demonstration only. No transaction was sent.")


async def cancel_order_example(client, web3, market):
    """Example of cancelling an order."""
    print_separator("Cancel Order Example")

    # For this example, we'll use a fictional order ID
    fictional_order_id = 12345

    print(f"Creating cancel transaction for order ID {fictional_order_id}...")

    tx = await client.cancel_order(
        market_address=market.address,
        order_id=fictional_order_id,
        sender_address=WALLET_ADDRESS,
        use_router=True,
        gas=200000,
    )

    print("Transaction created (not sent):")
    print(f"To: {tx.get('to')}")
    print(f"Data length: {len(tx.get('data', ''))}")
    print(f"Gas: {tx.get('gas')}")

    print("\nNOTE: This is a demonstration only. No transaction was sent.")


async def main():
    """Run the on-chain trading examples."""
    if not check_config():
        return

    print("Initializing Web3...")
    web3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not web3.is_connected():
        print(f"Error: Could not connect to RPC URL {RPC_URL}")
        return

    print("Connected to blockchain:")
    print(f"Chain ID: {web3.eth.chain_id}")

    # Initialize client with Web3
    print("Initializing GTE client...")
    client = Client(web3_provider=web3, router_address=ROUTER_ADDRESS)

    try:
        # Get a market to work with
        market = await get_market_info(client)
        print(f"Selected market: {market.address}")

        # Run the examples
        await deposit_example(client, web3, market)
        await limit_order_example(client, web3, market)
        await market_order_example(client, web3, market)
        await cancel_order_example(client, web3, market)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
