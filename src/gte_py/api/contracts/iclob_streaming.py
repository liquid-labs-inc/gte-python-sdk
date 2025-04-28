"""
Event streaming module for CLOB contract events.

This module provides functionality to subscribe to and process events
from the CLOB (Central Limit Order Book) contract in real-time.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TypeVar, Generic, Iterator, Union, Tuple, Any
import time
import asyncio
from threading import Thread

from urllib3.util import current_time
from web3 import AsyncWeb3
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
    parse_order_matched
)
from gte_py.models import OrderBookSnapshot

T = TypeVar('T')


class EventStream(Generic[T]):
    """Generic class for handling event streams with filtering and processing."""

    def __init__(
            self,
            web3: AsyncWeb3,
            event: object,
            parser: Callable[[Dict], T],
            from_block: int = 0,
            to_block: Union[int, str] = 'latest',
            poll_interval: float = 2.0,
    ):
        """
        Initialize an event stream for a specific event.
        
        Args:
            web3: AsyncWeb3 instance
            event: AsyncWeb3 contract event object
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
    Streamer for CLOB contract events and market data.
    
    This class provides methods to subscribe to and process various events
    from a CLOB contract, including order creation, fills, amendments, cancellations,
    and market data like order book updates and trades.
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

        # For market data tracking
        self._last_tob = None
        self._last_book_snapshot = None
        self._callbacks = {
            'orderbook': [],
            'tob': [],
            'trades': [],
            'stats': []
        }

    # ================= EVENT STREAMS =================

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

    # ================= MARKET DATA METHODS =================

    def get_order_book_snapshot(self, depth: int = 5, side: Optional[int] = None) -> OrderBookSnapshot:
        """
        Get a snapshot of the current order book.
        
        Args:
            depth: Number of price levels to include on each side
            side: Optional side to filter (0 for bids, 1 for asks, None for both)
            
        Returns:
            Dictionary containing bids and asks with prices and sizes
        """
        bids = []
        asks = []

        tob = self.clob.get_tob()
        max_bid, min_ask = tob

        if side is None or side == 0:  # Include bids
            # Start from the top bid
            current_price = max_bid
            for _ in range(depth):
                if current_price == 0:
                    break

                (num_orders, head_order_id, tail_order_id) = self.clob.get_limit(current_price, 0)  # 0 is BUY side

                # Extract total size at this price level by traversing the linked list of orders
                total_size = 0
                if num_orders > 0:
                    order_id = head_order_id
                    while order_id != 0:
                        order = self.clob.get_order(order_id)
                        total_size += order.amount
                        order_id = order.nextOrderId

                if total_size > 0:
                    bids.append((current_price, total_size, num_orders))

                # Get the next price level
                current_price = self.clob.get_next_smallest_price(current_price, 0)

        if side is None or side == 1:  # Include asks
            # Start from the top ask
            current_price = min_ask
            for _ in range(depth):
                if current_price == 0:
                    break

                (num_orders, head_order_id, tail_order_id) = self.clob.get_limit(current_price, 1)  # 0 is BUY side

                # Extract total size at this price level by traversing the linked list of orders
                total_size = 0
                if num_orders > 0:
                    order_id = head_order_id
                    while order_id != 0:
                        order = self.clob.get_order(order_id)
                        total_size += order.amount
                        order_id = order.nextOrderId

                if total_size > 0:
                    asks.append((current_price, total_size, num_orders))

                # Get the next price level
                current_price = self.clob.get_next_biggest_price(current_price, 1)

        return OrderBookSnapshot(
            bids=bids,
            asks=asks,
            timestamp=current_time(),
            market_address=self.clob.address,
        )

    def get_market_stats(self) -> Dict[str, Any]:
        """
        Get current market statistics.
        
        Returns:
            Dictionary containing market statistics
        """
        tob = self.clob.get_tob()
        max_bid, min_ask = tob

        open_interest = self.clob.get_open_interest()

        return {
            'max_bid': max_bid,
            'min_ask': min_ask,
            'spread': min_ask - max_bid if min_ask > 0 and max_bid > 0 else 0,
            'mid_price': (min_ask + max_bid) // 2 if min_ask > 0 and max_bid > 0 else 0,
            'num_bids': self.clob.get_num_bids(),
            'num_asks': self.clob.get_num_asks(),
            'quote_open_interest': open_interest[0],
            'base_open_interest': open_interest[1]
        }

    def stream_order_book(self, depth: int = 5, callback: Optional[Callable] = None) -> Iterator[
        Dict[str, List[Tuple[int, int]]]]:
        """
        Stream order book updates.
        
        Args:
            depth: Number of price levels to include on each side
            callback: Optional callback function when book is updated
            
        Yields:
            Dictionary containing bids and asks with prices and sizes whenever there's a change
        """
        # Register the callback if provided
        if callback:
            self._callbacks['orderbook'].append(callback)

        # Create filters for events that would change the order book
        limit_filter = self.contract.events.LimitOrderProcessed.createFilter(fromBlock='latest')
        fill_filter = self.contract.events.FillOrderProcessed.createFilter(fromBlock='latest')
        amend_filter = self.contract.events.OrderAmended.createFilter(fromBlock='latest')
        cancel_filter = self.contract.events.OrderCanceled.createFilter(fromBlock='latest')
        match_filter = self.contract.events.OrderMatched.createFilter(fromBlock='latest')

        # Initial snapshot
        last_book = self.get_order_book_snapshot(depth)
        yield last_book

        # Check for changes in real-time
        try:
            while True:
                # Check if any events have modified the order book
                has_changes = False

                for filter in [limit_filter, fill_filter, amend_filter, cancel_filter, match_filter]:
                    if filter.get_new_entries():
                        has_changes = True
                        break

                if has_changes:
                    current_book = self.get_order_book_snapshot(depth)
                    if current_book != last_book:
                        last_book = current_book

                        # Notify callbacks
                        for cb in self._callbacks['orderbook']:
                            cb(current_book)

                        yield current_book

                time.sleep(self.poll_interval)

        except Exception as e:
            print(f"Error in stream_order_book: {e}")
        finally:
            # Cleanup filters
            for filter in [limit_filter, fill_filter, amend_filter, cancel_filter, match_filter]:
                filter.uninstall()

    def stream_trades(self, callback: Optional[Callable] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream trade data from OrderMatched events.
        
        Args:
            callback: Optional callback function when a trade occurs
            
        Yields:
            Dictionary containing trade details whenever a new trade occurs
        """
        # Register the callback if provided
        if callback:
            self._callbacks['trades'].append(callback)

        # Create filter for trade events
        order_matched_filter = self.contract.events.OrderMatched.createFilter(
            fromBlock='latest'
        )

        try:
            while True:
                for event in order_matched_filter.get_new_entries():
                    parsed_event = parse_order_matched(event)
                    trade_data = {
                        'taker_order_id': parsed_event.taker_order_id,
                        'maker_order_id': parsed_event.maker_order_id,
                        'taker_side': parsed_event.taker_order['side'],
                        'price': parsed_event.maker_order['price'],
                        'amount': parsed_event.traded_base,
                        'taker': parsed_event.taker_order['owner'],
                        'maker': parsed_event.maker_order['owner'],
                        'timestamp': event['blockTimestamp'] if 'blockTimestamp' in event else None
                    }

                    # Notify callbacks
                    for cb in self._callbacks['trades']:
                        cb(trade_data)

                    yield trade_data

                time.sleep(self.poll_interval)

        except Exception as e:
            print(f"Error in stream_trades: {e}")
        finally:
            # Cleanup filter
            order_matched_filter.uninstall()

    def stream_tob(self, callback: Optional[Callable] = None) -> Iterator[Tuple[int, int]]:
        """
        Stream top-of-book (TOB) updates.
        
        Args:
            callback: Optional callback function when TOB changes
            
        Yields:
            Tuple of (highest_bid_price, lowest_ask_price) whenever there's a change
        """
        # Register the callback if provided
        if callback:
            self._callbacks['tob'].append(callback)

        # Create filters for events that would change the TOB
        limit_filter = self.contract.events.LimitOrderProcessed.createFilter(fromBlock='latest')
        fill_filter = self.contract.events.FillOrderProcessed.createFilter(fromBlock='latest')
        amend_filter = self.contract.events.OrderAmended.createFilter(fromBlock='latest')
        cancel_filter = self.contract.events.OrderCanceled.createFilter(fromBlock='latest')
        match_filter = self.contract.events.OrderMatched.createFilter(fromBlock='latest')

        # Initial TOB
        last_tob = self.clob.get_tob()
        yield last_tob

        try:
            while True:
                # Check if any events have modified the order book
                has_changes = False

                for filter in [limit_filter, fill_filter, amend_filter, cancel_filter, match_filter]:
                    if filter.get_new_entries():
                        has_changes = True
                        break

                if has_changes:
                    current_tob = self.clob.get_tob()
                    if current_tob != last_tob:
                        last_tob = current_tob

                        # Notify callbacks
                        for cb in self._callbacks['tob']:
                            cb(current_tob)

                        yield current_tob

                time.sleep(self.poll_interval)

        except Exception as e:
            print(f"Error in stream_tob: {e}")
        finally:
            # Cleanup filters
            for filter in [limit_filter, fill_filter, amend_filter, cancel_filter, match_filter]:
                filter.uninstall()

    def stream_market_stats(self, callback: Optional[Callable] = None) -> Iterator[Dict[str, Any]]:
        """
        Stream market statistics.
        
        Args:
            callback: Optional callback function when market stats change
            
        Yields:
            Dictionary containing market statistics whenever there's a change
        """
        # Register the callback if provided
        if callback:
            self._callbacks['stats'].append(callback)

        # Create filters for events that would change market statistics
        limit_filter = self.contract.events.LimitOrderProcessed.createFilter(fromBlock='latest')
        fill_filter = self.contract.events.FillOrderProcessed.createFilter(fromBlock='latest')
        amend_filter = self.contract.events.OrderAmended.createFilter(fromBlock='latest')
        cancel_filter = self.contract.events.OrderCanceled.createFilter(fromBlock='latest')
        match_filter = self.contract.events.OrderMatched.createFilter(fromBlock='latest')

        # Initial stats
        last_stats = self.get_market_stats()
        yield last_stats

        try:
            while True:
                # Check if any events have modified the market
                has_changes = False

                for filter in [limit_filter, fill_filter, amend_filter, cancel_filter, match_filter]:
                    if filter.get_new_entries():
                        has_changes = True
                        break

                if has_changes:
                    current_stats = self.get_market_stats()
                    if current_stats != last_stats:
                        last_stats = current_stats

                        # Notify callbacks
                        for cb in self._callbacks['stats']:
                            cb(current_stats)

                        yield current_stats

                time.sleep(self.poll_interval)

        except Exception as e:
            print(f"Error in stream_market_stats: {e}")
        finally:
            # Cleanup filters
            for filter in [limit_filter, fill_filter, amend_filter, cancel_filter, match_filter]:
                filter.uninstall()

    # ================= CONVENIENCE METHODS =================

    def on_orderbook(self, callback: Callable[[Dict[str, List[Tuple[int, int]]]], None]):
        """
        Register a callback for orderbook updates.
        
        Args:
            callback: Function to call with orderbook data
        """
        self._callbacks['orderbook'].append(callback)

    def on_trades(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register a callback for trade updates.
        
        Args:
            callback: Function to call with trade data
        """
        self._callbacks['trades'].append(callback)

    def on_tob(self, callback: Callable[[Tuple[int, int]], None]):
        """
        Register a callback for top-of-book updates.
        
        Args:
            callback: Function to call with (highest_bid, lowest_ask) tuple
        """
        self._callbacks['tob'].append(callback)

    def on_stats(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register a callback for market statistics updates.
        
        Args:
            callback: Function to call with market statistics data
        """
        self._callbacks['stats'].append(callback)

    # ================= EXAMPLE UTILITIES =================

    def watch_orderbook(self, depth: int = 5, duration: int = None):
        """
        Watch and print the orderbook for a specified duration.
        
        Args:
            depth: Number of levels to display
            duration: How long to watch in seconds (None for indefinite)
        """
        start_time = time.time()

        def print_book(book):
            print("\nOrderbook update:")
            print("BIDS:")
            for price, size in sorted(book['bids'], key=lambda x: x[0], reverse=True):
                print(f"  {price:10} | {size}")
            print("ASKS:")
            for price, size in sorted(book['asks'], key=lambda x: x[0]):
                print(f"  {price:10} | {size}")
            print("-" * 30)

        # Start streaming with the print callback
        book_stream = self.stream_order_book(depth=depth, callback=print_book)

        try:
            for _ in book_stream:
                if duration and time.time() - start_time > duration:
                    break
        except KeyboardInterrupt:
            print("Order book watch stopped.")

    def watch_trades(self, duration: int = None):
        """
        Watch and print trades for a specified duration.
        
        Args:
            duration: How long to watch in seconds (None for indefinite)
        """
        start_time = time.time()

        def print_trade(trade):
            side = "BUY" if trade['taker_side'] == 0 else "SELL"
            print(f"\nTrade: {side} {trade['amount']} @ {trade['price']}")
            print(f"Taker: {trade['taker']}")
            print(f"Maker: {trade['maker']}")
            print("-" * 30)

        # Start streaming with the print callback
        trade_stream = self.stream_trades(callback=print_trade)

        try:
            for _ in trade_stream:
                if duration and time.time() - start_time > duration:
                    break
        except KeyboardInterrupt:
            print("Trade watch stopped.")
