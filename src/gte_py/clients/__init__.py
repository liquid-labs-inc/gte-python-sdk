"""High-level GTE client."""

import logging

from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.rest import RestApi
from gte_py.configs import NetworkConfig
from .user import UserClient
from .execution import ExecutionClient
from .info import InfoClient
from .market import MarketClient

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
        self.market: MarketClient = MarketClient(config, self.rest, self.info, self.clob)
        if not account:
            self.user: UserClient = None
        else:
            self.user = UserClient(
                config=config,
                account=account, clob=self.clob, token=self.token, rest=self.rest
            )

        if not account:
            self.execution: ExecutionClient = None
        else:
            # Initialize execution client for trading operations
            self.execution = ExecutionClient(
                web3=self._web3,
                main_account=account,
                clob=self.clob,
                token=self.token,
                rest=self.rest,
                market=self.market,
                user=self.user
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
