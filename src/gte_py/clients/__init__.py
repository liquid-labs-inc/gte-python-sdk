"""High-level GTE client."""

import logging

from eth_typing import ChecksumAddress
from eth_account.types import PrivateKeyType
from web3 import AsyncWeb3

from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.token_client import TokenClient
from gte_py.api.chain.utils import make_web3
from gte_py.api.rest import RestApi
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
        *,
        config: NetworkConfig,
        account: ChecksumAddress,
        wallet_private_key: PrivateKeyType,
    ) -> "Client":
        """Initializes a Web3 instance and returns a connected GTE client.

        Args:
            config (NetworkConfig): Network configuration settings.
            account (ChecksumAddress): Ethereum address of the user.
            wallet_private_key (PrivateKeyType): Private key for signing transactions.

        Returns:
            Client: A fully initialized client instance.
        """
        web3 = await make_web3(
            config,
            wallet_address=account,
            wallet_private_key=wallet_private_key,
        )
        return cls(web3=web3, config=config, account=account)

    def __init__(
        self,
        *,
        web3: AsyncWeb3,
        config: NetworkConfig,
        account: ChecksumAddress | None = None,
    ):
        """Initializes the GTE client and subcomponents.

        Args:
            web3 (AsyncWeb3): Web3 instance for blockchain interaction.
            config (NetworkConfig): Configuration for connecting to the network.
            account (ChecksumAddress | None): Optional user account address.
        """
        self.config = config
        self._account = account
        self._web3 = web3
        self._ws_url = config.ws_url

        self.rest = RestApi(base_url=config.api_url)

        self.clob = CLOBClient(self._web3, self.config.router_address)
        self.token = TokenClient(self._web3)
        self.info = InfoClient(self.rest, self._web3, self.clob, self.token)
        self.market = MarketClient(self.config, self.rest, self.info, self.clob)

        self.user = None
        self.execution = None

        if self._account:
            self.user = UserClient(self.config, self._account, self.clob, self.token, self.rest)
            self.execution = ExecutionClient(
                web3=self._web3,
                main_account=self._account,
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
        await self.rest.__aenter__()
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rest.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        """Close the client and release resources."""
        await self.__aexit__(None, None, None)
