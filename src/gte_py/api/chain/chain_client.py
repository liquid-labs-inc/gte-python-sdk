from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.chain.clob import Clob
from gte_py.api.chain.clob_manager import ClobManager
from gte_py.api.chain.router import Router
from gte_py.api.chain.uniswap_router import UniswapRouter
from gte_py.api.chain.erc20 import Erc20
from gte_py.api.chain.weth import Weth
from gte_py.api.chain.launchpad import Launchpad


class ChainClient:
    """
    Simplified chain client that provides access to all contract wrappers and addresses.
    
    Provides a clean API with:
    - Properties for singleton contracts and addresses (router, clob_factory, univ2_router, weth)
    - Methods for parameterized contracts (get_clob, get_erc20)
    - Automatic caching to avoid redundant router calls and contract instantiation
    """

    def __init__(self, web3: AsyncWeb3, router_address: ChecksumAddress):
        """
        Initialize the chain client.

        Args:
            web3: AsyncWeb3 instance
            router_address: Address of the router contract
        """
        self._web3 = web3
        self._router_address = router_address
        self._router = Router(web3=web3, address=self._router_address)
        
        # Cached addresses
        self._clob_manager_address: ChecksumAddress | None = None
        self._univ2_router_address: ChecksumAddress | None = None
        self._weth_address: ChecksumAddress | None = None
        self._launchpad_address: ChecksumAddress | None = None
        
        # Cached contract instances
        self._univ2_router: UniswapRouter | None = None
        self._clob_manager: ClobManager | None = None
        self._weth: Weth | None = None
        self._launchpad: Launchpad | None = None
        self._clob_contracts: dict[ChecksumAddress, Clob] = {}
        self._erc20_contracts: dict[ChecksumAddress, Erc20] = {}

    async def init(self):
        """
        Initialize the chain client by fetching required addresses.
        """
        if self._clob_manager_address and self._univ2_router_address and self._weth_address:
            return

        # Get and cache addresses from router
        self._clob_manager_address = await self._router.clob_factory()
        self._univ2_router_address = await self._router.uni_v2_router()
        self._weth_address = await self._router.weth()
        self._launchpad_address = await self._router.launchpad()
        
        self._clob_manager = ClobManager(web3=self._web3, address=self._clob_manager_address)
        self._univ2_router = UniswapRouter(web3=self._web3, address=self._univ2_router_address)
        self._weth = Weth(web3=self._web3, address=self._weth_address)
        self._launchpad = Launchpad(web3=self._web3, address=self._launchpad_address)

    # Router properties
    @property
    def router(self) -> Router:
        """Get the router contract instance."""
        return self._router

    @property
    def router_address(self) -> ChecksumAddress:
        """Get the router contract address."""
        return self._router_address

    @property
    def clob_manager(self) -> ClobManager:
        """Get the CLOB manager contract instance."""
        if not self._clob_manager:
            raise ValueError("CLOB manager is not initialized. Call init() first.")
        return self._clob_manager
    
    @property
    def clob_manager_address(self) -> ChecksumAddress:
        """Get the CLOB manager contract address."""
        if not self._clob_manager_address:
            raise ValueError("CLOB manager address is not initialized. Call init() first.")
        return self._clob_manager_address
    
    # UniswapV2 Router properties
    @property
    def univ2_router(self) -> UniswapRouter:
        """Get the UniswapV2 router contract instance."""
        if not self._univ2_router:
            raise ValueError("UniswapV2 router is not initialized. Call init() first.")
        return self._univ2_router

    @property
    def univ2_router_address(self) -> ChecksumAddress:
        """Get the UniswapV2 router contract address."""
        if not self._univ2_router_address:
            raise ValueError("UniswapV2 router address is not initialized. Call init() first.")
        return self._univ2_router_address

    # WETH properties (singleton)
    @property
    def weth(self) -> Weth:
        """Get the WETH contract instance."""
        if not self._weth:
            raise ValueError("WETH is not initialized. Call init() first.")
        return self._weth

    @property
    def weth_address(self) -> ChecksumAddress:
        """Get the WETH contract address."""
        if not self._weth_address:
            raise ValueError("WETH address is not initialized. Call init() first.")
        return self._weth_address
    
    @property
    def launchpad_address(self) -> ChecksumAddress:
        """Get the Launchpad contract instance."""
        if not self._launchpad_address:
            raise ValueError("Launchpad address is not initialized. Call init() first.")
        return self._launchpad_address
    
    @property
    def launchpad(self) -> Launchpad:
        """Get the Launchpad contract instance."""
        if not self._launchpad:
            raise ValueError("Launchpad is not initialized. Call init() first.")
        return self._launchpad
    
    # ICLOB methods (parameterized)
    def get_clob(self, clob_address: ChecksumAddress) -> Clob:
        """
        Get the ICLOB contract instance.

        Args:
            clob_address: Address of the CLOB contract

        Returns:
            Clob instance
        """
        if clob_address not in self._clob_contracts:
            self._clob_contracts[clob_address] = Clob(
                web3=self._web3, address=clob_address
            )
        return self._clob_contracts[clob_address]

    # ERC20 methods (parameterized)
    def get_erc20(self, token_address: ChecksumAddress) -> Erc20:
        """
        Get the ERC20 contract instance.

        Args:
            token_address: Address of the ERC20 contract

        Returns:
            Erc20 instance
        """
        if token_address not in self._erc20_contracts:
            self._erc20_contracts[token_address] = Erc20(
                web3=self._web3, address=token_address
            )
        return self._erc20_contracts[token_address]
