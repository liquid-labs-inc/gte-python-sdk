import asyncio
from typing import Callable, Any

from eth_typing import ChecksumAddress

from gte_py.api.rest import RestApi, logger
from gte_py.api.ws import WebSocketApi
from gte_py.configs import NetworkConfig
from gte_py.models import Market, Trade


class TradesClient:
    """
    This class is used to interact with the trades endpoint of the GTE API.
    """

    def __init__(self, config: NetworkConfig, rest: RestApi):
        self._ws = WebSocketApi(config.ws_url)
        self._trade_callbacks = []
        self._rest = rest
        self._last_trade = None  # Store the last received trade

    async def connect(self):
        """Connect to the WebSocket."""
        await self._ws.connect()

    async def get_trades(self, market: ChecksumAddress, limit: int = 100, offset: int = 0) -> list[Trade]:
        """
        Get trades for a specific symbol.

        :param market: The symbol to get trades for.

        :return: The response from the API.
        """
        trades = await self._rest.get_trades(market, limit, offset)
        return [Trade.from_api(trade) for trade in trades]

    # Trade methods
    async def subscribe_trades(
        self, market: Market, callback: Callable[[Trade], Any] | None = None
    ):
        """Subscribe to real-time trades.

        Args:
            callback: Function to call when a trade is received
        """
        if callback:
            self._trade_callbacks.append(callback)

        if not self._trade_callbacks:
            # If no callbacks, add a dummy one to store the last trade
            self._trade_callbacks.append(lambda trade: setattr(self, "_last_trade", trade))

        # Define handler for raw trade messages that handles both raw and parsed data
        async def handle_trade_message(raw_data, parsed_data):
            if raw_data.get("s") != "trades":
                return

            # Extract trade data from raw data as fallback
            trade_data = raw_data.get("d", {})
            
            # Use parsed_data if available, otherwise fallback to parsing raw_data
            if parsed_data:
                # Make sure timestamp is processed correctly
                timestamp = None
                if parsed_data.get("timestamp"):
                    try:
                        timestamp = int(parsed_data.get("timestamp").timestamp() * 1000)
                    except (AttributeError, TypeError):
                        timestamp = trade_data.get("t")
                
                trade = Trade(
                    market_address=parsed_data.get("market"),
                    side=parsed_data.get("side"),
                    price=parsed_data.get("price"),
                    size=parsed_data.get("size"),
                    timestamp=timestamp or trade_data.get("t", 0),  # Fallback to raw data timestamp or 0
                    tx_hash=parsed_data.get("tx_hash"),
                )
            else:
                trade = Trade(
                    market_address=trade_data.get("m"),
                    side=trade_data.get("sd"),
                    price=float(trade_data.get("px", 0)),
                    size=float(trade_data.get("sz", 0)),
                    timestamp=trade_data.get("t", 0),  # Default to 0 if not available
                    tx_hash=trade_data.get("h"),
                )

            self._last_trade = trade

            for cb in self._trade_callbacks:
                try:
                    await cb(trade) if asyncio.iscoroutinefunction(cb) else cb(trade)
                except Exception as e:
                    logger.error(f"Error in trade callback: {e}")

        await self._ws.subscribe_trades(market.address, handle_trade_message)

    async def unsubscribe_trades(self, market: Market):
        """Unsubscribe from real-time trades."""
        await self._ws.unsubscribe_trades(market.address)
        self._trade_callbacks = []
