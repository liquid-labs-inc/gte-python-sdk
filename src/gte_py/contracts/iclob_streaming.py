"""
Event streaming module for CLOB contract events.

This module provides functionality to subscribe to and process events
from the CLOB (Central Limit Order Book) contract in real-time.
"""

from typing import Callable, Dict, List, Optional, TypeVar, Generic, Iterator, Union
import time
from web3 import Web3
from web3.types import EventData, LogReceipt

from .iclob import ICLOB
from .events import (
    LimitOrderProcessedEvent,
    FillOrderProcessedEvent,
    OrderAmendedEvent,
    OrderCanceledEvent,
    OrderMatchedEvent,
    parse_limit_order_processed,
    parse_fill_order_processed,
    parse_order_amended,
    parse_order_canceled,
    parse_order_matched,
)

T = TypeVar('T')


class EventStream(Generic[T]):
    """Generic class for handling event streams with filtering and processing."""
    
    def __init__(
        self,
        web3: Web3,
        event: object,
        parser: Callable[[Dict], T],
        from_block: int = 0,
        to_block: Union[int, str] = 'latest',
        poll_interval: float = 2.0,
    ):
        """
        Initialize an event stream for a specific event.
        
        Args:
            web3: Web3 instance
            event: Web3 contract event object
            parser: Function to parse raw event data into typed event objects
            from_block: Starting block number to fetch events from
            to_block: Ending block number or 'latest'
            poll_interval: Interval (in seconds) between poll requests for new events
        """
        self.web3 = web3
        self.event = event
        self.parser = parser
        self.from_block = from_block
        self.to_block = to_block
        self.poll_interval = poll_interval
        self.filter = None
        self._latest_processed_block = from_block
    
    def create_filter(self, **filter_params) -> 'EventStream[T]':
        """
        Create a filter for this event stream with given parameters.
        
        Args:
            **filter_params: Event filter parameters
            
        Returns:
            Self for method chaining
        """
        self.filter = self.event.createFilter(
            fromBlock=self.from_block,
            toBlock=self.to_block,
            **filter_params
        )
        return self
    
    def get_all_entries(self) -> List[T]:
        """
        Get all events matching the filter.
        
        Returns:
            List of parsed event objects
        """
        if not self.filter:
            self.create_filter()
        
        entries = self.filter.get_all_entries()
        return [self.parser(entry) for entry in entries]
    
    def get_new_entries(self) -> List[T]:
        """
        Get new events since the last check.
        
        Returns:
            List of new parsed event objects
        """
        if not self.filter:
            self.create_filter()
        
        entries = self.filter.get_new_entries()
        return [self.parser(entry) for entry in entries]
    
    def stream(self) -> Iterator[T]:
        """
        Stream events as they occur.
        
        Yields:
            Parsed event objects as they occur
        """
        if not self.filter:
            self.create_filter()
        
        while True:
            for entry in self.get_new_entries():
                yield entry
            time.sleep(self.poll_interval)
    
    def process_events(self, handler: Callable[[T], None], exit_condition: Optional[Callable[[], bool]] = None):
        """
        Process events using a handler function until an optional exit condition is met.
        
        Args:
            handler: Function to call for each event
            exit_condition: Optional function that returns True when processing should stop
        """
        for event in self.stream():
            handler(event)
            if exit_condition and exit_condition():
                break


