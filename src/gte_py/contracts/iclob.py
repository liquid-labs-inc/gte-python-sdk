from typing import Any

from eth_typing import ChecksumAddress
from web3 import Web3

from .structs import (
    FillOrderType,
    ICLOBAmendArgs,
    ICLOBCancelArgs,
    ICLOBPostFillOrderArgs,
    ICLOBPostLimitOrderArgs,
    LimitOrderType,
    Settlement,
)


class CLOBError(Exception):
    """Base exception for CLOB contract errors"""

    pass


class ICLOB:
    """
    Python wrapper for the GTE CLOB (Central Limit Order Book) smart contract.
    Provides methods to interact with the CLOB functionality including:
    - Posting limit orders
    - Posting fill orders
    - Order management (amend, cancel)
    - Order book information retrieval
    """

    def __init__(
        self,
        web3: Web3,
        contract_address: str,
        abi_path: str | None = None,
        abi: list[dict[str, Any]] | None = None,
    ):
        """
        Initialize the ICLOB wrapper.

        Args:
            web3: Web3 instance connected to a provider
            contract_address: Address of the CLOB contract
            abi_path: Path to the ABI JSON file (optional)
            abi: The contract ABI as a Python dictionary (optional)
        """
        self.web3 = web3
        self.address = web3.to_checksum_address(contract_address)
        loaded_abi = get_abi("iclob", abi_path, abi)
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

    # ================= READ METHODS =================

    def get_quote_token(self) -> ChecksumAddress:
        """Get the quote token used in the CLOB."""
        return self.contract.functions.getQuoteToken().call()

    def get_base_token(self) -> ChecksumAddress:
        """Get the base token used in the CLOB."""
        return self.contract.functions.getBaseToken().call()

    def get_market_config(self) -> dict[str, Any]:
        """Get the market configuration settings for the CLOB."""
        return self.contract.functions.getMarketConfig().call()

    def get_market_settings(self) -> dict[str, Any]:
        """Get the market settings for the CLOB."""
        return self.contract.functions.getMarketSettings().call()

    def get_open_interest(self) -> tuple[int, int]:
        """
        Get the current open interest for both quote and base tokens.

        Returns:
            Tuple of (quote_open_interest, base_open_interest) in atoms
        """
        return self.contract.functions.getOpenInterest().call()

    def get_order(self, order_id: int) -> dict[str, Any]:
        """
        Get the details of a specific order.

        Args:
            order_id: The unique identifier of the order

        Returns:
            Order details as a dictionary
        """
        return self.contract.functions.getOrder(order_id).call()

    def get_tob(self) -> tuple[int, int]:
        """
        Get the top of book prices for both bid and ask sides.

        Returns:
            Tuple of (highest_bid_price, lowest_ask_price) in ticks
        """
        return self.contract.functions.getTOB().call()

    def get_limit(self, price: int, side: int) -> dict[str, Any]:
        """
        Get the limit level details at a specific price level for a given side.

        Args:
            price: The price level
            side: The side (BUY=0, SELL=1)

        Returns:
            Limit details as a dictionary
        """
        return self.contract.functions.getLimit(price, side).call()

    def get_num_bids(self) -> int:
        """Get the total number of bid orders in the order book."""
        return self.contract.functions.getNumBids().call()

    def get_num_asks(self) -> int:
        """Get the total number of ask orders in the order book."""
        return self.contract.functions.getNumAsks().call()

    def get_next_biggest_price(self, price: int, side: int) -> int:
        """
        Get the next biggest price for a given side.

        Args:
            price: The current price level
            side: The side (BUY=0, SELL=1)

        Returns:
            The next biggest price
        """
        return self.contract.functions.getNextBiggestPrice(price, side).call()

    def get_next_smallest_price(self, price: int, side: int) -> int:
        """
        Get the next smallest price for a given side.

        Args:
            price: The current price level
            side: The side (BUY=0, SELL=1)

        Returns:
            The next smallest price
        """
        return self.contract.functions.getNextSmallestPrice(price, side).call()

    def get_next_orders(self, start_order_id: int, num_orders: int) -> list[dict[str, Any]]:
        """
        Get a list of orders starting from a specific order ID.

        Args:
            start_order_id: The starting order ID
            num_orders: The number of orders to retrieve

        Returns:
            List of order details
        """
        return self.contract.functions.getNextOrders(start_order_id, num_orders).call()

    def get_next_order_id(self) -> int:
        """Get the next order ID that will be assigned to a new order."""
        return self.contract.functions.getNextOrderId().call()

    def get_factory(self) -> ChecksumAddress:
        """Get the address of the factory associated with the CLOB."""
        return self.contract.functions.getFactory().call()

    def get_base_token_amount(self, price: int, quote_amount: int) -> int:
        """
        Calculate the base token amount for a given price and quote token amount.

        Args:
            price: The price
            quote_amount: The quote token amount

        Returns:
            The base token amount
        """
        return self.contract.functions.getBaseTokenAmount(price, quote_amount).call()

    def get_quote_token_amount(self, price: int, base_amount: int) -> int:
        """
        Calculate the quote token amount for a given price and base token amount.

        Args:
            price: The price
            base_amount: The base token amount

        Returns:
            The quote token amount
        """
        return self.contract.functions.getQuoteTokenAmount(price, base_amount).call()

    def get_event_nonce(self) -> int:
        """Get the current event nonce."""
        return self.contract.functions.getEventNonce().call()

    def get_max_limit_exempt(self, account: str) -> bool:
        """
        Check if an account is exempt from the max limit restriction.

        Args:
            account: The address of the account

        Returns:
            True if the account is exempt, False otherwise
        """
        account = self.web3.to_checksum_address(account)
        return self.contract.functions.getMaxLimitExempt(account).call()

    def owner(self) -> ChecksumAddress:
        """Get the owner of the CLOB contract."""
        return self.contract.functions.owner().call()

    def pending_owner(self) -> ChecksumAddress:
        """Get the pending owner of the CLOB contract."""
        return self.contract.functions.pendingOwner().call()

    # ================= WRITE METHODS =================

    def post_limit_order(
        self, account: str, args: ICLOBPostLimitOrderArgs, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Post a limit order to the CLOB.

        Args:
            account: Address of the account to post the order for
            args: PostLimitOrderArgs struct with order details
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        account = self.web3.to_checksum_address(account)
        tx = self.contract.functions.postLimitOrder(account, args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def post_fill_order(
        self, account: str, args: ICLOBPostFillOrderArgs, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Post a fill order to the CLOB.

        Args:
            account: Address of the account to post the order for
            args: PostFillOrderArgs struct with order details
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        account = self.web3.to_checksum_address(account)
        tx = self.contract.functions.postFillOrder(account, args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def amend(
        self, account: str, args: ICLOBAmendArgs, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Amend an existing order.

        Args:
            account: Address of the account that owns the order
            args: AmendArgs struct with order details
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        account = self.web3.to_checksum_address(account)
        tx = self.contract.functions.amend(account, args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def cancel(
        self, account: str, args: ICLOBCancelArgs, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Cancel one or more orders.

        Args:
            account: Address of the account that owns the orders
            args: CancelArgs struct with order IDs and settlement type
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        account = self.web3.to_checksum_address(account)
        tx = self.contract.functions.cancel(account, args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def accept_ownership(self, sender_address: str, **kwargs) -> dict[str, Any]:
        """
        Accept ownership of the contract.

        Args:
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.acceptOwnership().build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def renounce_ownership(self, sender_address: str, **kwargs) -> dict[str, Any]:
        """
        Renounce ownership of the contract.

        Args:
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.renounceOwnership().build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def transfer_ownership(self, new_owner: str, sender_address: str, **kwargs) -> dict[str, Any]:
        """
        Transfer ownership of the contract.

        Args:
            new_owner: Address of the new owner
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        new_owner = self.web3.to_checksum_address(new_owner)
        tx = self.contract.functions.transferOwnership(new_owner).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def set_max_limits_exempt(
        self, account: str, toggle: bool, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Set whether an account is exempt from the max limits restriction.

        Args:
            account: Address of the account
            toggle: True to exempt, False to not exempt
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        account = self.web3.to_checksum_address(account)
        tx = self.contract.functions.setMaxLimitsExempt(account, toggle).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def set_max_limits_per_tx(
        self, new_max_limits: int, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Set the maximum number of limit orders allowed per transaction.

        Args:
            new_max_limits: The new maximum number of limits per transaction
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.setMaxLimitsPerTx(new_max_limits).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def set_min_limit_order_amount_in_base(
        self, new_min_amount: int, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Set the minimum amount in base for limit orders.

        Args:
            new_min_amount: The new minimum amount in base
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.setMinLimitOrderAmountInBase(
            new_min_amount
        ).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def set_tick_size(self, tick_size: int, sender_address: str, **kwargs) -> dict[str, Any]:
        """
        Set the tick size for the CLOB.

        Args:
            tick_size: The new tick size
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.setTickSize(tick_size).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    # ================= HELPER METHODS =================

    def create_post_limit_order_args(
        self,
        amount_in_base: int,
        price: int,
        side: int,
        cancel_timestamp: int = 0,
        limit_order_type: int = LimitOrderType.GOOD_TILL_CANCELLED,
        settlement: int = Settlement.INSTANT,
    ) -> ICLOBPostLimitOrderArgs:
        """
        Create a PostLimitOrderArgs struct for use with post_limit_order.

        Args:
            amount_in_base: The size of the order in base tokens
            price: The price of the order
            side: BUY(0) or SELL(1)
            cancel_timestamp: Timestamp after which the order is automatically canceled (0 = never)
            limit_order_type: Type of limit order (default: GOOD_TILL_CANCELLED)
            settlement: Settlement type (default: INSTANT)

        Returns:
            PostLimitOrderArgs struct
        """
        return {
            "amountInBase": amount_in_base,
            "price": price,
            "cancelTimestamp": cancel_timestamp,
            "side": side,
            "limitOrderType": limit_order_type,
            "settlement": settlement,
        }

    def create_post_fill_order_args(
        self,
        amount: int,
        price_limit: int,
        side: int,
        amount_is_base: bool = True,
        fill_order_type: int = FillOrderType.IMMEDIATE_OR_CANCEL,
        settlement: int = Settlement.INSTANT,
    ) -> ICLOBPostFillOrderArgs:
        """
        Create a PostFillOrderArgs struct for use with post_fill_order.

        Args:
            amount: The size of the order
            price_limit: The price limit of the order
            side: BUY(0) or SELL(1)
            amount_is_base: Whether the amount is in base tokens (True) or quote tokens (False)
            fill_order_type: Type of fill order (default: IMMEDIATE_OR_CANCEL)
            settlement: Settlement type (default: INSTANT)

        Returns:
            PostFillOrderArgs struct
        """
        return {
            "amount": amount,
            "priceLimit": price_limit,
            "side": side,
            "amountIsBase": amount_is_base,
            "fillOrderType": fill_order_type,
            "settlement": settlement,
        }

    def create_amend_args(
        self,
        order_id: int,
        amount_in_base: int,
        price: int,
        side: int,
        cancel_timestamp: int = 0,
        limit_order_type: int = LimitOrderType.GOOD_TILL_CANCELLED,
        settlement: int = Settlement.INSTANT,
    ) -> ICLOBAmendArgs:
        """
        Create an AmendArgs struct for use with amend.

        Args:
            order_id: The ID of the order to amend
            amount_in_base: The new size of the order in base tokens
            price: The new price of the order
            side: BUY(0) or SELL(1)
            cancel_timestamp: New timestamp after which the order is automatically canceled (0 = never)
            limit_order_type: Type of limit order (default: GOOD_TILL_CANCELLED)
            settlement: Settlement type (default: INSTANT)

        Returns:
            AmendArgs struct
        """
        return {
            "orderId": order_id,
            "amountInBase": amount_in_base,
            "price": price,
            "cancelTimestamp": cancel_timestamp,
            "side": side,
            "limitOrderType": limit_order_type,
            "settlement": settlement,
        }

    def create_cancel_args(
        self, order_ids: list[int], settlement: int = Settlement.INSTANT
    ) -> ICLOBCancelArgs:
        """
        Create a CancelArgs struct for use with cancel.

        Args:
            order_ids: List of order IDs to cancel
            settlement: Settlement type (default: INSTANT)

        Returns:
            CancelArgs struct
        """
        return {"orderIds": order_ids, "settlement": settlement}
