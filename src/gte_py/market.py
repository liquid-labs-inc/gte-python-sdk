"""Real-time market data client."""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Union
import json
from datetime import datetime

from .raw import GTEWebSocketClient
from .models import Market, Trade, Candle, OrderbookUpdate

logger = logging.getLogger(__name__)


class GteMarketClient:
    """WebSocket-based client for real-time market data."""

    def __init__(self, market: Market, ws_url: str = "wss://ws.gte.io/v1"):
        """Initialize the client.

        Args:
            market: Market object
            ws_url: WebSocket URL
        """
        self.market = market
        self._ws_client = GTEWebSocketClient(ws_url=ws_url)
        self._trade_callbacks = []
        self._candle_callbacks = {}  # Keyed by interval
        self._orderbook_callbacks = []
        self._last_trade = None
        self._last_candle = {}  # Keyed by interval
        self._orderbook_state = None  # Current orderbook state

    async def connect(self):
        """Connect to the WebSocket."""
        await self._ws_client.connect()
        logger.info(f"Connected to WebSocket for market {self.market.address}")

    async def close(self):
        """Close the WebSocket connection."""
        await self._ws_client.close()
        logger.info(f"Disconnected from WebSocket for market {self.market.address}")

    # Trade methods
    async def subscribe_trades(self, callback: Optional[Callable[[Trade], Any]] = None):
        """Subscribe to real-time trades.

        Args:
            callback: Function to call when a trade is received
        """
        if callback:
            self._trade_callbacks.append(callback)

        if not self._trade_callbacks:
            # If no callbacks, add a dummy one to store the last trade
            self._trade_callbacks.append(lambda trade: setattr(self, '_last_trade', trade))

        # Define handler for raw trade messages
        async def handle_trade_message(data):
            if data.get('s') != 'trades':
                return
            
            trade_data = data.get('d', {})
            trade = Trade(
                market_address=trade_data.get('m'),
                side=trade_data.get('sd'),
                price=float(trade_data.get('px')),
                size=float(trade_data.get('sz')),
                timestamp=trade_data.get('t'),
                tx_hash=trade_data.get('h'),
                trade_id=trade_data.get('id')
            )
            
            self._last_trade = trade
            
            for cb in self._trade_callbacks:
                try:
                    await cb(trade) if asyncio.iscoroutinefunction(cb) else cb(trade)
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")

        await self._ws_client.subscribe_trades([self.market.address], handle_trade_message)

    async def unsubscribe_trades(self):
        """Unsubscribe from real-time trades."""
        await self._ws_client.unsubscribe_trades([self.market.address])
        self._trade_callbacks = []

    @property
    def last_trade(self) -> Optional[Trade]:
        """Get the most recent trade."""
        return self._last_trade

    # Candle methods
    async def subscribe_candles(self, interval: str = "1m", 
                               callback: Optional[Callable[[Candle], Any]] = None):
        """Subscribe to real-time candles.

        Args:
            interval: Candle interval (e.g., "1m")
            callback: Function to call when a candle is received
        """
        if interval not in self._candle_callbacks:
            self._candle_callbacks[interval] = []
        
        if callback:
            self._candle_callbacks[interval].append(callback)
        
        if not self._candle_callbacks[interval]:
            # If no callbacks, add a dummy one to store the last candle
            self._candle_callbacks[interval].append(
                lambda candle: self._last_candle.update({interval: candle})
            )

        # Define handler for raw candle messages
        async def handle_candle_message(data):
            if data.get('s') != 'candle':
                return
            
            candle_data = data.get('d', {})
            if candle_data.get('i') != interval:
                return  # Ignore candles for other intervals
                
            candle = Candle(
                market_address=candle_data.get('m'),
                interval=candle_data.get('i'),
                timestamp=candle_data.get('t'),
                open=float(candle_data.get('o')),
                high=float(candle_data.get('h')),
                low=float(candle_data.get('l')),
                close=float(candle_data.get('c')),
                volume=float(candle_data.get('v')),
                num_trades=candle_data.get('n')
            )
            
            self._last_candle[interval] = candle
            
            for cb in self._candle_callbacks[interval]:
                try:
                    await cb(candle) if asyncio.iscoroutinefunction(cb) else cb(candle)
                except Exception as e:
                    logger.error(f"Error in candle callback: {e}")

        await self._ws_client.subscribe_candles(
            market=self.market.address, 
            interval=interval,
            callback=handle_candle_message
        )

    async def unsubscribe_candles(self, interval: str = "1m"):
        """Unsubscribe from real-time candles.

        Args:
            interval: Candle interval to unsubscribe from
        """
        await self._ws_client.unsubscribe_candles(
            market=self.market.address, 
            interval=interval
        )
        if interval in self._candle_callbacks:
            del self._candle_callbacks[interval]
        if interval in self._last_candle:
            del self._last_candle[interval]

    def get_last_candle(self, interval: str = "1m") -> Optional[Candle]:
        """Get the most recent candle for the specified interval."""
        return self._last_candle.get(interval)

    # Orderbook methods
    async def subscribe_orderbook(self, callback: Optional[Callable[[OrderbookUpdate], Any]] = None):
        """Subscribe to real-time orderbook updates.

        Args:
            callback: Function to call when an orderbook update is received
        """
        if callback:
            self._orderbook_callbacks.append(callback)
        
        if not self._orderbook_callbacks:
            # If no callbacks, add a dummy one to update the orderbook state
            self._orderbook_callbacks.append(
                lambda update: setattr(self, '_orderbook_state', update)
            )

        # Define handler for raw orderbook messages
        async def handle_orderbook_message(data):
            if data.get('s') != 'orderbook':
                return
            
            ob_data = data.get('d', {})
            update = OrderbookUpdate(
                market_address=ob_data.get('m'),
                timestamp=ob_data.get('t'),
                bids=[{'price': float(bid.get('px')), 
                      'size': float(bid.get('sz')), 
                      'count': bid.get('n')} 
                     for bid in ob_data.get('b', [])],
                asks=[{'price': float(ask.get('px')), 
                      'size': float(ask.get('sz')), 
                      'count': ask.get('n')} 
                     for ask in ob_data.get('a', [])]
            )
            
            self._orderbook_state = update
            
            for cb in self._orderbook_callbacks:
                try:
                    await cb(update) if asyncio.iscoroutinefunction(cb) else cb(update)
                except Exception as e:
                    logger.error(f"Error in orderbook callback: {e}")

        # Use the trading pair format required by API
        pair = f"{self.market.base_asset.symbol}-{self.market.quote_asset.symbol}"
        await self._ws_client.subscribe_orderbook(pair=pair, callback=handle_orderbook_message)

    async def unsubscribe_orderbook(self):
        """Unsubscribe from real-time orderbook updates."""
        pair = f"{self.market.base_asset.symbol}-{self.market.quote_asset.symbol}"
        await self._ws_client.unsubscribe_orderbook(pair=pair)
        self._orderbook_callbacks = []
        self._orderbook_state = None

    @property
    def orderbook(self) -> Optional[OrderbookUpdate]:
        """Get the current orderbook state."""
        return self._orderbook_state

    # Convenience method to subscribe to all data types
    async def subscribe_all(self, 
                           trade_callback: Optional[Callable[[Trade], Any]] = None,
                           candle_callback: Optional[Callable[[Candle], Any]] = None,
                           orderbook_callback: Optional[Callable[[OrderbookUpdate], Any]] = None,
                           candle_interval: str = "1m"):
        """Subscribe to all data types for this market.

        Args:
            trade_callback: Function to call when a trade is received
            candle_callback: Function to call when a candle is received
            orderbook_callback: Function to call when an orderbook update is received
            candle_interval: Candle interval to subscribe to
        """
        await self.subscribe_trades(trade_callback)
        await self.subscribe_candles(candle_interval, candle_callback)
        await self.subscribe_orderbook(orderbook_callback)
