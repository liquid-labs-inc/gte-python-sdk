"""Example of wrapping and unwrapping ETH with the GTE client."""

import asyncio
import os

from dotenv import load_dotenv
from eth_typing import HexStr
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG

# Load environment variables from .env file
load_dotenv()

# Configure these variables through environment or directly
WALLET_ADDRESS = Web3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
WALLET_PRIVATE_KEY = HexStr(os.getenv("WALLET_PRIVATE_KEY"))


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


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


async def wrap_eth_example(client: Client, web3, amount_eth=0.01, send_tx=False):
    """Example of wrapping ETH to WETH."""
    print_separator("Wrap ETH Example")

    try:
        print(f"Creating transaction to wrap {amount_eth} ETH to WETH...")

        # Explicitly add nonce to avoid missing nonce errors
        nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

        tx_func = await client.wrap_eth(
            weth_address=TESTNET_CONFIG.weth_address,
            amount_eth=amount_eth,
            gas=100000,
            nonce=nonce
        )

        print("Transaction created:")

        if send_tx and WALLET_PRIVATE_KEY:
            print("\nSending transaction...")
            receipt = tx_func.send(WALLET_PRIVATE_KEY)
            return receipt
        else:
            print("\nNOTE: This is a demonstration only. No transaction was sent.")
            print("Set send_tx=True and provide WALLET_PRIVATE_KEY to send transactions.")
            return None
    except Exception as e:
        print(f"Error wrapping ETH: {str(e)}")
        raise


async def unwrap_eth_example(client: Client, web3, amount_eth=0.01, send_tx=False):
    """Example of unwrapping WETH back to ETH."""
    print_separator("Unwrap WETH Example")

    try:
        print(f"Creating transaction to unwrap {amount_eth} WETH to ETH...")

        # Explicitly add nonce to avoid missing nonce errors
        nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

        tx_func = await client.unwrap_eth(
            weth_address=TESTNET_CONFIG.weth_address,
            amount_eth=amount_eth,
            gas=100000,
            nonce=nonce
        )

        print("Transaction created:")

        if send_tx and WALLET_PRIVATE_KEY:
            print("\nSending transaction...")
            receipt = tx_func.send(WALLET_PRIVATE_KEY)
            return receipt
        else:
            print("\nNOTE: This is a demonstration only. No transaction was sent.")
            print("Set send_tx=True and provide WALLET_PRIVATE_KEY to send transactions.")
            return None
    except Exception as e:
        print(f"Error unwrapping WETH: {str(e)}")
        raise


async def get_weth_balance(client: Client, web3):
    """Get WETH balance of the wallet."""
    print_separator("WETH Balance")

    # Create WETH instance directly to check balance
    from gte_py.contracts.weth import WETH
    weth = WETH(web3, TESTNET_CONFIG.weth_address)

    # Get WETH balance using the ERC20 balanceOf method
    weth_balance_raw = weth.balance_of(WALLET_ADDRESS)
    weth_balance = weth.format_amount_readable(weth_balance_raw)

    # Get exchange balance through the client
    _, exchange_balance = await client.get_balance(TESTNET_CONFIG.weth_address)

    # Get native ETH balance
    eth_balance = web3.from_wei(web3.eth.get_balance(WALLET_ADDRESS), 'ether')

    print(f"ETH Balance:   {eth_balance:.6f} ETH")
    print(f"WETH Balance:  {weth_balance:.6f} WETH (in wallet)")
    print(f"WETH Balance:  {exchange_balance:.6f} WETH (in exchange)")


async def main():
    """Run the WETH wrapping examples."""
    network = TESTNET_CONFIG

    print("Initializing Web3...")
    web3 = Web3(Web3.HTTPProvider(network.rpc_http))

    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC node at {network.rpc_http}")

    print("Connected to blockchain:")
    print(f"Chain ID: {web3.eth.chain_id}")

    print(f"Using WETH address: {TESTNET_CONFIG.weth_address}")
    if not TESTNET_CONFIG.weth_address:
        print("ERROR: WETH address not configured in TESTNET_CONFIG. Please add it.")
        return

    # Initialize client with Web3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, sender_address=WALLET_ADDRESS)

    # Show balances before operations
    await get_weth_balance(client, web3)

    # Run the examples (set send_tx=True to actually send transactions)
    send_tx = True  # Set to True to send actual transactions

    # WETH examples
    amount_to_wrap = 0.001  # Small amount for testing
    await wrap_eth_example(client, web3, amount_eth=amount_to_wrap, send_tx=send_tx)

    # Show balances before operations
    await get_weth_balance(client, web3)

    # Only try to unwrap if we wrapped first
    if send_tx:
        # Wait a bit to make sure the wrapping transaction is fully processed
        print("\nWaiting for wrap transaction to be fully processed...")
        await asyncio.sleep(5)

        # Then try to unwrap the same amount
        # await unwrap_eth_example(client, web3, amount_eth=amount_to_wrap, send_tx=send_tx)

        # Show balances after operations
        # print("\nBalances after operations:")
        # Wait a bit to make sure the unwrapping transaction is fully processed
        # await asyncio.sleep(5)
        # await get_weth_balance(client, web3)
    else:
        print("\nSet send_tx=True to execute actual transactions and see balance changes.")


if __name__ == "__main__":
    asyncio.run(main())
