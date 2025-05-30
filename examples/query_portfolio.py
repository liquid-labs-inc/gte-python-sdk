"""Example of querying portfolio and LP positions with the GTE client."""

import asyncio

from examples.utils import MARKET_ADDRESS, show_balances
from gte_py.api.chain.utils import make_web3
from gte_py.clients import Client
from gte_py.configs import TESTNET_CONFIG
from utils import (
    print_separator,
    WALLET_ADDRESS,
    WALLET_PRIVATE_KEY
)


async def display_portfolio(client: Client) -> None:
    """
    Retrieve and display the user's portfolio information.
    
    Args:
        client: Initialized GTE client
    """
    print_separator("Portfolio Overview")

    try:
        # Get the full portfolio information
        portfolio = await client.user.get_portfolio()

        # Display total USD value
        total_usd_balance = await client.user.get_total_usd_balance()
        print(f"Total Portfolio Value: ${total_usd_balance:.2f} USD")

        # Display individual token balances
        token_balances = await client.user.get_token_balances()

        print("\nToken Balances:")
        print("--------------------------------------------------------------")
        print(f"{'Token':<10} {'Balance':<15} {'USD Value':<15} {'PnL (USD)':<15}")
        print("--------------------------------------------------------------")

        for token in token_balances:
            token_info = token.get('token', {})
            symbol = token_info.get('symbol', 'UNKNOWN')
            balance = float(token.get('balance', 0))
            balance_usd = float(token.get('balanceUsd', 0))
            realized_pnl = float(token.get('realizedPnlUsd', 0))
            unrealized_pnl = float(token.get('unrealizedPnlUsd', 0))
            total_pnl = realized_pnl + unrealized_pnl

            print(f"{symbol:<10} {balance:<15.6f} ${balance_usd:<14.2f} ${total_pnl:<14.2f}")

    except Exception as e:
        print(f"Error retrieving portfolio: {e}")


async def display_lp_positions(client: Client) -> None:
    """
    Retrieve and display the user's liquidity provider positions.
    
    Args:
        client: Initialized GTE client
    """
    print_separator("LP Positions")

    try:
        # Get LP positions
        lp_positions = await client.user.get_lp_positions()

        if not lp_positions:
            print("No LP positions found.")
            return

        print(f"Found {len(lp_positions)} LP positions:\n")
        print("--------------------------------------------------------------")
        print(f"{'Market':<20} {'Share':<10} {'APR':<10} {'Token Amounts':<30}")
        print("--------------------------------------------------------------")

        for position in lp_positions:
            market = position.get('market', {})
            base_token = market.get('baseToken', {}).get('symbol', 'UNKNOWN')
            quote_token = market.get('quoteToken', {}).get('symbol', 'UNKNOWN')
            market_name = f"{base_token}/{quote_token}"

            share = position.get('shareOfPool', 0) * 100  # Convert to percentage
            apr = position.get('apr', 0) * 100  # Convert to percentage
            token0_amount = float(position.get('token0Amount', 0))
            token1_amount = float(position.get('token1Amount', 0))

            token_amounts = f"{token0_amount:.4f} {base_token}, {token1_amount:.4f} {quote_token}"

            print(f"{market_name:<20} {share:<10.2f}% {apr:<10.2f}% {token_amounts:<30}")

    except Exception as e:
        print(f"Error retrieving LP positions: {e}")


async def main() -> None:
    """Run the portfolio query examples."""
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

        # Display portfolio overview
        await display_portfolio(client)

        # Display LP positions
        await display_lp_positions(client)

        market = await client.info.get_market(MARKET_ADDRESS)
        await show_balances(client, market)


if __name__ == "__main__":
    asyncio.run(main())
