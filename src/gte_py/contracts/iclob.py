from typing import Any

from eth_typing import ChecksumAddress
from web3 import Web3

from .structs import (
    FillOrderType,
    ICLOBCancelArgs,
    ICLOBPostFillOrderArgs,
    ICLOBPostLimitOrderArgs,
    ICLOBReduceArgs,
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
    - Deposit and withdrawal
    - Posting limit orders
    - Posting fill orders
    - Order management (cancel, reduce)
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
        Initialize the GTECLOB wrapper.

        Args:
            web3: Web3 instance connected to a provider
            contract_address: Address of the CLOB contract
            abi_path: Path to the ABI JSON file (optional)
            abi: The contract ABI as a Python dictionary (optional)
        """
        self.web3 = web3
        self.address = web3.to_checksum_address(contract_address)
        loaded_abi = get_abi("GTECLOB", abi_path, abi)
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

    def get_token_config(self) -> dict[str, Any]:
        """Get the token configuration settings for the CLOB."""
        return self.contract.functions.getTokenConfig().call()

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

    def get_limit(self, price_in_ticks: int, side: int) -> dict[str, Any]:
        """
        Get the limit level details at a specific price level for a given side.

        Args:
            price_in_ticks: The price level in ticks
            side: The side (BUY=0, SELL=1)

        Returns:
            Limit details as a dictionary
        """
        return self.contract.functions.getLimit(price_in_ticks, side).call()

    def get_num_bids(self) -> int:
        """Get the total number of bid orders in the order book."""
        return self.contract.functions.getNumBids().call()

    def get_num_asks(self) -> int:
        """Get the total number of ask orders in the order book."""
        return self.contract.functions.getNumAsks().call()

    def get_next_biggest_tick(self, price_in_ticks: int, side: int) -> int:
        """
        Get the next biggest price tick for a given side.

        Args:
            price_in_ticks: The current price level in ticks
            side: The side (BUY=0, SELL=1)

        Returns:
            The next biggest price tick
        """
        return self.contract.functions.getNextBiggestTick(price_in_ticks, side).call()

    def get_next_smallest_tick(self, price_in_ticks: int, side: int) -> int:
        """
        Get the next smallest price tick for a given side.

        Args:
            price_in_ticks: The current price level in ticks
            side: The side (BUY=0, SELL=1)

        Returns:
            The next smallest price tick
        """
        return self.contract.functions.getNextSmallestTick(price_in_ticks, side).call()

    def get_orders(self, start_order_id: int, num_orders: int) -> list[dict[str, Any]]:
        """
        Get a list of orders starting from a specific order ID.

        Args:
            start_order_id: The starting order ID
            num_orders: The number of orders to retrieve

        Returns:
            List of order details
        """
        return self.contract.functions.getOrders(start_order_id, num_orders).call()

    def get_quote_token_account_balance(self, account: str) -> int:
        """
        Get the quote token balance of a specific account.

        Args:
            account: The address of the account

        Returns:
            The quote token balance in atoms
        """
        account = self.web3.to_checksum_address(account)
        return self.contract.functions.getQuoteTokenAccountBalance(account).call()

    def get_base_token_account_balance(self, account: str) -> int:
        """
        Get the base token balance of a specific account.

        Args:
            account: The address of the account

        Returns:
            The base token balance in atoms
        """
        account = self.web3.to_checksum_address(account)
        return self.contract.functions.getBaseTokenAccountBalance(account).call()

    def get_next_order_id(self) -> int:
        """Get the next order ID that will be assigned to a new order."""
        return self.contract.functions.getNextOrderId().call()

    def get_factory(self) -> ChecksumAddress:
        """Get the address of the factory associated with the CLOB."""
        return self.contract.functions.getFactory().call()

    def get_factory_owner(self) -> ChecksumAddress:
        """Get the owner of the factory associated with the CLOB."""
        return self.contract.functions.getFactoryOwner().call()

    def get_fee_recipient(self) -> ChecksumAddress:
        """Get the address designated to receive fees on the CLOB."""
        return self.contract.functions.getFeeRecipient().call()

    # ================= WRITE METHODS =================

    def deposit(
        self, token_address: str, amount: int, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Deposit tokens into the CLOB.

        Args:
            token_address: Address of the token to deposit
            amount: Amount of tokens to deposit
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        token_address = self.web3.to_checksum_address(token_address)
        tx = self.contract.functions.deposit(token_address, amount).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def withdraw(
        self, token_address: str, amount: int, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Withdraw tokens from the CLOB.

        Args:
            token_address: Address of the token to withdraw
            amount: Amount of tokens to withdraw
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        token_address = self.web3.to_checksum_address(token_address)
        tx = self.contract.functions.withdraw(token_address, amount).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def post_limit_order(
        self, args: ICLOBPostLimitOrderArgs, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Post a limit order to the CLOB.

        Args:
            args: PostLimitOrderArgs struct with order details
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.postLimitOrder(args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def post_fill_order(
        self, args: ICLOBPostFillOrderArgs, sender_address: str, **kwargs
    ) -> dict[str, Any]:
        """
        Post a fill order to the CLOB.

        Args:
            args: PostFillOrderArgs struct with order details
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.postFillOrder(args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def reduce(self, args: ICLOBReduceArgs, sender_address: str, **kwargs) -> dict[str, Any]:
        """
        Reduce the amount of an existing order.

        Args:
            args: ReduceArgs struct with order details
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.reduce(args).build_transaction(
            {
                "from": sender_address,
                "nonce": self.web3.eth.get_transaction_count(sender_address),
                **kwargs,
            }
        )
        return tx

    def cancel(self, args: ICLOBCancelArgs, sender_address: str, **kwargs) -> dict[str, Any]:
        """
        Cancel one or more orders.

        Args:
            args: CancelArgs struct with order IDs and settlement type
            sender_address: Address of the transaction sender
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            Transaction object
        """
        tx = self.contract.functions.cancel(args).build_transaction(
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
        amount_in_base_lots: int,
        price_in_ticks: int,
        side: int,
        limit_order_type: int = LimitOrderType.GOOD_TILL_CANCELLED,
        settlement: int = Settlement.INSTANT,
        cancel_timestamp: int = 0,
    ) -> ICLOBPostLimitOrderArgs:
        """
        Create a PostLimitOrderArgs struct for use with post_limit_order.

        Args:
            amount_in_base_lots: The size of the order in base lots
            price_in_ticks: The price of the order in ticks
            side: BUY(0) or SELL(1)
            limit_order_type: Type of limit order (default: GOOD_TILL_CANCELLED)
            settlement: Settlement type (default: INSTANT)
            cancel_timestamp: Timestamp after which the order is automatically canceled (0 = never)

        Returns:
            PostLimitOrderArgs struct
        """
        return {
            "amountInBaseLots": amount_in_base_lots,
            "priceInTicks": price_in_ticks,
            "cancelTimestamp": cancel_timestamp,
            "side": side,
            "limitOrderType": limit_order_type,
            "settlement": settlement,
        }

    def create_post_fill_order_args(
        self,
        amount_in_base_lots: int,
        price_in_ticks: int,
        side: int,
        fill_order_type: int = FillOrderType.IMMEDIATE_OR_CANCEL,
        settlement: int = Settlement.INSTANT,
    ) -> ICLOBPostFillOrderArgs:
        """
        Create a PostFillOrderArgs struct for use with post_fill_order.

        Args:
            amount_in_base_lots: The size of the order in base lots
            price_in_ticks: The price of the order in ticks
            side: BUY(0) or SELL(1)
            fill_order_type: Type of fill order (default: IMMEDIATE_OR_CANCEL)
            settlement: Settlement type (default: INSTANT)

        Returns:
            PostFillOrderArgs struct
        """
        return {
            "amountInBaseLots": amount_in_base_lots,
            "priceInTicks": price_in_ticks,
            "side": side,
            "fillOrderType": fill_order_type,
            "settlement": settlement,
        }

    def create_reduce_args(
        self, order_id: int, amount_in_base_lots: int, settlement: int = Settlement.INSTANT
    ) -> ICLOBReduceArgs:
        """
        Create a ReduceArgs struct for use with reduce.

        Args:
            order_id: The ID of the order to reduce
            amount_in_base_lots: The amount by which to reduce the order
            settlement: Settlement type (default: INSTANT)

        Returns:
            ReduceArgs struct
        """
        return {
            "orderId": order_id,
            "amountInBaseLots": amount_in_base_lots,
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
