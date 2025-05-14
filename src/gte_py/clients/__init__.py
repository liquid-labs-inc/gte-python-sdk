"""High-level GTE client."""

import logging

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from .account import AccountClient
from .execution import ExecutionClient
from .clob import CLOBClient
from .info import InfoClient
from .orderbook import OrderbookClient
from .token import TokenClient
from .trades import TradesClient
from ..api.rest import RestApi
from ..configs import NetworkConfig

logger = logging.getLogger(__name__)


class Client:
    """User-friendly client for interacting with GTE."""

    def __init__(
        self,
        web3: AsyncWeb3,
        config: NetworkConfig,
        account: ChecksumAddress | None = None,
    ):
        """
        Initialize the client.

        Args:
            web3: AsyncWeb3 instance
            config: Network configuration
            account: Address of main account
        """
        account = account or web3.eth.default_account

        self.rest = RestApi(base_url=config.api_url)
        self._ws_url = config.ws_url
        self.config: NetworkConfig = config

        self._web3 = web3
        self.clob = CLOBClient(self._web3, config.router_address)
        # Initialize market service for fetching market information
        self.token = TokenClient(self._web3)
        self.info = InfoClient(
            web3=self._web3, rest=self.rest, clob_client=self.clob, token_client=self.token
        )
        self.orderbook: OrderbookClient = OrderbookClient(config, self.rest, self.info, self.clob)
        if not account:
            self.account = None
        else:
            self.account = AccountClient(
                config=config,
                account=account, clob=self.clob, token=self.token, rest=self.rest
            )
        self.trades = TradesClient(config, self.rest)

        if not account:
            self.execution = None
        else:
            # Initialize execution client for trading operations
            self.execution = ExecutionClient(
                web3=self._web3,
                main_account=account,
                clob=self.clob,
                token=self.token,
                rest=self.rest,
                orderbook=self.orderbook,
            )

        self._sender_address = account

    async def init(self):
        await self.clob.init()

    async def __aenter__(self):
        """Enter async context."""
        await self.rest.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.rest.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        """Close the client and release resources."""
        await self.__aexit__(None, None, None)
