# get env variables
import os
from dotenv import load_dotenv
from eth_typing import ChecksumAddress, HexStr
from eth_utils.address import to_checksum_address

_ = load_dotenv()

WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")

if WALLET_ADDRESS_RAW:
    WALLET_ADDRESS: ChecksumAddress = to_checksum_address(WALLET_ADDRESS_RAW)
if WALLET_PRIVATE_KEY_RAW:
    WALLET_PRIVATE_KEY: HexStr = HexStr(WALLET_PRIVATE_KEY_RAW)


def print_separator(title: str) -> None:
    """Print a section separator."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)