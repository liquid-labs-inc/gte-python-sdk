"""High-level GTE client."""

import logging

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from .account import AccountClient
from .execution import ExecutionClient
from .iclob import CLOBClient
from .info import InfoClient
from .orderbook import OrderbookClient
from .token import TokenClient
from ..api.rest import RestApi
from ..configs import NetworkConfig

logger = logging.getLogger(__name__)


class Client:
    """User-friendly client for interacting with GTE."""

    def __init__(
            self,
            web3: AsyncWeb3,
            config: NetworkConfig,
            sender_address: ChecksumAddress | None = None,
    ):
        """
        Initialize the client.

        Args:
            web3: AsyncWeb3 instance
            config: Network configuration
            sender_address: Address to send transactions from (optional)
        """
        self._rest = RestApi(base_url=config.api_url)
        self._ws_url = config.ws_url
        self.config: NetworkConfig = config

        self._web3 = web3
        self.clob = CLOBClient(self._web3, config.router_address)
        # Initialize market service for fetching market information
        self.token = TokenClient(self._web3)
        self.info = InfoClient(web3=self._web3, rest=self._rest, clob_client=self.clob, token_client=self.token)
        self.market: OrderbookClient = OrderbookClient(config, self.info)
        self.account = AccountClient(
            sender_address=sender_address,
            clob=self.clob,
            token=self.token,
        )

        if not sender_address:
            self.execution = None
        else:
            # Initialize execution client for trading operations
            self.execution = ExecutionClient(
                web3=self._web3,
                sender_address=sender_address,
                clob=self.clob,
                token=self.token,

            )

        self._sender_address = sender_address

    async def __aenter__(self):
        """Enter async context."""
        await self._rest.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self._rest.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        """Close the client and release resources."""
        await self.__aexit__(None, None, None)
