"""
Generic event source for both historical queries and real-time streaming.

This module provides a unified interface for accessing blockchain events,
supporting both historical queries and real-time streaming.
"""

import asyncio
import logging
from typing import Callable, Dict, Generic, AsyncIterator, List, Optional, TypeVar, Any, Union

from web3 import AsyncWeb3
from web3._utils.filters import AsyncLogFilter
from web3.contract.async_contract import AsyncContractEvent
from web3.types import EventData

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EventSource(Generic[T]):
    """
    Generic event source for blockchain events.

    Provides methods to fetch historical events and stream new events
    with consistent parsing into typed event objects.
    """

    def __init__(
        self,
        web3: AsyncWeb3,
        event: AsyncContractEvent,
        parser: Callable[[EventData], T],
    ):
        """
        Initialize an event source.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            event: ContractEvent to query or stream events from
            parser: Function to parse raw event data into typed objects
        """
        self.web3 = web3
        self.event = event
        self.parser = parser

    async def get_historical(
        self,
        from_block: int,
        to_block: Union[int, str] = "latest",
        **filter_params
    ) -> List[T]:
        """
        Query historical events within a block range.

        Args:
            from_block: Starting block number (inclusive)
            to_block: Ending block number (inclusive) or 'latest'
            **filter_params: Additional filter parameters for the event

        Returns:
            List of parsed event objects
        """
        argument_filters = filter_params if filter_params else None

        raw_logs = await self.event.get_logs(
            from_block=from_block,
            to_block=to_block,
            argument_filters=argument_filters,
        )

        return [self.parser(log) for log in raw_logs]

    def get_streaming(
        self,
        from_block: Union[int, str] = "latest",
        poll_interval: float = 2.0,
        **filter_params
    ) -> 'EventStream[T]':
        """
        Get a stream of events as they occur.

        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval in seconds between polling for new events
            **filter_params: Additional filter parameters for the event

        Returns:
            EventStream instance for the requested events
        """
        return EventStream(
            web3=self.web3,
            event=self.event,
            parser=self.parser,
            from_block=from_block,
            poll_interval=poll_interval,
            filter_params=filter_params
        )


class EventStream(Generic[T]):
    """Async stream of blockchain events with filtering and parsing capabilities."""

    def __init__(
        self,
        web3: AsyncWeb3,
        event: AsyncContractEvent,
        parser: Callable[[EventData], T],
        from_block: Union[int, str] = "latest",
        poll_interval: float = 2.0,
        filter_params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize an event stream.

        Args:
            web3: AsyncWeb3 instance
            event: ContractEvent to stream events from
            parser: Function to parse raw event data into typed objects
            from_block: Starting block number or 'latest'
            poll_interval: Interval in seconds between polling for new events
            filter_params: Optional filter parameters for the event
            max_retries: Maximum number of retries for filter recreation
            retry_delay: Delay between retries in seconds
        """
        self.web3 = web3
        self.event = event
        self.parser = parser
        self.from_block = from_block
        self.poll_interval = poll_interval
        self.filter_params = filter_params or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.filter: AsyncLogFilter | None = None
        self._running = False

    async def __aenter__(self):
        """Setup the event filter when entering an async context."""
        await self.create_filter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup the event filter when exiting an async context."""
        self._running = False
        # Note: We don't explicitly delete the filter as it's ephemeral anyway

    async def create_filter(self) -> AsyncLogFilter:
        """Create an event filter based on the provided parameters."""
        try:
            self.filter = await self.event.create_filter(
                from_block=self.from_block,
                **self.filter_params
            )
            if self.filter:
                logger.debug(f"Created event filter: {self.filter.filter_id}")
                return self.filter
            else:
                raise RuntimeError("Failed to create filter - got None")
        except Exception as e:
            logger.error(f"Failed to create event filter: {e}")
            raise

    async def _get_entries_simple(self, get_entries_func: Callable[[], Any]) -> List[T]:
        """
        Get entries with minimal logic: create filter if needed, process logs, and parse events.
        """
        if not self.filter:
            await self.create_filter()
            assert self.filter is not None

        logs = await get_entries_func()
        event_datas = []
        for log in logs:
            try:
                # Only process if it's a raw log (LogReceipt)
                if "topics" in log:
                    event_data = self.event.process_log(log)
                else:
                    event_data = log  # Already EventData
                event_datas.append(event_data)
            except Exception as e:
                logger.warning(f"Failed to process log {log}: {e}")
                continue
        results = []
        for event_data in event_datas:
            try:
                result = self.parser(event_data)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse event data {event_data}: {e}")
                continue
        return results

    async def get_all_entries(self) -> List[T]:
        """
        Get all events matching the filter.

        Returns:
            List of parsed event objects
        """
        return await self._get_entries_simple(
            lambda: self.filter.get_all_entries() if self.filter else None
        )

    async def get_new_entries(self) -> List[T]:
        """
        Get new events since the last check.

        Returns:
            List of new parsed event objects
        """
        return await self._get_entries_simple(
            lambda: self.filter.get_new_entries() if self.filter else None
        )

    async def stream(self) -> AsyncIterator[T]:
        """
        Stream events as they occur with automatic error recovery.

        Yields:
            Parsed event objects as they occur
        """
        self._running = True
        
        while self._running:
            try:
                entries = await self.get_new_entries()
                for entry in entries:
                    if not self._running:
                        break
                    yield entry
                    
                # Only sleep if we're still running
                if self._running:
                    await asyncio.sleep(self.poll_interval)
                    
            except Exception as e:
                logger.error(f"Error in event stream: {e}")
                if not self._running:
                    break
                    
                # Wait before retrying
                await asyncio.sleep(self.retry_delay)

    def stop(self):
        """Stop the event stream."""
        self._running = False

    async def process_events(
        self,
        handler: Callable[[T], Any],
        exit_condition: Optional[Callable[[], bool]] = None
    ):
        """
        Process events using a handler function until an optional exit condition is met.

        Args:
            handler: Function to call for each event
            exit_condition: Optional function that returns True when processing should stop
        """
        async for event in self.stream():
            try:
                await handler(event)
                if exit_condition and exit_condition():
                    break
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                # Continue processing other events
