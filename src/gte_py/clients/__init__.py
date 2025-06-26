"""High-level GTE client."""

import logging

from eth_typing import ChecksumAddress
from eth_account.types import PrivateKeyType

from gte_py.api.chain.utils import make_web3, Web3RequestManager
from gte_py.api.rest import RestApi
from gte_py.api.ws import WebSocketApi
from gte_py.configs import NetworkConfig

from .execution import ExecutionClient
from .info import InfoClient

logger = logging.getLogger(__name__)


class GTEClient:
    """User-friendly client for interacting with GTE.

    Provides an interface to communicate with the GTE protocol through REST and Web3.
    Aggregates low-level clients including CLOB, token, user, market, info, and execution layers.
    """

    def __init__(
        self,
        config: NetworkConfig,
        wallet_address: ChecksumAddress | None = None,
        wallet_private_key: PrivateKeyType | None = None,
    ):
        """Initializes the GTE client and subcomponents.

        Args:
            web3 (AsyncWeb3): Web3 instance for blockchain interaction.
            config (NetworkConfig): Configuration for connecting to the network.
            wallet_address (ChecksumAddress | None): Optional user wallet address.
        """
        self.config = config
        self._wallet_address = wallet_address
        
        self._web3, self._account = make_web3(
            config.rpc_http,
            wallet_address=wallet_address,
            wallet_private_key=wallet_private_key,
        )

        self.rest = RestApi(base_url=config.api_url)
        self.websocket = WebSocketApi(ws_url=config.ws_url)
        self.info = InfoClient(self.rest, self.websocket)

        self.execution = None
        
        if self._wallet_address:
            # self.execution = ExecutionClient(
            #     web3=self._web3,
            #     main_account=self._wallet_address,
            # )
            pass
        
        self.connected = False
    
    async def connect(self):
        if self.connected:
            return
        
        if self._account:
            await Web3RequestManager.ensure_instance(self._web3, self._account)
        
        await self.rest.connect()
        await self.websocket.connect()
        self.connected = True
    
    async def disconnect(self):
        if not self.connected:
            return
        
        await self.info.clear_subscriptions()
        await self.rest.disconnect()
        await self.websocket.disconnect()
        
        self.connected = False
    
    async def __aenter__(self) -> "GTEClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

