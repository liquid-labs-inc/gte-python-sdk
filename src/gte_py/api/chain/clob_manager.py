from enum import IntEnum
from typing import TypeVar, Union, List

from eth_typing import ChecksumAddress
from typing_extensions import Unpack
from web3 import AsyncWeb3
from web3.types import TxParams

from .event_source import EventSource, EventStream
from .events import (
    AccountCreditedEvent,
    AccountDebitedEvent,
    AccountFeeTierUpdatedEvent,
    DepositEvent,
    FeeCollectedEvent,
    FeeRecipientSetEvent,
    # MarketCreatedEvent,
    OperatorApprovedEvent,
    OperatorDisapprovedEvent,
    WithdrawEvent,
    parse_account_credited,
    parse_account_debited,
    parse_account_fee_tier_updated,
    parse_deposit,
    parse_fee_collected,
    parse_fee_recipient_set,
    # parse_market_created,
    parse_operator_approved,
    parse_operator_disapproved,
    parse_withdraw,
)
from .utils import TypedContractFunction, load_abi

# Type variable for contract function return types
T = TypeVar("T")


class FeeTiers(IntEnum):
    """Fee tier levels for trading accounts"""
    ZERO = 0
    ONE = 1
    TWO = 2


class CLOBManagerError(Exception):
    """Base exception for CLOB Manager contract errors"""
    pass


