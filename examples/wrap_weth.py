"""Example of wrapping and unwrapping ETH with the GTE client."""

import asyncio

from eth_utils import to_wei
from web3 import AsyncWeb3

from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from utils import (
    print_separator,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY
)


async def get_weth_balance(client: Client, web3: AsyncWeb3, weth_address: str) -> None:
    """Get WETH balance of the wallet."""
    print_separator("WETH Balance")

    # Create WETH instance directly to check balance
    weth = client.token.get_weth(weth_address)

    # Get WETH balance using the async ERC20 balanceOf method
    weth_balance_raw = await weth.balance_of(WALLET_ADDRESS)
    weth_balance = await weth.convert_amount_to_quantity(weth_balance_raw)

    # Get exchange balance through the client
    exchange_balance = await client.user.get_token_balance(weth_address)

    # Get native ETH balance
    eth_balance = web3.from_wei(await web3.eth.get_balance(WALLET_ADDRESS, 'latest'), 'ether')

    print(f"ETH Balance:   {eth_balance:.6f} ETH")
    print(f"WETH Balance:  {weth_balance:.6f} WETH (in wallet)")
    print(f"WETH Balance:  {exchange_balance:.6f} WETH (in exchange)")


async def wrap_eth_example(client: Client, web3: AsyncWeb3, weth_address: str, amount_eth: float = 0.01):
    """Example of wrapping ETH to WETH."""
    print_separator("Wrap ETH Example")

    print(f"Creating transaction to wrap {amount_eth} ETH to WETH...")

    await client.user.wrap_eth(
        weth_address=weth_address,
        amount=to_wei(amount_eth, 'ether'),

    )


async def unwrap_eth_example(client: Client, web3: AsyncWeb3, weth_address: str, amount_eth: float = 0.01):
    """Example of unwrapping WETH back to ETH."""
    print_separator("Unwrap WETH Example")

    print(f"Creating transaction to unwrap {amount_eth} WETH to ETH...")

    await client.user.unwrap_eth(
        weth_address=weth_address,
        amount=to_wei(amount_eth, 'ether'),

    )


async def main() -> None:
    """Run the WETH wrapping examples."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)

    print("Connected to blockchain:")
    print(f"Chain ID: {await web3.eth.chain_id}")

    # Check for WETH address
    if not TESTNET_CONFIG.weth_address:
        raise ValueError("WETH address not configured in TESTNET_CONFIG")
    print(f"Using WETH address: {TESTNET_CONFIG.weth_address}")

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")
    client = Client(web3=web3, config=network, account=web3.eth.default_account)
    await client.init()

    # Show balances before operations
    await get_weth_balance(client, web3, TESTNET_CONFIG.weth_address)

    # Wrap ETH to WETH
    amount_to_wrap = 0.01  # Small amount for testing
    await wrap_eth_example(client, web3, TESTNET_CONFIG.weth_address, amount_eth=amount_to_wrap)

    # Show balances after wrapping
    await get_weth_balance(client, web3, TESTNET_CONFIG.weth_address)

    # Unwrap WETH back to ETH
    print("\nNow unwrapping the same amount...")
    await unwrap_eth_example(client, web3, TESTNET_CONFIG.weth_address, amount_eth=amount_to_wrap)

    # Show final balances
    await get_weth_balance(client, web3, TESTNET_CONFIG.weth_address)


if __name__ == "__main__":
    asyncio.run(main())
