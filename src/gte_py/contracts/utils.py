import importlib.resources as pkg_resources
import json
import os
from typing import Any

from web3 import Web3


def get_current_timestamp() -> int:
    """Get the current Unix timestamp in seconds."""
    return int(time.time())


def create_deadline(minutes_in_future: int = 30) -> int:
    """
    Create a deadline timestamp for transactions.

    Args:
        minutes_in_future: Number of minutes in the future for the deadline

    Returns:
        Unix timestamp in seconds
    """
    return get_current_timestamp() + (minutes_in_future * 60)


def to_wei(amount: float, decimals: int = 18) -> int:
    """
    Convert a decimal amount to wei (or equivalent for other tokens).

    Args:
        amount: Decimal amount
        decimals: Number of decimals of the token

    Returns:
        Integer amount in wei
    """
    return int(amount * (10**decimals))


def from_wei(amount: int, decimals: int = 18) -> float:
    """
    Convert wei amount to decimal.

    Args:
        amount: Wei amount
        decimals: Number of decimals of the token

    Returns:
        Decimal amount
    """
    return amount / (10**decimals)


# Fix for the Traversable issue
def load_abi(abi_name: str, abi_path: str | None = None) -> list[dict[str, Any]]:
    """
    Load ABI from a file or package resources.

    Args:
        abi_name: Name of the ABI file (without .json extension)
        abi_path: Optional path to the ABI file

    Returns:
        The loaded ABI as a Python object

    Raises:
        ValueError: If the ABI file cannot be found
    """
    # If path is provided, try to load from there
    if abi_path:
        try:
            with open(abi_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"ABI file not found at {abi_name}") from None

    # Otherwise, try to load from package resources
    try:
        # Look in the abi directory first
        abi_file = f"{abi_name}.json"
        try:
            # For Python 3.9+
            package_path = pkg_resources.files("gte_py.contracts.abi")
            file_path = package_path.joinpath(abi_file)
            # Convert Traversable to string path
            str_path = str(file_path)
            with open(str_path) as f:
                return json.load(f)
        except (AttributeError, TypeError):
            # Fallback for older Python versions
            resource_pkg = "gte_py.contracts.abi"
            with pkg_resources.open_text(resource_pkg, abi_file) as f:
                return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError):
        # Try predefined paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "abi", f"{abi_name}.json"),
            os.path.join(os.path.dirname(__file__), f"{abi_name}.json"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)

        raise ValueError(
            f"ABI '{abi_name}' not found in package resources or expected paths"
        ) from None


def load_iclob_abi() -> list[dict[str, Any]]:
    """
    Load the ICLOB ABI from package resources.

    Returns:
        The ICLOB contract ABI as a Python list
    """
    return load_abi("iclob")


def prepare_permit_signature(
    web3: Web3, permit_data: dict[str, Any], private_key: str
) -> tuple[dict[str, Any], bytes]:
    """
    Helper function to prepare and sign Permit2 data.

    Args:
        web3: Web3 instance
        permit_data: Permit data
        private_key: Private key to sign with

    Returns:
        Tuple of (permit_single, signature)
    """
    # This is a simplified implementation. In a real application,
    # you would need to implement the full EIP-712 signing logic.
    # You would typically use a library like eth-account for this.

    # Placeholder for the real implementation
    permit_single = {
        "details": {
            "token": web3.to_checksum_address(permit_data["token"]),
            "amount": permit_data["amount"],
            "expiration": permit_data["expiration"],
            "nonce": permit_data["nonce"],
        },
        "spender": web3.to_checksum_address(permit_data["spender"]),
        "sigDeadline": permit_data["sigDeadline"],
    }

    # In a real implementation, you would create the correct EIP-712 message
    # and sign it with the private key
    message_hash = b""  # Placeholder
    signature = b""  # Placeholder

    return permit_single, signature
