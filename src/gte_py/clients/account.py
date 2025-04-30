from typing import Dict, List, Any, Optional, Tuple

from eth_typing import ChecksumAddress

from gte_py.api.rest import RestApi
from gte_py.clients.iclob import CLOBClient
from gte_py.clients.token import TokenClient


class AccountClient:
    def __init__(self,
                 account: ChecksumAddress,
                 clob: CLOBClient, 
                 token: TokenClient,
                 rest: RestApi):
        """
        Initialize the account client.

        Args:
            account: EVM address of the account
            clob: CLOBClient instance
            token: TokenClient instance
            rest: RestApi instance for API interactions
        """
        self._account = account
        self.clob = clob
        self.token = token
        self._rest = rest

    async def wrap_eth(
            self,
            weth_address: ChecksumAddress,
            amount: int,
            **kwargs
    ):
        return await self.token.get_weth(weth_address).deposit_eth(amount, **kwargs).send_wait()

    async def unwrap_eth(
            self,
            weth_address: ChecksumAddress,
            amount: int,
            **kwargs
    ):
        return await self.token.get_weth(weth_address).withdraw_eth(amount, **kwargs).send_wait()

    async def deposit_to_market(
            self,
            token_address: ChecksumAddress,
            amount: int,
            **kwargs
    ):
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
        await token.approve(
            spender=self.clob.get_factory_address(),
            amount=amount_in_atoms,
            **kwargs
        ).send_wait()

        # Then deposit the tokens
        await self.clob.clob_factory.deposit(
            account=self._account,
            token=token_address,
            amount=amount_in_atoms,
            from_operator=False,
            **kwargs
        ).send_wait()

    async def withdraw_from_market(
            self,
            token_address: ChecksumAddress,
            amount: int,
            **kwargs
    ):
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
        return await self.clob.clob_factory.withdraw(
            account=self._account,
            token=token_address,
            amount=amount,
            to_operator=False,
            **kwargs
        ).send_wait()

    async def get_portfolio(self) -> Dict[str, Any]:
        """
        Get the user's portfolio including token balances and USD values.

        Returns:
            Dict containing portfolio information with token balances and total USD value
        """
        return await self._rest.get_user_portfolio(self._account)

    async def get_token_balances(self) -> List[Dict[str, Any]]:
        """
        Get the user's token balances with USD values.

        Returns:
            List of token balances with associated information
        """
        portfolio = await self.get_portfolio()
        return portfolio.get('tokens', [])

    async def get_total_usd_balance(self) -> float:
        """
        Get the user's total portfolio value in USD.

        Returns:
            Total portfolio value in USD
        """
        portfolio = await self.get_portfolio()
        return float(portfolio.get('totalUsdBalance', 0))

    async def get_lp_positions(self) -> List[Dict[str, Any]]:
        """
        Get the user's liquidity provider positions.

        Returns:
            List of liquidity provider positions
        """
        return await self._rest.get_user_lp_positions(self._account)

    async def get_token_balance(self, token_address: ChecksumAddress) -> Tuple[float, float]:
        """
        Get the user's balance for a specific token both on-chain and in the exchange.

        Args:
            token_address: Address of the token to check

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """
        token = self.token.get_erc20(token_address)

        # Get wallet balance
        wallet_balance_raw = await token.balance_of(self._account)
        wallet_balance = await token.convert_amount_to_float(wallet_balance_raw)

        # Get exchange balance
        exchange_balance_raw = await self.clob.clob_factory.get_account_balance(self._account, token_address)
        exchange_balance = await token.convert_amount_to_float(exchange_balance_raw)

        return wallet_balance, exchange_balance


