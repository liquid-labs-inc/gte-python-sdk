import asyncio
import os
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from eth_utils.address import to_checksum_address

from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG

load_dotenv()

WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")

if not WALLET_ADDRESS_RAW or not WALLET_PRIVATE_KEY_RAW:
    raise ValueError("Missing wallet credentials")

WALLET_ADDRESS: ChecksumAddress = to_checksum_address(WALLET_ADDRESS_RAW)
WALLET_PRIVATE_KEY: HexStr = HexStr(WALLET_PRIVATE_KEY_RAW)

BTC_ADDRESS: ChecksumAddress = to_checksum_address("0x7f11aa697e05b75600354ac9acf8bb209225e932")

def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


async def main():
    config = TESTNET_CONFIG
        
    async with GTEClient(config=config, wallet_address=WALLET_ADDRESS, wallet_private_key=WALLET_PRIVATE_KEY) as client:

        
       # print out current baclances
       balances = await client.execution.get_balance(token_address=BTC_ADDRESS, account=WALLET_ADDRESS)
       
       print(f"Wallet balance: {balances[0]}")
       print(f"Exchange balance: {balances[1]}")
       
       exchange_balance = balances[1]

       await client.execution.withdraw(token_address=BTC_ADDRESS, amount=int(exchange_balance * 10 ** 18), gas=50 * 10**6)
        
    return


if __name__ == "__main__":
    asyncio.run(main())
