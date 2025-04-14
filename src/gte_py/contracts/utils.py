import importlib.resources as pkg_resources
import json
import os
import time
from typing import Any


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
