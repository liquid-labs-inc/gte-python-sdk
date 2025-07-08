"""Example of querying portfolio and LP positions with the GTE client."""
import sys
sys.path.append(".")
import asyncio

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG

from examples.utils import WALLET_ADDRESS, print_separator


async def display_portfolio(client: GTEClient) -> None:
    """
    Retrieve and display the user's portfolio information.
    
    Args:
        client: Initialized GTE client
    """
    print_separator("Portfolio Overview")

    try:
        # Get the full portfolio information
        portfolio = await client.info.get_user_portfolio(WALLET_ADDRESS)

        # Display total USD value
        total_usd_balance = portfolio.get('totalUsdBalance', 0)
        print(f"Total Portfolio Value: ${total_usd_balance:.2f} USD")

        # Display individual token balances
        token_balances = portfolio.get('tokens', [])

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


async def display_lp_positions(client: GTEClient) -> None:
    """
    Retrieve and display the user's liquidity provider positions.
    
    Args:
        client: Initialized GTE client
    """
    print_separator("LP Positions")

    try:
        # Get LP positions
        lp_positions = await client.info.get_user_lp_positions(WALLET_ADDRESS)

        if not lp_positions:
            print("No LP positions found.")
            return

        print(f"Found {len(lp_positions)} LP positions:\n")
        print("--------------------------------------------------------------")
        print(f"{'Market':<10} {'Share':<10} {'APR':<10} {'Token Amounts':<30}")
        print("--------------------------------------------------------------")

        for position in lp_positions:
            market = position.market
            base_token = market.base.symbol
            quote_token = market.quote.symbol
            market_name = f"{base_token}/{quote_token}"
            share = position.share_of_pool * 100
            apr = position.apr * 100

            token0_amount = position.token0_amount
            token1_amount = position.token1_amount

            token_amounts = f"{token0_amount:.4f} {base_token}, {token1_amount:.4f} {quote_token}"

            print(f"{market_name:<10} {f'{share:.2f}%':<10} {f'{apr:.2f}%':<10} {token_amounts:<30}")

    except Exception as e:
        print(f"Error retrieving LP positions: {e}")


async def main() -> None:
    """Run the portfolio query examples."""
    config = TESTNET_CONFIG

    print("Connected to blockchain:")
    print(f"Account: {WALLET_ADDRESS}")

    # Initialize client with GTEClient
    print("Initializing GTE client...")
    async with GTEClient(
        config=config,
    ) as client:
        print(f"Chain ID: {await client._web3.eth.chain_id}")

        # Display portfolio overview
        await display_portfolio(client)

        # Display LP positions
        await display_lp_positions(client)


if __name__ == "__main__":
    asyncio.run(main())
