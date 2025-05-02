"""Example of ensuring token deposits for a market with the GTE client."""

import asyncio
import logging
from typing import Optional, Tuple

from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from gte_py.models import Market, Token

from utils import (
    print_separator,
    display_market_info,
    show_balances,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY,
    MARKET_ADDRESS
)


async def get_token_balances(client: Client, token: Token) -> float:
    """
    Get wallet and exchange balances for a token.
    
    Args:
        client: Initialized GTE client
        token: Token object
        
    Returns:
        Tuple containing (wallet_balance, exchange_balance)
    """
    try:
        exchange_balance = await client.account.get_token_balance(token.address)
        return exchange_balance
    except Exception as e:
        print(f"Error getting balances for {token.symbol}: {e}")
        return 0.0


async def ensure_token_deposit(
        client: Client,
        token: Token,
        quantity: float,
        gas_limit: int = 50 * 10000000
) -> bool:
    """
    Ensure a token is approved and deposited to the exchange.
    
    Args:
        client: Initialized GTE client
        token: Token to deposit
        quantity: Quantity to deposit in token units
        gas_limit: Gas limit for transaction
        
    Returns:
        bool: True if deposit was successful, False otherwise
    """
    print_separator(f"Deposit {token.symbol}")

    try:
        token_amount = token.convert_quantity_to_amount(quantity)
        print(f"Creating transaction to approve and deposit {quantity} {token.symbol}...")

        # This will handle both approval and deposit as needed
        await client.account.ensure_deposit(
            token_address=token.address,
            amount=token_amount,
            gas=gas_limit
        )

        print(f"Successfully deposited {quantity} {token.symbol} to the exchange")
        return True

    except Exception as e:
        print(f"Error during token deposit: {e}")
        return False


async def select_token_from_market(market: Market) -> Optional[Token]:
    """
    Allow user to select a token from the market.
    
    Args:
        market: Market object
        
    Returns:
        Selected token or None if selection was invalid
    """
    print(f"\nAvailable tokens in market {market.pair}:")
    print(f"1. {market.base.symbol} (Base token)")
    print(f"2. {market.quote.symbol} (Quote token)")

    try:
        choice = int(input("\nSelect token (1 or 2): "))
        if choice == 1:
            return market.base
        elif choice == 2:
            return market.quote
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input. Please enter 1 or 2.")
        return None


async def main() -> None:
    """Run the token deposit example."""
    network = TESTNET_CONFIG

    print("Initializing AsyncWeb3...")
    web3 = await make_web3(network, WALLET_ADDRESS, WALLET_PRIVATE_KEY)

    print("Connected to blockchain:")
    print(f"Chain ID: {await web3.eth.chain_id}")
    print(f"Account: {WALLET_ADDRESS}")

    # Initialize client with AsyncWeb3
    print("Initializing GTE client...")

    async with Client(web3=web3, config=network, account=WALLET_ADDRESS) as client:
        await client.init()

        # Get market information
        market = await display_market_info(client, MARKET_ADDRESS)
        if not market:
            print("Could not get market information. Exiting.")
            return

        # Show initial balances
        await show_balances(client, market)

        # Let user select which token to deposit
        token = await select_token_from_market(market)
        if not token:
            return

        # Get deposit amount
        try:
            quantity = float(input(f"\nEnter quantity(float) of {token.symbol} to deposit: "))
            if quantity <= 0:
                print("Amount must be greater than zero. Exiting.")
                return
        except ValueError:
            print("Invalid amount entered. Exiting.")
            return

        # Perform the deposit
        success = await ensure_token_deposit(client, token, quantity)

        await show_balances(client, market)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
