from typing import List

from eth_typing import ChecksumAddress

from gte_py.api.chain.utils import TypedContractFunction
from gte_py.clients.iclob import CLOBClient
from gte_py.clients.token import TokenClient


class AccountClient:
    def __init__(self,
                 sender_address: ChecksumAddress,
                 clob: CLOBClient, token: TokenClient):
        """
        Initialize the account client.

        Args:
            clob: CLOBClient instance
            token: TokenClient instance
        """
        self._sender_address = sender_address
        self.clob = clob
        self.token = token

    def wrap_eth(
            self,
            weth_address: ChecksumAddress,
            amount: int,
            **kwargs
    ) -> TypedContractFunction:
        return self.token.get_weth(weth_address).deposit_eth(amount, **kwargs)

    def unwrap_eth(
            self,
            weth_address: ChecksumAddress,
            amount: int,
            **kwargs
    ) -> TypedContractFunction:
        return self.token.get_weth(weth_address).withdraw_eth(amount, **kwargs)

    def deposit_to_market(
            self,
            token_address: ChecksumAddress,
            amount: int,
            **kwargs
    ) -> List[TypedContractFunction]:
        """
        Deposit tokens to the exchange for trading.

        Args:
            token_address: Address of token to deposit
            amount: Amount to deposit
            **kwargs: Additional transaction parameters

        Returns:
            List of TypedContractFunction objects (approve and deposit)
        """

        token = self.token.get_erc20(token_address)
        amount_in_atoms = amount

        # First approve the factory to spend tokens
        approve_tx = token.approve(
            spender=self.clob._clob_factory_address,
            amount=amount_in_atoms,
            **kwargs
        )

        # Then deposit the tokens
        deposit_tx = self.clob.clob_factory.deposit(
            account=self._sender_address,
            token=token_address,
            amount=amount_in_atoms,
            from_operator=False,
            **kwargs
        )

        return [approve_tx, deposit_tx]

    async def withdraw_from_market(
            self,
            token_address: ChecksumAddress,
            amount: int,
            **kwargs
    ) -> TypedContractFunction:
        """
        Withdraw tokens from the exchange.

        Args:
            token_address: Address of token to withdraw
            amount: Amount to withdraw
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction for the withdraw transaction
        """

        # Withdraw the tokens
        return self.clob.clob_factory.withdraw(
            account=self._sender_address,
            token=token_address,
            amount=amount,
            to_operator=False,
            **kwargs
        )
