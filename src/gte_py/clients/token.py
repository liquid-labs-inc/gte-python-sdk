from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from gte_py.api.chain.erc20 import ERC20
from gte_py.api.chain.clob_factory import CLOBFactory
from gte_py.api.chain.clob import ICLOB
from gte_py.api.chain.router import Router
from gte_py.api.chain.weth import WETH


class TokenClient:
    """
    Client for the iCloud service.
    """

    def __init__(self, web3: AsyncWeb3):
        """
        Initialize the iCloud client.

        Args:
            web3: AsyncWeb3 instance

        """
        self._web3 = web3
        self._contracts_erc20: dict[ChecksumAddress, ERC20] = {}
        self._contracts_weth: dict[ChecksumAddress, WETH] = {}

    def get_erc20(self, token_address: ChecksumAddress) -> ERC20:
        """
        Get the ERC20 contract instance.

        Args:
            token_address: Address of the ERC20 contract

        Returns:
            ERC20 instance
        """
        if token_address not in self._contracts_erc20:
            self._contracts_erc20[token_address] = ERC20(
                web3=self._web3, contract_address=token_address
            )
        return self._contracts_erc20[token_address]

    def get_weth(self, token_address: ChecksumAddress) -> WETH:
        """
        Get the WETH contract instance.
        :param token_address:
        :return:
        """
        if token_address not in self._contracts_weth:
            self._contracts_weth[token_address] = WETH(
                web3=self._web3, contract_address=token_address
            )
        return self._contracts_weth[token_address]
