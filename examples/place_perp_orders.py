"""Example for querying and trading the FAKEBTCUSD perpetual market."""
from __future__ import annotations

import asyncio
import logging
import sys
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

sys.path.append(".")

from gte_py.api.chain.structs import Side, TiF
from gte_py.clients import GTEClient
from gte_py.configs import TESTNET_CONFIG
from gte_py.utils.revert_reason import fetch_transaction_revert_reason
from examples.constants import FAKEBTCUSD
from examples.utils import WALLET_PRIVATE_KEY, print_separator
from hexbytes import HexBytes
from web3 import Web3


def atomic_to_decimal(value: int) -> Decimal:
    """Convert an atomic 18-decimal integer value to Decimal."""
    return Decimal(value) / Decimal(10**18)


async def main() -> None:
    """Query perp market data and place example orders on FAKEBTCUSD."""

    config = TESTNET_CONFIG
    market_id = FAKEBTCUSD

    async with GTEClient(config=config, wallet_private_key=WALLET_PRIVATE_KEY) as client:
        print_separator("Available Perpetual Markets")
        markets = await client.info.get_perp_markets()
        print(markets)

        print_separator(f"{market_id} Market Snapshot")
        market_details = await client.info.get_perp_market_by_id(market_id)
        print(market_details)

        print_separator(f"Recent {market_id} Trades")
        trades = await client.info.get_perp_trades(market_id)
        if trades:
            for trade in trades[:5]:
                print(f"Price: {trade['price']}, Size: {trade['size']}, Side: {trade['side']}")
        else:
            print("No trades found for this market yet.")

        print_separator("Funding Perp Account")
        margin_balance_atomic = await client.execution.perp_get_margin_balance(0)
        margin_balance = atomic_to_decimal(margin_balance_atomic)
        print(f"Current subaccount 0 margin balance: {margin_balance} capUSD")

        if margin_balance == 0:
            deposit_amount = Decimal("1000")
            print(f"No margin available. Depositing {deposit_amount} capUSD and allocating to subaccount 0.")
            deposit_tx = await client.execution.perp_deposit(deposit_amount)
            print(f"Perp deposit transaction: {deposit_tx}")
            if not await wait_for_completion(client.execution, deposit_tx, "perp deposit"):
                return

            margin_tx = await client.execution.perp_add_margin(subaccount=0, amount=deposit_amount)
            print(f"Add margin transaction: {margin_tx}")
            if not await wait_for_completion(client.execution, margin_tx, "add margin"):
                return
            margin_balance_atomic = await client.execution.perp_get_margin_balance(0)
            margin_balance = atomic_to_decimal(margin_balance_atomic)
            print(f"Updated subaccount 0 margin balance: {margin_balance} capUSD")

        if margin_balance == 0:
            print("Unable to fund margin for subaccount 0. Ensure collateral is deposited before trading.")
            return

        print_separator("Placing FAKEBTCUSD Perp Order")
        mark_price_atomic = await client.execution.perp_get_mark_price(market_id)
        mark_price = atomic_to_decimal(mark_price_atomic)
        if mark_price == 0:
            # Fallback to an arbitrary price if mark price is unavailable.
            mark_price = Decimal("100_000")
        order_price = (mark_price * Decimal("1.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        order_size = Decimal("0.01")
        print(f"Using limit price {order_price} and size {order_size} BTC")
        order_receipt = await client.execution.perp_place_order(
            asset=market_id,
            side=Side.BUY,
            amount=order_size,
            limit_price=order_price,
            subaccount=0,
            tif=TiF.GTC,
        )
        print(order_receipt)


async def wait_for_completion(execution_client: Any, tx_hash: str, action: str) -> bool:
    """Wait for a transaction to complete and report its status."""
    try:
        print(f"Waiting for {action} confirmation...")
        receipt = await execution_client._scheduler.wait_for_receipt(HexBytes(tx_hash))
    except Exception as error:  # pragma: no cover - network interaction
        print(f"Failed to confirm {action}: {error}")
        return False

    status = receipt.get("status")
    if status != 1:
        print(f"{action.capitalize()} reverted. Transaction receipt: {receipt}")
        await _print_revert_reason(execution_client, tx_hash)
        return False

    print(f"{action.capitalize()} confirmed in block {receipt.get('blockNumber')}")
    return True


async def _print_revert_reason(execution_client: Any, tx_hash: str) -> None:
    """Surface the revert reason by replaying the transaction locally."""
    try:
        sync_web3 = _get_sync_web3(execution_client)
    except Exception as error:  # pragma: no cover - diagnostic output
        print(f"Revert reason: <could not prepare web3 client: {error}>")
        return

    try:
        reason = await asyncio.to_thread(
            fetch_transaction_revert_reason,
            sync_web3,
            HexBytes(tx_hash),
            False,
            "<could not extract the revert reason>",
        )
    except Exception as error:  # pragma: no cover - diagnostic output
        print(f"Revert reason: <fetch failed: {error}>")
        return

    print(f"Revert reason: {reason}")


_SYNC_WEB3: Web3 | None = None


def _get_sync_web3(execution_client: Any) -> Web3:
    """Initialise (once) a synchronous Web3 client for revert lookups."""
    global _SYNC_WEB3
    if _SYNC_WEB3 is not None:
        return _SYNC_WEB3

    endpoint_uri = getattr(execution_client._config, "rpc_http", None)
    if endpoint_uri is None:
        provider = getattr(execution_client._scheduler.web3, "provider", None)
        endpoint_uri = getattr(provider, "endpoint_uri", None)
    if endpoint_uri is None:
        raise RuntimeError("Unable to determine RPC endpoint for revert reason lookup")

    _SYNC_WEB3 = Web3(Web3.HTTPProvider(endpoint_uri))
    return _SYNC_WEB3


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
