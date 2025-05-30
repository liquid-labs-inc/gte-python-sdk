"""Example of approving an operator for trading on behalf of your account."""

import asyncio
import logging
from os import getenv

from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address

from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from utils import (
    print_separator,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
)

OPERATOR_ADDRESS = to_checksum_address(getenv("OPERATOR_ADDRESS"))


async def check_operator_status(client: Client, operator_address: ChecksumAddress) -> bool:
    """Check if an operator is already approved."""
    print_separator("Checking Operator Status")

    is_approved = await client.user.is_operator_approved(operator_address)

    if is_approved:
        print(f"Operator {operator_address} is already approved")
    else:
        print(f"Operator {operator_address} is NOT approved")

    return is_approved


async def approve_operator_example(client: Client, operator_address: ChecksumAddress) -> None:
    """Example of approving an operator."""
    print_separator("Approve Operator Example")

    print(f"Approving operator {operator_address}...")

    # Approve the operator
    await client.user.approve_operator(
        operator_address=operator_address,
        gas=300000  # Set appropriate gas limit
    )

    print(f"Operator {operator_address} approval transaction submitted")

    # Check if approval was successful
    is_approved = await client.user.is_operator_approved(operator_address)

    if is_approved:
        print(f"Operator {operator_address} is now approved")
    else:
        print(f"Operator approval transaction may still be pending")


async def disapprove_operator_example(client: Client, operator_address: ChecksumAddress) -> None:
    """Example of disapproving an operator."""
    print_separator("Disapprove Operator Example")
    print(f"Disapproving operator {operator_address}...")

    # Disapprove the operator
    await client.user.disapprove_operator(
        operator_address=operator_address,
        gas=300000  # Set appropriate gas limit
    )

    print(f"Operator {operator_address} disapproval transaction submitted")

    # Check if disapproval was successful
    is_approved = await client.user.is_operator_approved(operator_address)

    if not is_approved:
        print(f"Operator {operator_address} is now disapproved")
    else:
        print(f"Operator disapproval transaction may still be pending")


async def main() -> None:
    """Run the operator approval examples."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)

    print("Connected to blockchain:")
    print(f"Chain ID: {await web3.eth.chain_id}")

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, account=WALLET_ADDRESS)
    await client.init()

    # Display operator address
    print(f"Using operator address: {OPERATOR_ADDRESS}")

    # Check current operator status
    is_approved = await check_operator_status(client, OPERATOR_ADDRESS)

    # Approve or disapprove based on current status
    if not is_approved:
        await approve_operator_example(client, OPERATOR_ADDRESS)
    else:
        # Uncomment below if you want to disapprove an already approved operator
        # await disapprove_operator_example(client, OPERATOR_ADDRESS)
        print("Operator is already approved. To disapprove, uncomment the disapprove call in main().")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
