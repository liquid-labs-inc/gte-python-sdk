from typing import TypeVar, Union, List, Dict, Optional, AsyncIterator, Any, Tuple, Callable

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams
from .event_source import EventSource, EventStream
from .events import (
    LimitOrderSubmittedEvent,
    LimitOrderProcessedEvent,
    FillOrderSubmittedEvent,
    FillOrderProcessedEvent,
    OrderAmendedEvent,
    OrderCanceledEvent,
    OrderMatchedEvent,
    TickSizeUpdatedEvent,
    MinLimitOrderAmountInBaseUpdatedEvent,
    MaxLimitOrdersPerTxUpdatedEvent,
    MaxLimitOrdersAllowlistedEvent,
    CancelFailedEvent,
    InitializedEvent,
    OwnershipTransferStartedEvent,
    ClobOwnershipTransferredEvent,
    parse_limit_order_submitted,
    parse_limit_order_processed,
    parse_fill_order_submitted,
    parse_fill_order_processed,
    parse_order_amended,
    parse_order_canceled,
    parse_order_matched,
    parse_tick_size_updated,
    parse_min_limit_order_amount_in_base_updated,
    parse_max_limit_orders_per_tx_updated,
    parse_max_limit_orders_allowlisted,
    parse_cancel_failed,
    parse_initialized,
    parse_ownership_transfer_started,
    parse_clob_ownership_transferred,
)
from .structs import (
    FillOrderType,
    ICLOBAmendArgs,
    ICLOBCancelArgs,
    ICLOBPostFillOrderArgs,
    ICLOBPostLimitOrderArgs,
    LimitOrderType,
    Settlement,
    CLOBOrder,
    OrderSide,
)
from .utils import TypedContractFunction, load_abi

# Type variable for contract function return types
T = TypeVar("T")



