from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.contracts.factory import CLOBFactory
from gte_py.api.contracts.iclob import ICLOB
from gte_py.api.contracts.router import Router


class CLOBClient:
    """
    Client for the iCloud service.
    """

    def __init__(self, web3: AsyncWeb3, router_address: ChecksumAddress):
        """
        Initialize the iCloud client.

        Args:
            web3: AsyncWeb3 instance

        """
        self._web3 = web3
        self._clob_factory_address: ChecksumAddress | None = None
        self.clob_factory: CLOBFactory | None = None
        self._router_address = router_address
        self._router = Router(web3=web3, contract_address=self._router_address)
        self._contracts: dict[ChecksumAddress, ICLOB] = {}

    async def init(self):
        # Get and initialize CLOB factory
        self._clob_factory_address = await self._router.get_clob_factory()
        self.clob_factory = CLOBFactory(web3=self._web3, contract_address=self._clob_factory_address)

    def get_clob(self, clob_address: ChecksumAddress) -> ICLOB:
        """
        Get the iCloud contract instance.

        Args:
            clob_address: Address of the iCloud contract

        Returns:
            ICLOB instance
        """
        if clob_address not in self._contracts:
            self._contracts[clob_address] = ICLOB(web3=self._web3, contract_address=clob_address)
        return self._contracts[clob_address]
