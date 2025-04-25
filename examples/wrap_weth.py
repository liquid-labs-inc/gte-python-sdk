"""Example of wrapping and unwrapping ETH with the GTE client."""

import asyncio
from eth_typing import HexStr
from web3 import Web3

from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.contracts.weth import WETH

from utils import (
    print_separator, 
    WALLET_ADDRESS, 
    WALLET_PRIVATE_KEY
)


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


async def get_weth_balance(client: Client, web3, weth_address):
    """Get WETH balance of the wallet."""
    print_separator("WETH Balance")

    # Create WETH instance directly to check balance
    weth = WETH(web3, weth_address)

    # Get WETH balance using the ERC20 balanceOf method
    weth_balance_raw = weth.balance_of(WALLET_ADDRESS)
    weth_balance = weth.convert_amount_to_float(weth_balance_raw)

    # Get exchange balance through the client
    _, exchange_balance = await client.get_balance(weth_address)

    # Get native ETH balance
    eth_balance = web3.from_wei(web3.eth.get_balance(WALLET_ADDRESS), 'ether')

    print(f"ETH Balance:   {eth_balance:.6f} ETH")
    print(f"WETH Balance:  {weth_balance:.6f} WETH (in wallet)")
    print(f"WETH Balance:  {exchange_balance:.6f} WETH (in exchange)")


async def wrap_eth_example(client: Client, web3, weth_address, amount_eth=0.01):
    """Example of wrapping ETH to WETH."""
    print_separator("Wrap ETH Example")

    try:
        print(f"Creating transaction to wrap {amount_eth} ETH to WETH...")

        # Explicitly add nonce to avoid missing nonce errors
        nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

        tx_func = await client.wrap_eth(
            weth_address=weth_address,
            amount_eth=amount_eth,
            gas=100000,
            nonce=nonce
        )

        print("Transaction created")
        print("\nSending transaction...")
        receipt = tx_func.send(WALLET_PRIVATE_KEY)
        return receipt
    except Exception as e:
        print(f"Error wrapping ETH: {str(e)}")
        raise


async def unwrap_eth_example(client: Client, web3, weth_address, amount_eth=0.01):
    """Example of unwrapping WETH back to ETH."""
    print_separator("Unwrap WETH Example")

    try:
        print(f"Creating transaction to unwrap {amount_eth} WETH to ETH...")

        # Explicitly add nonce to avoid missing nonce errors
        nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)

        tx_func = await client.unwrap_eth(
            weth_address=weth_address,
            amount_eth=amount_eth,
            gas=100000,
            nonce=nonce
        )

        print("Transaction created")
        print("\nSending transaction...")
        receipt = tx_func.send(WALLET_PRIVATE_KEY)
        return receipt
    except Exception as e:
        print(f"Error unwrapping WETH: {str(e)}")
        raise


async def main():
    """Run the WETH wrapping examples."""
    network = TESTNET_CONFIG

    print("Initializing Web3...")
    web3 = Web3(Web3.HTTPProvider(network.rpc_http))

    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC node at {network.rpc_http}")

    print("Connected to blockchain:")
    print(f"Chain ID: {web3.eth.chain_id}")

    # Check for WETH address
    if not TESTNET_CONFIG.weth_address:
        raise ValueError("WETH address not configured in TESTNET_CONFIG")
    print(f"Using WETH address: {TESTNET_CONFIG.weth_address}")

    # Check for wallet configuration
    if not WALLET_ADDRESS or not WALLET_PRIVATE_KEY:
        raise ValueError("WALLET_ADDRESS and WALLET_PRIVATE_KEY must be set in .env file")
    wallet_address = Web3.to_checksum_address(WALLET_ADDRESS)

    # Initialize client with Web3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, sender_address=wallet_address)

    try:
        # Show balances before operations
        await get_weth_balance(client, web3, TESTNET_CONFIG.weth_address)

        # Wrap ETH to WETH
        amount_to_wrap = 0.01  # Small amount for testing
        receipt = await wrap_eth_example(client, web3, TESTNET_CONFIG.weth_address, amount_eth=amount_to_wrap)
        print(f"Transaction hash: {receipt.transactionHash.hex()}")

        # Wait a bit for the transaction to be fully processed
        print("\nWaiting for transaction to be fully processed...")
        await asyncio.sleep(5)

        # Show balances after wrapping
        await get_weth_balance(client, web3, TESTNET_CONFIG.weth_address)

        # Unwrap WETH back to ETH
        print("\nNow unwrapping the same amount...")
        receipt = await unwrap_eth_example(client, web3, TESTNET_CONFIG.weth_address, amount_eth=amount_to_wrap)
        print(f"Transaction hash: {receipt.transactionHash.hex()}")

        # Wait a bit for the transaction to be fully processed
        print("\nWaiting for transaction to be fully processed...")
        await asyncio.sleep(5)

        # Show final balances
        await get_weth_balance(client, web3, TESTNET_CONFIG.weth_address)

    except Exception as e:
        print(f"Error during examples: {str(e)}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