class ICLOB:
    """
    Python wrapper for the GTE CLOB (Central Limit Order Book) smart contract.
    Provides methods to interact with the CLOB functionality including:
    - Posting limit orders
    - Posting fill orders
    - Order management (amend, cancel)
    - Order book information retrieval
    - Historical event queries
    - Real-time event streaming
    """

    def __init__(
            self,
            web3: AsyncWeb3,
            contract_address: ChecksumAddress,
    ):
        """
        Initialize the ICLOB wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the CLOB contract
        """
        self.web3 = web3
        self.address = contract_address
        loaded_abi = load_abi("clob")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

        # Initialize event sources
        self._limit_order_submitted_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.LimitOrderSubmitted,
            parser=parse_limit_order_submitted
        )

        self._limit_order_processed_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.LimitOrderProcessed,
            parser=parse_limit_order_processed
        )

        self._fill_order_submitted_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.FillOrderSubmitted,
            parser=parse_fill_order_submitted
        )

        self._fill_order_processed_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.FillOrderProcessed,
            parser=parse_fill_order_processed
        )

        self._order_amended_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OrderAmended,
            parser=parse_order_amended
        )

        self._order_canceled_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OrderCanceled,
            parser=parse_order_canceled
        )

        self._order_matched_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OrderMatched,
            parser=parse_order_matched
        )

        self._tick_size_updated_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.TickSizeUpdated,
            parser=parse_tick_size_updated
        )

        self._min_limit_order_amount_in_base_updated_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.MinLimitOrderAmountInBaseUpdated,
            parser=parse_min_limit_order_amount_in_base_updated
        )

        self._max_limit_orders_per_tx_updated_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.MaxLimitOrdersPerTxUpdated,
            parser=parse_max_limit_orders_per_tx_updated
        )

        self._max_limit_orders_allowlisted_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.MaxLimitOrdersAllowlisted,
            parser=parse_max_limit_orders_allowlisted
        )

        self._cancel_failed_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.CancelFailed,
            parser=parse_cancel_failed
        )

        self._initialized_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.Initialized,
            parser=parse_initialized
        )

        self._ownership_transfer_started_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OwnershipTransferStarted,
            parser=parse_ownership_transfer_started
        )

        self._ownership_transferred_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OwnershipTransferred,
            parser=parse_clob_ownership_transferred
        )

    # ================= READ METHODS =================

    async def abi_version(self) -> int:
        """Get the ABI version of the contract."""
        return await self.contract.functions.ABI_VERSION().call()

    async def get_quote_token(self) -> ChecksumAddress:
        """Get the quote token used in the CLOB."""
        return await self.contract.functions.getQuoteToken().call()

    async def get_base_token(self) -> ChecksumAddress:
        """Get the base token used in the CLOB."""
        return await self.contract.functions.getBaseToken().call()

    async def get_market_config(
            self,
    ) -> tuple[ChecksumAddress, int, ChecksumAddress, ChecksumAddress, int, int]:
        """Get the market configuration settings for the CLOB."""
        return await self.contract.functions.getMarketConfig().call()

    async def get_market_settings(self) -> tuple[bool, int, int, int]:
        """
        Get the market settings for the CLOB.
        Returns:
            A tuple containing:
            - status (bool): Whether the market is active
            - maxLimitsPerTx (int): Maximum number of limit orders allowed per transaction
            - minLimitOrderAmountInBase (int): Minimum amount for limit orders in base tokens
            - tickSize (int): Tick size for price increments
        """
        return await self.contract.functions.getMarketSettings().call()

    async def get_open_interest(self) -> tuple[int, int]:
        """
        Get the current open interest for both quote and base tokens.

        Returns:
            Tuple of (quote_open_interest, base_open_interest) in atoms
        """
        return await self.contract.functions.getOpenInterest().call()

    async def get_order(self, order_id: int) -> CLOBOrder:
        """
        Get the details of a specific order.

        Args:
            order_id: The unique identifier of the order

        Returns:
            Order details as a dictionary
        """
        tpl = await self.contract.functions.getOrder(order_id).call()
        return CLOBOrder.from_tuple(tpl)

    async def get_tob(self) -> tuple[int, int]:
        """
        Get the top of book prices for both bid and ask sides.

        Returns:
            Tuple of (highest_bid_price, lowest_ask_price) in ticks
        """
        return await self.contract.functions.getTOB().call()

    async def get_limit(self, price: int, side: OrderSide) -> tuple[int, int, int]:
        """
        Get the limit level details at a specific price level for a given side.
        Args:
            price: The price level
            side: The side (BUY=0, SELL=1)

        Returns:
            Tuple of (num_orders, head_order_id, tail_order_id)
        """
        return await self.contract.functions.getLimit(price, side).call()

    async def get_num_bids(self) -> int:
        """Get the total number of bid orders in the order book."""
        return await self.contract.functions.getNumBids().call()

    async def get_num_asks(self) -> int:
        """Get the total number of ask orders in the order book."""
        return await self.contract.functions.getNumAsks().call()

    async def get_next_biggest_price(self, price: int, side: OrderSide) -> int:
        """
        Get the next biggest price for a given side.

        Args:
            price: The current price level
            side: The side (BUY=0, SELL=1)

        Returns:
            The next biggest price
        """
        return await self.contract.functions.getNextBiggestPrice(price, side).call()

    async def get_next_smallest_price(self, price: int, side: OrderSide) -> int:
        """
        Get the next smallest price for a given side.

        Args:
            price: The current price level
            side: The side (BUY=0, SELL=1)

        Returns:
            The next smallest price
        """
        return await self.contract.functions.getNextSmallestPrice(price, side).call()

    async def get_next_orders(self, start_order_id: int, num_orders: int) -> list[CLOBOrder]:
        """
        Get a list of orders starting from a specific order ID.

        Args:
            start_order_id: The starting order ID
            num_orders: The number of orders to retrieve

        Returns:
            List of order details
        """
        orders = await self.contract.functions.getNextOrders(start_order_id, num_orders).call()
        return [CLOBOrder.from_tuple(order) for order in orders]

    async def get_next_order_id(self) -> int:
        """Get the next order ID that will be assigned to a new order."""
        return await self.contract.functions.getNextOrderId().call()

    async def get_factory(self) -> ChecksumAddress:
        """Get the address of the factory associated with the CLOB."""
        return await self.contract.functions.getFactory().call()

    async def get_base_token_amount(self, price: int, quote_amount: int) -> int:
        """
        Calculate the base token amount for a given price and quote token amount.

        Args:
            price: The price
            quote_amount: The quote token amount

        Returns:
            The base token amount
        """
        return await self.contract.functions.getBaseTokenAmount(price, quote_amount).call()

    async def get_quote_token_amount(self, price: int, base_amount: int) -> int:
        """
        Calculate the quote token amount for a given price and base token amount.

        Args:
            price: The price
            base_amount: The base token amount

        Returns:
            The quote token amount
        """
        return await self.contract.functions.getQuoteTokenAmount(price, base_amount).call()

    async def get_tick_size(self) -> int:
        """Get the tick size for the CLOB."""
        return await self.contract.functions.getTickSize().call()

    async def get_event_nonce(self) -> int:
        """Get the current event nonce."""
        return await self.contract.functions.getEventNonce().call()

    async def get_max_limit_exempt(self, account: ChecksumAddress) -> bool:
        """
        Check if an account is exempt from the max limit restriction.

        Args:
            account: The address of the account

        Returns:
            True if the account is exempt, False otherwise
        """
        return await self.contract.functions.getMaxLimitExempt(account).call()

    async def owner(self) -> ChecksumAddress:
        """Get the owner of the CLOB contract."""
        return await self.contract.functions.owner().call()

    async def pending_owner(self) -> ChecksumAddress:
        """Get the pending owner of the CLOB contract."""
        return await self.contract.functions.pendingOwner().call()
    
    async def gte_router(self) -> ChecksumAddress:
        """Get the GTE router associated with the CLOB."""
        return await self.contract.functions.gteRouter().call()

    # ================= WRITE METHODS =================

    def initialize(
            self, market_config: Dict[str, Any], market_settings: Dict[str, Any], initial_owner: ChecksumAddress,
            **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Initialize the CLOB contract.

        Args:
            market_config: Market configuration parameters
            market_settings: Market settings parameters
            initial_owner: The initial owner address
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.initialize(market_config, market_settings, initial_owner)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def post_limit_order(
            self, account: ChecksumAddress, args: ICLOBPostLimitOrderArgs, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[LimitOrderProcessedEvent]:
        """
        Post a limit order to the CLOB.

        Args:
            account: Address to use as the 'account' parameter in the ABI. This must be:
                - The router contract's address if called from the router
                - The user's address if called directly
            args: PostLimitOrderArgs struct with order details
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.postLimitOrder(account, tuple(args))
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.LimitOrderProcessed, parse_limit_order_processed
        )

    def post_fill_order(
            self, account: ChecksumAddress, args: ICLOBPostFillOrderArgs, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[FillOrderProcessedEvent]:
        """
        Post a fill order to the CLOB.

        Args:
            account: Address to use as the 'account' parameter in the ABI. This must be:
                - The router contract's address if called from the router
                - The user's address if called directly
            args: PostFillOrderArgs struct with order details
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.postFillOrder(account, tuple(args))
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.FillOrderProcessed, parse_fill_order_processed
        )

    def amend(
            self, account: ChecksumAddress, args: ICLOBAmendArgs, **kwargs
    ) -> TypedContractFunction[OrderAmendedEvent]:
        """
        Amend an existing order.

        Args:
            account: Address to use as the 'account' parameter in the ABI. This must be:
                - The router contract's address if called from the router
                - The user's address if called directly
            args: AmendArgs struct with order details
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.amend(account, tuple(args))
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def cancel(
            self, account: ChecksumAddress, args: ICLOBCancelArgs, **kwargs
    ) -> TypedContractFunction[OrderCanceledEvent]:
        """
        Cancel one or more orders.

        Args:
            account: Address to use as the 'account' parameter in the ABI. This must be:
                - The router contract's address if called from the router
                - The user's address if called directly
            args: CancelArgs struct with order IDs and settlement type
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.cancel(account, tuple(args))
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params).with_event(
            self.contract.events.OrderCanceled, parse_order_canceled
        )

    def accept_ownership(self, **kwargs) -> TypedContractFunction[None]:
        """
        Accept ownership of the contract.

        Args:
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.acceptOwnership()
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[None]:
        """
        Renounce ownership of the contract.

        Args:
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.renounceOwnership()
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def transfer_ownership(
            self, new_owner: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Transfer ownership of the contract.

        Args:
            new_owner: Address of the new owner
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.transferOwnership(new_owner)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def set_max_limits_exempt(
            self, account: ChecksumAddress, toggle: bool, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Set whether an account is exempt from the max limits restriction.

        Args:
            account: Address of the account
            toggle: True to exempt, False to not exempt
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.setMaxLimitsExempt(account, toggle)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def set_max_limits_per_tx(self, new_max_limits: int, **kwargs) -> TypedContractFunction[None]:
        """
        Set the maximum number of limit orders allowed per transaction.

        Args:
            new_max_limits: The new maximum number of limits per transaction
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.setMaxLimitsPerTx(new_max_limits)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def set_min_limit_order_amount_in_base(
            self, new_min_amount: int, **kwargs
    ) -> TypedContractFunction[None]:
        """
        Set the minimum amount in base for limit orders.

        Args:
            new_min_amount: The new minimum amount in base
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.setMinLimitOrderAmountInBase(new_min_amount)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    def set_tick_size(self, tick_size: int, **kwargs) -> TypedContractFunction[None]:
        """
        Set the tick size for the CLOB.

        Args:
            tick_size: The new tick size
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.setTickSize(tick_size)
        params = {
            **kwargs,
        }
        return TypedContractFunction(func, params)

    # ================= EVENT METHODS =================

    async def get_limit_order_submitted_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[LimitOrderSubmittedEvent]:
        """
        Get historical LimitOrderSubmitted events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of LimitOrderSubmitted events
        """
        return await self._limit_order_submitted_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_limit_order_submitted_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[LimitOrderSubmittedEvent]:
        """
        Stream LimitOrderSubmitted events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of LimitOrderSubmitted events
        """
        return self._limit_order_submitted_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_limit_order_processed_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[LimitOrderProcessedEvent]:
        """
        Get historical LimitOrderProcessed events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of LimitOrderProcessed events
        """
        return await self._limit_order_processed_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_limit_order_processed_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[LimitOrderProcessedEvent]:
        """
        Stream LimitOrderProcessed events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of LimitOrderProcessed events
        """
        return self._limit_order_processed_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_fill_order_submitted_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[FillOrderSubmittedEvent]:
        """
        Get historical FillOrderSubmitted events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of FillOrderSubmitted events
        """
        return await self._fill_order_submitted_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_fill_order_submitted_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[FillOrderSubmittedEvent]:
        """
        Stream FillOrderSubmitted events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of FillOrderSubmitted events
        """
        return self._fill_order_submitted_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_fill_order_processed_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[FillOrderProcessedEvent]:
        """
        Get historical FillOrderProcessed events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of FillOrderProcessed events
        """
        return await self._fill_order_processed_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_fill_order_processed_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[FillOrderProcessedEvent]:
        """
        Stream FillOrderProcessed events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of FillOrderProcessed events
        """
        return self._fill_order_processed_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_order_amended_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[OrderAmendedEvent]:
        """
        Get historical OrderAmended events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OrderAmended events
        """
        return await self._order_amended_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_order_amended_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[OrderAmendedEvent]:
        """
        Stream OrderAmended events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OrderAmended events
        """
        return self._order_amended_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_order_canceled_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[OrderCanceledEvent]:
        """
        Get historical OrderCanceled events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OrderCanceled events
        """
        return await self._order_canceled_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_order_canceled_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[OrderCanceledEvent]:
        """
        Stream OrderCanceled events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OrderCanceled events
        """
        return self._order_canceled_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_order_matched_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[OrderMatchedEvent]:
        """
        Get historical OrderMatched events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OrderMatched events
        """
        return await self._order_matched_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_order_matched_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[OrderMatchedEvent]:
        """
        Stream OrderMatched events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OrderMatched events
        """
        return self._order_matched_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_tick_size_updated_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[TickSizeUpdatedEvent]:
        """
        Get historical TickSizeUpdated events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of TickSizeUpdated events
        """
        return await self._tick_size_updated_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_tick_size_updated_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[TickSizeUpdatedEvent]:
        """
        Stream TickSizeUpdated events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of TickSizeUpdated events
        """
        return self._tick_size_updated_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_min_limit_order_amount_in_base_updated_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[MinLimitOrderAmountInBaseUpdatedEvent]:
        """
        Get historical MinLimitOrderAmountInBaseUpdated events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of MinLimitOrderAmountInBaseUpdated events
        """
        return await self._min_limit_order_amount_in_base_updated_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_min_limit_order_amount_in_base_updated_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[MinLimitOrderAmountInBaseUpdatedEvent]:
        """
        Stream MinLimitOrderAmountInBaseUpdated events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of MinLimitOrderAmountInBaseUpdated events
        """
        return self._min_limit_order_amount_in_base_updated_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_max_limit_orders_per_tx_updated_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[MaxLimitOrdersPerTxUpdatedEvent]:
        """
        Get historical MaxLimitOrdersPerTxUpdated events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of MaxLimitOrdersPerTxUpdated events
        """
        return await self._max_limit_orders_per_tx_updated_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_max_limit_orders_per_tx_updated_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[MaxLimitOrdersPerTxUpdatedEvent]:
        """
        Stream MaxLimitOrdersPerTxUpdated events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of MaxLimitOrdersPerTxUpdated events
        """
        return self._max_limit_orders_per_tx_updated_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_max_limit_orders_allowlisted_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[MaxLimitOrdersAllowlistedEvent]:
        """
        Get historical MaxLimitOrdersAllowlisted events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of MaxLimitOrdersAllowlisted events
        """
        return await self._max_limit_orders_allowlisted_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_max_limit_orders_allowlisted_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[MaxLimitOrdersAllowlistedEvent]:
        """
        Stream MaxLimitOrdersAllowlisted events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of MaxLimitOrdersAllowlisted events
        """
        return self._max_limit_orders_allowlisted_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_cancel_failed_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[CancelFailedEvent]:
        """
        Get historical CancelFailed events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of CancelFailed events
        """
        return await self._cancel_failed_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_cancel_failed_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[CancelFailedEvent]:
        """
        Stream CancelFailed events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of CancelFailed events
        """
        return self._cancel_failed_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_initialized_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[InitializedEvent]:
        """
        Get historical Initialized events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of Initialized events
        """
        return await self._initialized_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_initialized_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[InitializedEvent]:
        """
        Stream Initialized events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of Initialized events
        """
        return self._initialized_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_ownership_transfer_started_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[OwnershipTransferStartedEvent]:
        """
        Get historical OwnershipTransferStarted events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OwnershipTransferStarted events
        """
        return await self._ownership_transfer_started_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_ownership_transfer_started_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[OwnershipTransferStartedEvent]:
        """
        Stream OwnershipTransferStarted events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OwnershipTransferStarted events
        """
        return self._ownership_transfer_started_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_ownership_transferred_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[ClobOwnershipTransferredEvent]:
        """
        Get historical OwnershipTransferred events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OwnershipTransferred events
        """
        return await self._ownership_transferred_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_ownership_transferred_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[ClobOwnershipTransferredEvent]:
        """
        Stream OwnershipTransferred events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OwnershipTransferred events
        """
        return self._ownership_transferred_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    # ================= HELPER METHODS =================

    def create_post_limit_order_args(
            self,
            amount_in_base: int,
            price: int,
            side: OrderSide,
            cancel_timestamp: int = 0,
            client_order_id: int = 0,
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
            client_order_id: Optional client-side order ID for tracking
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
            "clientOrderId": client_order_id,
            "limitOrderType": limit_order_type,
            "settlement": settlement,
        }

    def create_post_fill_order_args(
            self,
            amount: int,
            price_limit: int,
            side: OrderSide,
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
            side: OrderSide,
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

    def contract_address(self) -> ChecksumAddress:
        """
        Helper to get the contract's own address (useful for router context).
        Returns:
            The address of this CLOB contract instance.
        """
        return self.address