class ICLOBManager:
    """
    Python wrapper for the GTE CLOB Manager smart contract.
    Provides methods to interact with the CLOB Manager functionality including:
    - Market creation
    - Deposit/withdrawal management
    - Fee management
    - Operator approvals
    - Trading settlement
    """

    def __init__(
            self,
            web3: AsyncWeb3,
            contract_address: ChecksumAddress,
    ):
        """
        Initialize the ICLOBManager wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the CLOB Manager contract
        """
        self.web3 = web3
        self.address = contract_address
        loaded_abi = load_abi("clob_manager")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

        # Initialize event sources
        self._account_credited_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.AccountCredited,
            parser=parse_account_credited
        )

        self._account_debited_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.AccountDebited,
            parser=parse_account_debited
        )

        self._account_fee_tier_updated_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.AccountFeeTierUpdated,
            parser=parse_account_fee_tier_updated
        )

        self._deposit_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.Deposit,
            parser=parse_deposit
        )

        self._fee_collected_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.FeeCollected,
            parser=parse_fee_collected
        )

        self._fee_recipient_set_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.FeeRecipientSet,
            parser=parse_fee_recipient_set
        )

        # self._market_created_event_source = EventSource(
        #     web3=self.web3,
        #     event=self.contract.events.MarketCreated,
        #     parser=parse_market_created
        # )

        self._operator_approved_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OperatorApproved,
            parser=parse_operator_approved
        )

        self._operator_disapproved_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.OperatorDisapproved,
            parser=parse_operator_disapproved
        )

        self._withdraw_event_source = EventSource(
            web3=self.web3,
            event=self.contract.events.Withdraw,
            parser=parse_withdraw
        )

    # ================= READ METHODS =================

    async def approved_operators(self, account: ChecksumAddress, operator: ChecksumAddress) -> bool:
        """
        Check if an operator is approved for an account.

        Args:
            account: The account address
            operator: The operator address

        Returns:
            True if the operator is approved, False otherwise
        """
        return await self.contract.functions.approvedOperators(account, operator).call()

    async def beacon(self) -> ChecksumAddress:
        """Get the address of the beacon used for market proxy deployments."""
        return await self.contract.functions.beacon().call()

    async def get_account_balance(self, account: ChecksumAddress, token: ChecksumAddress) -> int:
        """
        Get the balance of a token for an account.

        Args:
            account: The account address
            token: The token address

        Returns:
            The balance amount
        """
        return await self.contract.functions.getAccountBalance(account, token).call()

    async def get_event_nonce(self) -> int:
        """Get the current event nonce."""
        return await self.contract.functions.getEventNonce().call()

    async def get_fee_recipient(self) -> ChecksumAddress:
        """Get the address of the fee recipient."""
        return await self.contract.functions.getFeeRecipient().call()

    async def get_fee_tier(self, account: ChecksumAddress) -> FeeTiers:
        """
        Get the fee tier for an account.

        Args:
            account: The account address

        Returns:
            The fee tier enum value
        """
        return FeeTiers(await self.contract.functions.getFeeTier(account).call())

    async def get_maker_fee_rate(self, fee_tier: FeeTiers) -> int:
        """
        Get the maker fee rate for a specific fee tier.

        Args:
            fee_tier: The fee tier enum value

        Returns:
            The maker fee rate (in basis points)
        """
        return await self.contract.functions.getMakerFeeRate(fee_tier).call()

    async def get_market_address(self, quote_token: ChecksumAddress, base_token: ChecksumAddress) -> ChecksumAddress:
        """
        Get the market address for a token pair.

        Args:
            quote_token: The quote token address
            base_token: The base token address

        Returns:
            The market contract address
        """
        return await self.contract.functions.getMarketAddress(quote_token, base_token).call()

    async def get_taker_fee_rate(self, fee_tier: FeeTiers) -> int:
        """
        Get the taker fee rate for a specific fee tier.

        Args:
            fee_tier: The fee tier enum value

        Returns:
            The taker fee rate (in basis points)
        """
        return await self.contract.functions.getTakerFeeRate(fee_tier).call()

    async def is_market(self, market: ChecksumAddress) -> bool:
        """
        Check if an address is a valid market contract.

        Args:
            market: The market address to check

        Returns:
            True if it's a valid market, False otherwise
        """
        return await self.contract.functions.isMarket(market).call()

    async def maker_fees(self) -> int:
        """Get the packed maker fee rates."""
        return await self.contract.functions.makerFees().call()

    async def max_num_orders(self) -> int:
        """Get the maximum number of orders allowed per market."""
        return await self.contract.functions.maxNumOrders().call()

    async def owner(self) -> ChecksumAddress:
        """Get the contract owner address."""
        return await self.contract.functions.owner().call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        """
        Get the expiration timestamp for an ownership handover request.

        Args:
            pending_owner: The address of the pending owner

        Returns:
            The expiration timestamp (0 if no request)
        """
        return await self.contract.functions.ownershipHandoverExpiresAt(pending_owner).call()

    async def taker_fees(self) -> int:
        """Get the packed taker fee rates."""
        return await self.contract.functions.takerFees().call()

    # ================= WRITE METHODS =================

    def approve_operator(self, operator: ChecksumAddress, **kwargs: Unpack[TxParams]) -> TypedContractFunction[None]:
        """
        Approve an operator for the caller's account.

        Args:
            operator: The operator address to approve
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.approveOperator(operator)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.OperatorApproved, parse_operator_approved
        )

    def cancel_ownership_handover(self, **kwargs: Unpack[TxParams]) -> TypedContractFunction[None]:
        """
        Cancel a pending ownership handover request.

        Args:
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.cancelOwnershipHandover()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def collect_fees(self, token: ChecksumAddress, **kwargs: Unpack[TxParams]) -> TypedContractFunction[int]:
        """
        Collect accumulated fees for a specific token.

        Args:
            token: The token address to collect fees for
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.collectFees(token)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.FeeCollected, parse_fee_collected
        )

    def complete_ownership_handover(
            self, pending_owner: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Complete a pending ownership handover.

        Args:
            pending_owner: The address of the pending owner
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    # def create_market(
    #         self, base_token: ChecksumAddress, quote_token: ChecksumAddress, settings: ICLOBSettingsParams,
    #         **kwargs: Unpack[TxParams]
    # ) -> TypedContractFunction[ChecksumAddress]:
    #     """
    #     Create a new market for a token pair.
    #
    #     Args:
    #         base_token: The base token address
    #         quote_token: The quote token address
    #         settings: The market settings parameters
    #         **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
    #
    #     Returns:
    #         TypedContractFunction that can be used to execute the transaction
    #     """
    #     func = self.contract.functions.createMarket(base_token, quote_token, settings)
    #     params = {**kwargs}
    #     return TypedContractFunction(func, params).with_event(
    #         self.contract.events.MarketCreated, parse_market_created
    #     )

    def credit_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Credit an account with tokens (admin only).

        Args:
            account: The account to credit
            token: The token address
            amount: The amount to credit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.creditAccount(account, token, amount)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.AccountCredited, parse_account_credited
        )

    def debit_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Debit an account with tokens (admin or market only).

        Args:
            account: The account to debit
            token: The token address
            amount: The amount to debit
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.debitAccount(account, token, amount)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.AccountDebited, parse_account_debited
        )

    def deposit(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, from_operator: bool,
            **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Deposit tokens into an account.

        Args:
            account: The account to deposit to
            token: The token address
            amount: The amount to deposit
            from_operator: If True, tokens are transferred from an approved operator
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.deposit(account, token, amount, from_operator)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.Deposit, parse_deposit
        )

    def disapprove_operator(
            self, operator: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Disapprove an operator for the caller's account.

        Args:
            operator: The operator address to disapprove
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.disapproveOperator(operator)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.OperatorDisapproved, parse_operator_disapproved
        )

    def initialize(
            self, owner: ChecksumAddress, fee_recipient: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Initialize the CLOB Manager contract.

        Args:
            owner: The contract owner address
            fee_recipient: The fee recipient address
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.initialize(owner, fee_recipient)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def pull_from_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Pull tokens from an account (admin only).

        Args:
            account: The account to pull from
            token: The token address
            amount: The amount to pull
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.pullFromAccount(account, token, amount)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def push_to_account(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Push tokens to an account (admin only).

        Args:
            account: The account to push to
            token: The token address
            amount: The amount to push
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.pushToAccount(account, token, amount)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def renounce_ownership(self, **kwargs: Unpack[TxParams]) -> TypedContractFunction[None]:
        """
        Renounce contract ownership.

        Args:
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.renounceOwnership()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def request_ownership_handover(self, **kwargs: Unpack[TxParams]) -> TypedContractFunction[None]:
        """
        Request ownership handover.

        Args:
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.requestOwnershipHandover()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def set_account_fee_tiers(
            self, accounts: List[ChecksumAddress], fee_tiers: List[FeeTiers], **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Set fee tiers for multiple accounts.

        Args:
            accounts: List of account addresses
            fee_tiers: List of fee tier enum values
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.setAccountFeeTiers(accounts, [int(tier) for tier in fee_tiers])
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def set_fee_recipient(
            self, new_fee_recipient: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Set a new fee recipient address.

        Args:
            new_fee_recipient: The new fee recipient address
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.setFeeRecipient(new_fee_recipient)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.FeeRecipientSet, parse_fee_recipient_set
        )

    # def settle_incoming_order(
    #         self, params: ICLOBSettleParams, **kwargs: Unpack[TxParams]
    # ) -> TypedContractFunction[int]:
    #     """
    #     Settle an incoming order (market only).
    #
    #     Args:
    #         params: The settlement parameters
    #         **kwargs: Additional transaction parameters (gas, gasPrice, etc.)
    #
    #     Returns:
    #         TypedContractFunction that can be used to execute the transaction
    #     """
    #     func = self.contract.functions.settleIncomingOrder(params)
    #     params_tx = {**kwargs}
    #     return TypedContractFunction(func, params_tx)

    def transfer_ownership(
            self, new_owner: ChecksumAddress, **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Transfer contract ownership.

        Args:
            new_owner: The new owner address
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.transferOwnership(new_owner)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def withdraw(
            self, account: ChecksumAddress, token: ChecksumAddress, amount: int, to_operator: bool,
            **kwargs: Unpack[TxParams]
    ) -> TypedContractFunction[None]:
        """
        Withdraw tokens from an account.

        Args:
            account: The account to withdraw from
            token: The token address
            amount: The amount to withdraw
            to_operator: If True, tokens are transferred to an approved operator
            **kwargs: Additional transaction parameters (gas, gasPrice, etc.)

        Returns:
            TypedContractFunction that can be used to execute the transaction
        """
        func = self.contract.functions.withdraw(account, token, amount, to_operator)
        params = {**kwargs}
        return TypedContractFunction(func, params).with_event(
            self.contract.events.Withdraw, parse_withdraw
        )

    # ================= EVENT METHODS =================

    async def get_account_credited_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[AccountCreditedEvent]:
        """
        Get historical AccountCredited events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of AccountCredited events
        """
        return await self._account_credited_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_account_credited_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[AccountCreditedEvent]:
        """
        Stream AccountCredited events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of AccountCredited events
        """
        return self._account_credited_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_account_debited_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[AccountDebitedEvent]:
        """
        Get historical AccountDebited events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of AccountDebited events
        """
        return await self._account_debited_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_account_debited_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[AccountDebitedEvent]:
        """
        Stream AccountDebited events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of AccountDebited events
        """
        return self._account_debited_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_account_fee_tier_updated_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[AccountFeeTierUpdatedEvent]:
        """
        Get historical AccountFeeTierUpdated events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of AccountFeeTierUpdated events
        """
        return await self._account_fee_tier_updated_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_account_fee_tier_updated_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[AccountFeeTierUpdatedEvent]:
        """
        Stream AccountFeeTierUpdated events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of AccountFeeTierUpdated events
        """
        return self._account_fee_tier_updated_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_deposit_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[DepositEvent]:
        """
        Get historical Deposit events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of Deposit events
        """
        return await self._deposit_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_deposit_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[DepositEvent]:
        """
        Stream Deposit events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of Deposit events
        """
        return self._deposit_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_fee_collected_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[FeeCollectedEvent]:
        """
        Get historical FeeCollected events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of FeeCollected events
        """
        return await self._fee_collected_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_fee_collected_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[FeeCollectedEvent]:
        """
        Stream FeeCollected events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of FeeCollected events
        """
        return self._fee_collected_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_fee_recipient_set_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[FeeRecipientSetEvent]:
        """
        Get historical FeeRecipientSet events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of FeeRecipientSet events
        """
        return await self._fee_recipient_set_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_fee_recipient_set_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[FeeRecipientSetEvent]:
        """
        Stream FeeRecipientSet events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of FeeRecipientSet events
        """
        return self._fee_recipient_set_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    # async def get_market_created_events(
    #         self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    # ) -> List[MarketCreatedEvent]:
    #     """
    #     Get historical MarketCreated events.
    #
    #     Args:
    #         from_block: Starting block number
    #         to_block: Ending block number or 'latest'
    #         **filter_params: Additional filter parameters
    #
    #     Returns:
    #         List of MarketCreated events
    #     """
    #     return await self._market_created_event_source.get_historical(
    #         from_block=from_block, to_block=to_block, **filter_params
    #     )
    #
    # def stream_market_created_events(
    #         self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    # ) -> EventStream[MarketCreatedEvent]:
    #     """
    #     Stream MarketCreated events asynchronously.
    #
    #     Args:
    #         from_block: Starting block number or 'latest'
    #         poll_interval: Interval between polls in seconds
    #         **filter_params: Additional filter parameters
    #
    #     Returns:
    #         EventStream of MarketCreated events
    #     """
    #     return self._market_created_event_source.get_streaming(
    #         from_block=from_block, poll_interval=poll_interval, **filter_params
    #     )

    async def get_operator_approved_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[OperatorApprovedEvent]:
        """
        Get historical OperatorApproved events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OperatorApproved events
        """
        return await self._operator_approved_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_operator_approved_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[OperatorApprovedEvent]:
        """
        Stream OperatorApproved events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OperatorApproved events
        """
        return self._operator_approved_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_operator_disapproved_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[OperatorDisapprovedEvent]:
        """
        Get historical OperatorDisapproved events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of OperatorDisapproved events
        """
        return await self._operator_disapproved_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_operator_disapproved_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[OperatorDisapprovedEvent]:
        """
        Stream OperatorDisapproved events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of OperatorDisapproved events
        """
        return self._operator_disapproved_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )

    async def get_withdraw_events(
            self, from_block: int, to_block: Union[int, str] = "latest", **filter_params
    ) -> List[WithdrawEvent]:
        """
        Get historical Withdraw events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number or 'latest'
            **filter_params: Additional filter parameters
            
        Returns:
            List of Withdraw events
        """
        return await self._withdraw_event_source.get_historical(
            from_block=from_block, to_block=to_block, **filter_params
        )

    def stream_withdraw_events(
            self, from_block: Union[int, str] = "latest", poll_interval: float = 2.0, **filter_params
    ) -> EventStream[WithdrawEvent]:
        """
        Stream Withdraw events asynchronously.
        
        Args:
            from_block: Starting block number or 'latest'
            poll_interval: Interval between polls in seconds
            **filter_params: Additional filter parameters
            
        Returns:
            EventStream of Withdraw events
        """
        return self._withdraw_event_source.get_streaming(
            from_block=from_block, poll_interval=poll_interval, **filter_params
        )
