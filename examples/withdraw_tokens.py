"""Example of withdrawing tokens from the exchange balance to the wallet."""
import sys
sys.path.append(".")
import asyncio
from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from examples.utils import WALLET_ADDRESS, WALLET_PRIVATE_KEY

BTC_ADDRESS: ChecksumAddress = to_checksum_address("0x7f11aa697e05b75600354ac9acf8bb209225e932")

def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        # when limit orders get filled, the exchange balance stores the tokens
        # so we need to withdraw the tokens from the exchange balance to put them in the wallet
        
       # print out current balances
       balances = await client.execution.get_balance(token_address=BTC_ADDRESS, account=WALLET_ADDRESS)
       
       print(f"Wallet balance: {balances[0]}")
       print(f"Exchange balance: {balances[1]}")
       
       exchange_balance = balances[1]

       await client.execution.withdraw(token_address=BTC_ADDRESS, amount=int(exchange_balance * 10 ** 18), gas=50 * 10**6)
        
    return


if __name__ == "__main__":
    asyncio.run(main())
