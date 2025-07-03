"""Example of canceling/replacing transactions with the GTE client."""
import sys
sys.path.append(".")
import asyncio
import logging

from eth_typing import HexStr
from eth_utils.address import to_checksum_address
from web3 import AsyncWeb3
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import (
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY
)


async def cancel_transaction(client: GTEClient, tx_hash: str, gas_price_increase: float = 1.5) -> str:
    """
    Cancel a pending transaction by replacing it with a higher gas price transaction.
    
    Args:
        client: GTEClient instance
        tx_hash: Hash of the transaction to cancel
        gas_price_increase: Multiplier for gas price increase (default 1.5x)
    
    Returns:
        Hash of the cancellation transaction
    """
    try:
        # Convert string hash to proper format
        tx_hash_formatted = to_checksum_address(tx_hash) if tx_hash.startswith('0x') else to_checksum_address(f"0x{tx_hash}")
        
        # Get the original transaction
        tx = await client._web3.eth.get_transaction(tx_hash_formatted)
        if not tx:
            raise ValueError(f"Transaction {tx_hash} not found")
        
        # Get current gas price
        current_gas_price = await client._web3.eth.gas_price
        
        # Calculate new gas price (increase by the specified multiplier)
        new_gas_price = int(current_gas_price * gas_price_increase)
        
        # Get nonce safely
        nonce = tx.get('nonce')
        if nonce is None:
            raise ValueError("Could not get transaction nonce")
        
        # Get original gas price safely
        original_gas_price = tx.get('gasPrice', 0)
        
        # Create cancellation transaction (send 0 ETH to yourself)
        cancel_tx = {
            'from': WALLET_ADDRESS,
            'to': WALLET_ADDRESS,
            'value': 0,
            'gas': 21000,  # Standard gas limit for ETH transfer
            'gasPrice': new_gas_price,
            'nonce': nonce,  # Same nonce as the original transaction
            'data': b''  # No data
        }
        
        # Sign and send the cancellation transaction
        signed_tx = client._web3.eth.account.sign_transaction(cancel_tx, WALLET_PRIVATE_KEY)
        cancel_hash = await client._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"Original transaction: {tx_hash}")
        print(f"Cancellation transaction sent: {cancel_hash.hex()}")
        print(f"Gas price increased from {original_gas_price} to {new_gas_price}")
        
        return cancel_hash.hex()
        
    except Exception as e:
        print(f"Error canceling transaction: {e}")
        raise


async def speed_up_transaction(client: GTEClient, tx_hash: str, gas_price_increase: float = 1.3) -> str:
    """
    Speed up a pending transaction by replacing it with a higher gas price.
    
    Args:
        client: GTEClient instance
        tx_hash: Hash of the transaction to speed up
        gas_price_increase: Multiplier for gas price increase (default 1.3x)
    
    Returns:
        Hash of the replacement transaction
    """
    try:
        # Convert string hash to proper format
        tx_hash_formatted = to_checksum_address(tx_hash) if tx_hash.startswith('0x') else to_checksum_address(f"0x{tx_hash}")
        
        # Get the original transaction
        tx = await client._web3.eth.get_transaction(tx_hash_formatted)
        if not tx:
            raise ValueError(f"Transaction {tx_hash} not found")
        
        # Get current gas price
        current_gas_price = await client._web3.eth.gas_price
        
        # Calculate new gas price
        new_gas_price = int(current_gas_price * gas_price_increase)
        
        # Get transaction fields safely
        tx_from = tx.get('from')
        tx_to = tx.get('to')
        tx_value = tx.get('value', 0)
        tx_gas = tx.get('gas', 21000)
        tx_nonce = tx.get('nonce')
        tx_input = tx.get('input', b'')
        original_gas_price = tx.get('gasPrice', 0)
        
        if tx_from is None or tx_to is None or tx_nonce is None:
            raise ValueError("Could not get required transaction fields")
        
        # Create replacement transaction with same parameters but higher gas price
        replacement_tx = {
            'from': tx_from,
            'to': tx_to,
            'value': tx_value,
            'gas': tx_gas,
            'gasPrice': new_gas_price,
            'nonce': tx_nonce,
            'data': tx_input
        }
        
        # Sign and send the replacement transaction
        signed_tx = client._web3.eth.account.sign_transaction(replacement_tx, WALLET_PRIVATE_KEY)
        replacement_hash = await client._web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"Original transaction: {tx_hash}")
        print(f"Replacement transaction sent: {replacement_hash.hex()}")
        print(f"Gas price increased from {original_gas_price} to {new_gas_price}")
        
        return replacement_hash.hex()
        
    except Exception as e:
        print(f"Error speeding up transaction: {e}")
        raise


async def main() -> None:
    """Run the transaction cancellation examples."""
    config = TESTNET_CONFIG

    print("Initializing GTE client...")
    async with GTEClient(
        config=config,
        wallet_address=WALLET_ADDRESS,
        wallet_private_key=WALLET_PRIVATE_KEY
    ) as client:
        print(f"Connected to chain ID: {await client._web3.eth.chain_id}")
        
        # Example transaction hash (replace with actual hash)
        example_tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        
        print("\n=== Transaction Cancellation Example ===")
        print("Note: Replace the example_tx_hash with an actual pending transaction hash")
        
        # Uncomment these lines when you have a real transaction to cancel:
        # await cancel_transaction(client, example_tx_hash)
        # await speed_up_transaction(client, example_tx_hash)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