class CLOBEventStreamer:
    """
    Streamer for CLOB contract events.
    
    This class provides methods to subscribe to and process various events
    from a CLOB contract, including order creation, fills, amendments, and cancellations.
    """
    
    def __init__(self, clob: ICLOB, from_block: int = 0, poll_interval: float = 2.0):
        """
        Initialize the CLOB event streamer.
        
        Args:
            clob: ICLOB instance
            from_block: Starting block number to fetch events from
            poll_interval: Interval (in seconds) between poll requests for new events
        """
        self.clob = clob
        self.web3 = clob.web3
        self.from_block = from_block
        self.poll_interval = poll_interval
        self.contract = clob.contract
    
    def limit_order_processed_stream(self, **filter_params) -> EventStream[LimitOrderProcessedEvent]:
        """
        Get a stream of LimitOrderProcessed events.
        
        Args:
            **filter_params: Event filter parameters
            
        Returns:
            EventStream of LimitOrderProcessed events
        """
        return EventStream(
            self.web3,
            self.contract.events.LimitOrderProcessed,
            parse_limit_order_processed,
            from_block=self.from_block,
            poll_interval=self.poll_interval
        ).create_filter(**filter_params)
    
    def fill_order_processed_stream(self, **filter_params) -> EventStream[FillOrderProcessedEvent]:
        """
        Get a stream of FillOrderProcessed events.
        
        Args:
            **filter_params: Event filter parameters
            
        Returns:
            EventStream of FillOrderProcessed events
        """
        return EventStream(
            self.web3,
            self.contract.events.FillOrderProcessed,
            parse_fill_order_processed,
            from_block=self.from_block,
            poll_interval=self.poll_interval
        ).create_filter(**filter_params)
    
    def order_amended_stream(self, **filter_params) -> EventStream[OrderAmendedEvent]:
        """
        Get a stream of OrderAmended events.
        
        Args:
            **filter_params: Event filter parameters
            
        Returns:
            EventStream of OrderAmended events
        """
        return EventStream(
            self.web3,
            self.contract.events.OrderAmended,
            parse_order_amended,
            from_block=self.from_block,
            poll_interval=self.poll_interval
        ).create_filter(**filter_params)
    
    def order_canceled_stream(self, **filter_params) -> EventStream[OrderCanceledEvent]:
        """
        Get a stream of OrderCanceled events.
        
        Args:
            **filter_params: Event filter parameters
            
        Returns:
            EventStream of OrderCanceled events
        """
        return EventStream(
            self.web3,
            self.contract.events.OrderCanceled,
            parse_order_canceled,
            from_block=self.from_block,
            poll_interval=self.poll_interval
        ).create_filter(**filter_params)
    
    def order_matched_stream(self, **filter_params) -> EventStream[OrderMatchedEvent]:
        """
        Get a stream of OrderMatched events.
        
        Args:
            **filter_params: Event filter parameters
            
        Returns:
            EventStream of OrderMatched events
        """
        return EventStream(
            self.web3,
            self.contract.events.OrderMatched,
            parse_order_matched,
            from_block=self.from_block,
            poll_interval=self.poll_interval
        ).create_filter(**filter_params)
    
    def all_events_stream(self) -> Iterator[Dict]:
        """
        Stream all CLOB events.
        
        Returns:
            Iterator of all CLOB events
        """
        event_filter = self.web3.eth.filter({
            'address': self.clob.address,
            'fromBlock': self.from_block,
        })
        
        while True:
            for event in event_filter.get_new_entries():
                yield event
            time.sleep(self.poll_interval)
    
    # Example utility methods for common use cases
    
    def watch_limit_orders(self, account: Optional[str] = None):
        """
        Watch for limit orders, optionally filtered by account.
        
        Args:
            account: Optional account address to filter by
        """
        filter_params = {}
        if account:
            filter_params['account'] = account
        
        limit_stream = self.limit_order_processed_stream(**filter_params)
        
        for event in limit_stream.stream():
            print(f"Limit Order: {event}")
    
    def watch_fills(self, account: Optional[str] = None):
        """
        Watch for fill orders, optionally filtered by account.
        
        Args:
            account: Optional account address to filter by
        """
        filter_params = {}
        if account:
            filter_params['account'] = account
        
        fill_stream = self.fill_order_processed_stream(**filter_params)
        
        for event in fill_stream.stream():
            print(f"Fill Order: {event}")
    
    def watch_order_book_changes(self):
        """
        Watch for all order book changes (limit orders, fills, amendments, cancellations).
        """
        # Using the lower-level event filter for more control
        event_filter = self.web3.eth.filter({
            'address': self.clob.address,
            'fromBlock': self.from_block,
        })
        
        event_handlers = {
            'LimitOrderProcessed': parse_limit_order_processed,
            'FillOrderProcessed': parse_fill_order_processed,
            'OrderAmended': parse_order_amended,
            'OrderCanceled': parse_order_canceled,
            'OrderMatched': parse_order_matched,
        }
        
        while True:
            for log in event_filter.get_new_entries():
                try:
                    # Try to decode the event
                    decoded = self.contract.events.getLogs(log)
                    event_name = decoded['event']
                    
                    if event_name in event_handlers:
                        parsed_event = event_handlers[event_name](decoded)
                        print(f"Order Book Change: {event_name} - {parsed_event}")
                except Exception as e:
                    print(f"Error processing event: {e}")
            
            time.sleep(self.poll_interval)


# Usage examples:
# 
# from web3 import Web3
# from gte_py.contracts.iclob import ICLOB
# from gte_py.contracts.iclob_streaming import CLOBEventStreamer
# 
# web3 = Web3(Web3.HTTPProvider('https://your-provider-url'))
# clob_address = '0x...'
# clob = ICLOB(web3, clob_address)
# 
# # Create a streamer
# streamer = CLOBEventStreamer(clob, from_block=web3.eth.block_number)
# 
# # Watch for limit orders from a specific account
# streamer.watch_limit_orders(account='0x...')
# 
# # Get a stream of order cancellations and process them
# cancel_stream = streamer.order_canceled_stream()
# 
# def handle_cancellation(event):
#     print(f"Order {event.order_id} was canceled by {event.owner}")
# 
# cancel_stream.process_events(
#     handler=handle_cancellation,
#     exit_condition=lambda: time.time() > start_time + 3600  # Run for an hour
# )