import logging
from typing import Dict, List, Any

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3.types import TxParams

from gte_py.api.chain.clob_client import CLOBClient
from gte_py.api.chain.clob_manager import ICLOBManager
from gte_py.api.rest import RestApi
from gte_py.clients.token import TokenClient
from gte_py.configs import NetworkConfig
from gte_py.models import Market, Order, Trade

logger = logging.getLogger(__name__)


class UserClient:
    def __init__(
            self,
            config: NetworkConfig,
            account: ChecksumAddress, clob: CLOBClient, token: TokenClient, rest: RestApi
    ):
        """
        Initialize the account client.

        Args:
            config: Network configuration
            account: EVM address of the account
            clob: CLOBClient instance
            token: TokenClient instance
            rest: RestApi instance for API interactions
        """
        self._config = config
        self._account = account
        self._clob = clob
        self._web3 = clob._web3
        self._token = token
        self._rest = rest

        # Initialize CLOB Manager
        self._clob_manager = ICLOBManager(web3=self._web3, contract_address=config.clob_manager_address)

    async def get_eth_balance(self) -> int:
        """
        Get the user's ETH balance.

        Returns:
            User's ETH balance in wei
        """
        return await self._web3.eth.get_balance(self._account)

    async def wrap_eth(
            self, weth_address: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ):
        return await self._token.get_weth(weth_address).deposit_eth(amount, **kwargs).send_wait()

    async def unwrap_eth(
            self, weth_address: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ):
        return await self._token.get_weth(weth_address).withdraw_eth(amount, **kwargs).send_wait()

    async def deposit(
            self, token_address: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
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
        token = self._token.get_erc20(token_address)
        if token_address == self._config.weth_address:
            weth_token = await token.balance_of(self._account)
            if weth_token < amount:
                wrap_amount = amount - weth_token
                logger.info("Not enough WETH in the account: asked for %d, got %d, lacking %d", amount, weth_token,
                            wrap_amount)
                await self.wrap_eth(
                    weth_address=token_address,
                    amount=wrap_amount,
                    **kwargs
                )
        allowance = await token.allowance(owner=self._account, spender=self._clob.get_factory_address())
        if allowance < amount:
            # approve the factory to spend tokens
            await token.approve(
                spender=self._clob.get_factory_address(), amount=amount, **kwargs
            ).send_wait()

        # Then deposit the tokens
        await self._clob.clob_factory.deposit(
            account=self._account,
            token=token_address,
            amount=amount,
            from_operator=False,
            **kwargs,
        ).send_wait()

    async def ensure_deposit(
            self,
            token_address: ChecksumAddress,
            amount: int,
            **kwargs: Unpack[TxParams]
    ) -> bool:
        """
        Ensure that the specified amount of tokens is deposited in the exchange.
        Args:
            token_address: Address of token to deposit
            amount: Amount to deposit
            **kwargs: Additional transaction parameters
        Returns:
            True if the deposit was executed
            False if the deposit was not needed

        """
        # First approve the factory to spend tokens
        exchange_balance = await self.get_token_balance(token_address)
        if exchange_balance >= amount:
            logger.info("Already enough tokens %s in the exchange: asked for %d, got %d", token_address, amount,
                        exchange_balance)
            return False
        logger.info("Not enough tokens %s in the exchange: asked for %d, got %d", token_address, amount,
                    exchange_balance)
        await self.deposit(token_address, amount, **kwargs)
        return True

    async def withdraw(
            self, token_address: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ):
        """
        Withdraw tokens from the exchange.

        Args:
            token_address: Address of token to withdraw
            amount: Amount to withdraw
            **kwargs: Additional transaction parameters

        Returns:
            TypedContractFunction for the withdrawal transaction
        """

        # Withdraw the tokens
        return await self._clob.clob_factory.withdraw(
            account=self._account, token=token_address, amount=amount, to_operator=False, **kwargs
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
        return portfolio.get("tokens", [])

    async def get_total_usd_balance(self) -> float:
        """
        Get the user's total portfolio value in USD.

        Returns:
            Total portfolio value in USD
        """
        portfolio = await self.get_portfolio()
        return float(portfolio.get("totalUsdBalance", 0))

    async def get_lp_positions(self) -> dict:
        """
        Get the user's liquidity provider positions.

        Returns:
            List of liquidity provider positions
        """
        return await self._rest.get_user_lp_positions(self._account)

    async def get_token_balance(self, token_address: ChecksumAddress) -> int:
        """
        Get the user's balance for a specific token both on-chain and in the exchange.

        Args:
            token_address: Address of the token to check

        Returns:
            Tuple of (wallet_balance, exchange_balance) in human-readable format
        """

        exchange_balance_raw = await self._clob.clob_factory.get_account_balance(
            self._account, token_address
        )

        return exchange_balance_raw

    async def approve_operator(self, operator_address: ChecksumAddress, **kwargs: Unpack[TxParams]):
        """
        Approve an operator to act on behalf of the account.

        Args:
            operator_address: Address of the operator to approve
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the approve_operator operation
        """
        logger.info(f"Approving operator {operator_address} for account {self._account}")
        return await self._clob_manager.approve_operator(
            operator=operator_address,
            **kwargs
        ).send_wait()

    async def disapprove_operator(self, operator_address: ChecksumAddress, **kwargs: Unpack[TxParams]):
        """
        Disapprove an operator from acting on behalf of the account.

        Args:
            operator_address: Address of the operator to disapprove
            **kwargs: Additional transaction parameters

        Returns:
            Transaction result from the disapprove_operator operation
        """
        logger.info(f"Disapproving operator {operator_address} for account {self._account}")
        return await self._clob_manager.disapprove_operator(
            operator=operator_address,
            **kwargs
        ).send_wait()

    async def is_operator_approved(self, operator_address: ChecksumAddress) -> bool:
        """
        Check if an operator is approved for the account.

        Args:
            operator_address: Address of the operator to check

        Returns:
            True if the operator is approved, False otherwise
        """
        return await self._clob_manager.approved_operators(
            account=self._account,
            operator=operator_address
        )

    async def get_trades(self, market: Market, limit: int = 100, offset: int = 0) -> List[Trade]:
        """
        Get trades for a specific market using the REST API.

        Args:
            market: Market to get trades from
            limit: Number of trades to retrieve (default 100)
            offset: Offset for pagination (default 0)

        Returns:
            List of Order objects representing trades
        """
        response = await self._rest.get_trades(market.address, limit, offset)
        return [Trade.from_api(trade) for trade in response]

    async def get_open_orders(
            self, market: Market | None = None
    ) -> List[Order]:
        """
        Get open orders for an address on a specific market using the REST API.

        Args:
            market: EVM address of the market (optional, defaults to None)


        Returns:
            List of Order objects representing open orders
        """

        response = await self._rest.get_user_open_orders(self._account, market and market.address)
        return [Order.from_api(order_data) for order_data in response]

    async def get_filled_orders(
            self, market: Market | None = None
    ) -> List[Order]:
        """
        Get filled orders for an address on a specific market using the REST API.

        Args:
            market: EVM address of the market (optional, defaults to None)

        Returns:
            List of Order objects representing filled orders
        """

        response = await self._rest.get_user_filled_orders(self._account, market and market.address)
        return [Order.from_api(order_data) for order_data in response]

    async def get_order_history(
            self, market: Market | None = None
    ) -> List[Order]:
        """
        Get order history for an address on a specific market using the REST API.

        Args:
            market: EVM address of the market (optional, defaults to None)

        Returns:
            List of Order objects representing order history
        """

        response = await self._rest.get_user_order_history(self._account, market and market.address)
        return [Order.from_api(order_data) for order_data in response]
