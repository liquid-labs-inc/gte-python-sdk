import asyncio
from typing import Callable, Any

from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address
from hexbytes import HexBytes

from gte_py.api.rest import RestApi, logger
from gte_py.api.rest.models import trade_to_model
from gte_py.api.ws import WebSocketApi, TradeData
from gte_py.configs import NetworkConfig
from gte_py.models import Market, Trade, OrderSide


class TradesClient:
    """
    This class is used to interact with the trades endpoint of the GTE API.
    """

    def __init__(self, config: NetworkConfig, rest: RestApi, ws: WebSocketApi):
        self._ws = ws
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
        return [trade_to_model(trade) for trade in trades]

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
        async def handle_trade_message(raw_data: TradeData):
            trade = Trade(
                market_address=to_checksum_address(raw_data['m']),
                side=OrderSide.from_str(raw_data['sd']),
                price=float(raw_data['px']),
                size=float(raw_data['sz']),
                timestamp= raw_data['t'],
                tx_hash=HexBytes(raw_data['h']),
                trade_id=raw_data['id']
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
