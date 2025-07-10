"""Order execution functionality for the GTE client."""

import logging
from typing import Optional, Union, Any

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

logger = logging.getLogger(__name__)

from .spot import SpotExecutionClient
from .perp import PerpExecutionClient

class ExecutionClient:
    """Unified client for executing spot and perp orders and managing deposits/withdrawals on the GTE exchange."""

    def __init__(
        self,
        web3: AsyncWeb3,
        main_account: ChecksumAddress,
        gte_router_address: ChecksumAddress,
        weth_address: ChecksumAddress,
        perp_manager_address: Optional[ChecksumAddress] = None,
    ):
        self.spot = SpotExecutionClient(web3, main_account, gte_router_address, weth_address)
        self.perp = PerpExecutionClient(web3, main_account, perp_manager_address)

    async def init(self):
        """Initialize both spot and perp execution clients."""
        await self.spot.init()
        await self.perp.init()

