"""High-level GTE client."""

import logging

from eth_typing import ChecksumAddress
from eth_account.types import PrivateKeyType
from web3 import AsyncWeb3

from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.chain.utils import make_web3
from gte_py.api.rest import RestApi
from gte_py.api.ws import WebSocketApi
from gte_py.configs import NetworkConfig

from .execution import ExecutionClient
from .info import InfoClient
from .market import MarketClient
from .user import UserClient

logger = logging.getLogger(__name__)


class Client:
    """User-friendly client for interacting with GTE.

    Provides an interface to communicate with the GTE protocol through REST and Web3.
    Aggregates low-level clients including CLOB, token, user, market, info, and execution layers.
    """

    @classmethod
    async def connect(
        cls,
        config: NetworkConfig,
        wallet_address: ChecksumAddress | None = None,
        wallet_private_key: PrivateKeyType | None = None,
    ) -> "Client":
        """Initializes a Web3 instance and returns a connected GTE client.

        Args:
            config (NetworkConfig): Network configuration settings.
            wallet_address (ChecksumAddress | None): Optional Ethereum address of the user.
            wallet_private_key (PrivateKeyType | None): Optional private key for signing transactions.

        Returns:
            Client: A fully initialized client instance.
        """
        web3 = await make_web3(
            config,
            wallet_address=wallet_address,
            wallet_private_key=wallet_private_key,
        )
        return cls(web3=web3, config=config, wallet_address=wallet_address)

    def __init__(
        self,
        *,
        web3: AsyncWeb3,
        config: NetworkConfig,
        wallet_address: ChecksumAddress | None = None,
    ):
        """Initializes the GTE client and subcomponents.

        Args:
            web3 (AsyncWeb3): Web3 instance for blockchain interaction.
            config (NetworkConfig): Configuration for connecting to the network.
            wallet_address (ChecksumAddress | None): Optional user wallet address.
        """
        self.config = config
        self._wallet_address = wallet_address
        self._web3 = web3

        # Initialize API clients
        self.rest = RestApi(base_url=config.api_url)
        self.websocket = WebSocketApi(ws_url=config.ws_url)
        self.clob = CLOBClient(self._web3, self.config.router_address)
        self.token = TokenClient(self._web3)
        self.info = InfoClient(self.rest, self.websocket)
        self.market = MarketClient(self.config, self.rest, self.info, self.clob)

        # Initialize user-specific clients (only if wallet address is provided)
        self.user = None
        self.execution = None

        if self._wallet_address:
            self.user = UserClient(self.config, self._wallet_address, self.clob, self.token, self.rest)
            self.execution = ExecutionClient(
                web3=self._web3,
                main_account=self._wallet_address,
                clob=self.clob,
                token=self.token,
                rest=self.rest,
                market=self.market,
                user=self.user,
            )

    async def init(self):
        """Initializes internal clients that require asynchronous setup."""
        await self.clob.init()

    async def __aenter__(self) -> "Client":
        await self.rest.connect()
        await self.websocket.connect()
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rest.disconnect()
        # get open subscriptions
        for subscription in self.info.get_subscriptions():
            await self.websocket.unsubscribe(*subscription)
        self.info.clear_subscriptions()
        await self.websocket.disconnect()

    async def close(self):
        """Close the client and release resources."""
        await self.__aexit__(None, None, None)
