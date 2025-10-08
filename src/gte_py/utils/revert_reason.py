"""Revert reason extraction utilities.

This module is adapted from Trading Strategy's ``web3-ethereum-defi`` project.
"""

from __future__ import annotations

import logging
import pprint
from typing import Any, Union

from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import ContractLogicError

logger = logging.getLogger(__name__)

try:  # Optional runtime dependency for Ethereum tester environments
    from eth_tester.exceptions import TransactionFailed
except ImportError:  # pragma: no cover - eth-tester is optional

    class TransactionFailed(Exception):
        """Fallback TransactionFailed when eth-tester is unavailable."""


class TransactionReverted(Exception):
    """Signal a transaction error with a human-readable revert reason."""

    def get_solidity_reason_message(self) -> str:
        return self.args[0]


def fetch_transaction_revert_reason(
    web3: Web3,
    tx_hash: Union[HexBytes, str],
    use_archive_node: bool = False,
    unknown_error_message: str = "<could not extract the revert reason>",
) -> str:
    """Get the revert reason for a transaction hash by replaying it locally."""

    tx = web3.eth.get_transaction(tx_hash)

    if not isinstance(tx_hash, HexBytes):
        if isinstance(tx_hash, str):
            tx_hash = HexBytes(tx_hash)
        else:  # pragma: no cover - defensive branch
            raise AssertionError(f"Unknown type: {tx_hash.__class__} {tx_hash}")

    replay_tx: dict[str, Any] = {
        "to": tx["to"],
        "from": tx["from"],
        "value": tx.get("value", 0),
        "data": _get_transaction_data_field(tx),
        "gas": tx.get("gas"),
    }

    code = web3.eth.get_code(tx["to"])
    if code is None:
        logger.warning(
            "fetch_transaction_revert_reason(): target address %s is not a smart contract, "
            "likely cannot fetch the revert reason",
            tx["to"],
        )

    try:
        if use_archive_node:
            result = web3.eth.call(replay_tx, tx.blockNumber - 1)
        else:
            result = web3.eth.call(replay_tx)
    except ValueError as error:
        logger.debug("Revert exception result is: %s", error)
        assert len(error.args) == 1, f"Unexpected error arguments for {error}"
        data = error.args[0]
        if isinstance(data, str):
            return data
        return data.get("message", unknown_error_message)
    except ContractLogicError as error:
        return error.args[0]
    except TransactionFailed as error:  # pragma: no cover - eth-tester specific
        return error.args[0]

    receipt = web3.eth.get_transaction_receipt(tx_hash)
    if receipt.get("status") != 0:
        logger.error(
            "Queried revert reason for a transaction, but receipt indicates success. "
            "tx_hash: %s, receipt: %s",
            tx_hash.hex(),
            receipt,
        )

    current_block_number = web3.eth.block_number
    pretty_result = pprint.pformat(result)
    logger.error(
        "Transaction succeeded when fetching revert reason.\n"
        "To address: %s, hash: %s, tx block num: %s, gas: %s, current block number: %s\n"
        "Transaction result:\n%s\n"
        "- Maybe the chain tip is unstable\n"
        "- Maybe transaction failed due to slippage\n"
        "- Maybe someone is frontrunning you and it does not happen with eth_call replay\n"
        "- Maybe the target address is not code",
        tx["to"],
        tx_hash.hex(),
        tx.get("blockNumber"),
        tx.get("gas"),
        current_block_number,
        pretty_result,
    )
    return unknown_error_message


def _get_transaction_data_field(tx: Any) -> str:
    data_field = tx.get("input") or tx.get("data")
    if isinstance(data_field, (bytes, bytearray, HexBytes)):
        return HexBytes(data_field).hex()
    if isinstance(data_field, str):
        return data_field
    return "0x"
