"""High-level GTE client."""

import logging
from decimal import getcontext

from eth_typing import ChecksumAddress
from eth_account.types import PrivateKeyType

from ..api.chain.utils import make_web3
from ..api.rest import RestApi
from ..api.ws import WebSocketApi
from ..configs import NetworkConfig

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
        wallet_private_key: PrivateKeyType | None = None,
    ):
        """Initializes the GTE client and subcomponents.

        Args:
            config: Network configuration for connecting to the network.
            wallet_address: Optional user wallet address.
            wallet_private_key: Optional wallet private key for signing transactions.
        """
        getcontext().prec = 40
        self.config = config
        
        # Initialize Web3 and account
        self._web3, self._account = make_web3(
            config.rpc_http,
            wallet_private_key=wallet_private_key,
        )

        # Initialize API clients
        self.rest = RestApi(base_url=config.api_url)
        self.websocket = WebSocketApi(ws_url=config.ws_url)
        
        # Initialize core clients
        self.info = InfoClient(self.rest, self.websocket)
        self._execution: ExecutionClient | None = None
        
        if self._account:
            self._execution = ExecutionClient(
                web3=self._web3,
                account=self._account,
                gte_router_address=config.router_address,
                weth_address=config.weth_address,
                clob_manager_address=config.clob_manager_address,
            )
        
        self.connected = False
    
    async def connect(self):
        if self.connected:
            return
        
        await self.rest.connect()
        await self.websocket.connect()
        
        if self._execution:
            await self._execution.init()
        
        self.connected = True
    
    async def disconnect(self):
        if not self.connected:
            return
        
        await self.info.unsubscribe_all()
        await self.rest.disconnect()
        await self.websocket.disconnect()
        
        self.connected = False
    
    async def __aenter__(self) -> "GTEClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @property
    def execution(self) -> ExecutionClient:
        assert self._execution is not None, "Execution client not initialized"
        return self._execution

