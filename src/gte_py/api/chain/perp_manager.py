from eth_typing import ChecksumAddress
from web3 import AsyncWeb3

from .structs import (
    PostLimitOrderArgs,
    PostFillOrderArgs,
    MarketConfig,
    Position
)
from .utils import load_abi, TypedContractFunction


# from .events import parse_withdraw_collateral  # To be implemented


class PerpManager:
    """
    Python wrapper for the GTE Perp Manager smart contract.
    Provides methods to interact with the Perp Manager functionality including:
    - Market creation
    - Deposit/withdrawal management
    - Fee management
    - Operator approvals
    - Trading settlement
    - Perp-specific methods
    """


    def __init__(
        self,
        web3: AsyncWeb3,
        contract_address: ChecksumAddress,
    ):
        """
        Initialize the IPerpManager wrapper.

        Args:
            web3: AsyncWeb3 instance connected to a provider
            contract_address: Address of the Perp Manager contract
        """
        self.web3 = web3
        self.address = contract_address
        loaded_abi = load_abi("PerpManager")
        self.contract = self.web3.eth.contract(address=self.address, abi=loaded_abi)

        # Event sources (add more as needed)
        # self._withdraw_collateral_event_source = EventSource(
        #     web3=self.web3,
        #     event=self.contract.events.WithdrawCollateral,
        #     parser=parse_withdraw_collateral
        # )



    # ================= READ METHODS =================

    async def get_collateral_balance(self, account: ChecksumAddress) -> int:
        return await self.contract.functions.getCollateralBalance(account).call()


    async def get_cumulative_funding(self, asset: str) -> int:
        return await self.contract.functions.getCumulativeFunding(asset).call()


    async def get_divergence_cap(self, asset: str) -> int:
        return await self.contract.functions.getDivergenceCap(asset).call()


    async def get_funding_interval(self, asset: str) -> int:
        return await self.contract.functions.getFundingInterval(asset).call()

    async def get_insurance_fund_balance(self) -> int:
        return await self.contract.functions.getInsuranceFundBalance().call()


    async def get_last_funding_time(self, asset: str) -> int:
        return await self.contract.functions.getLastFundingTime(asset).call()


    async def get_limit_order(self, asset: str, order_id: int) -> dict:
        return await self.contract.functions.getLimitOrder(asset, order_id).call()


    async def get_limit_order_backstop(self, asset: str, order_id: int) -> dict:
        return await self.contract.functions.getLimitOrderBackstop(asset, order_id).call()


    async def get_limit_order_counter(self, asset: str) -> int:
        return await self.contract.functions.getLimitOrderCounter(asset).call()


    async def get_limit_order_counter_backstop(self, asset: str) -> int:
        return await self.contract.functions.getLimitOrderCounterBackstop(asset).call()


    async def get_liquidation_fee_rate(self, asset: str) -> int:
        return await self.contract.functions.getLiquidationFeeRate(asset).call()

    async def get_margin_balance(self, account: ChecksumAddress, subaccount: int) -> int:
        return await self.contract.functions.getMarginBalance(account, subaccount).call()

    async def get_margin_debt_gross(self, account: ChecksumAddress, subaccount: int) -> int:
        return await self.contract.functions.getMarginDebtGross(account, subaccount).call()


    async def get_mark_price(self, asset: str) -> int:
        return await self.contract.functions.getMarkPrice(asset).call()


    async def get_market_status(self, asset: str) -> int:
        return await self.contract.functions.getMarketStatus(asset).call()


    async def get_max_funding_rate(self, asset: str) -> int:
        return await self.contract.functions.getMaxFundingRate(asset).call()


    async def get_max_leverage(self, asset: str) -> int:
        return await self.contract.functions.getMaxLeverage(asset).call()


    async def get_max_limits_per_tx(self, asset: str) -> int:
        return await self.contract.functions.getMaxLimitsPerTx(asset).call()


    async def get_max_num_orders(self, asset: str) -> int:
        return await self.contract.functions.getMaxNumOrders(asset).call()


    async def get_min_limit_order_amount_in_base(self, asset: str) -> int:
        return await self.contract.functions.getMinLimitOrderAmountInBase(asset).call()


    async def get_min_margin_ratio(self, asset: str) -> int:
        return await self.contract.functions.getMinMarginRatio(asset).call()


    async def get_min_margin_ratio_backstop(self, asset: str) -> int:
        return await self.contract.functions.getMinMarginRatioBackstop(asset).call()


    async def get_num_asks(self, asset: str) -> int:
        return await self.contract.functions.getNumAsks(asset).call()


    async def get_num_asks_backstop(self, asset: str) -> int:
        return await self.contract.functions.getNumAsksBackstop(asset).call()


    async def get_num_bids(self, asset: str) -> int:
        return await self.contract.functions.getNumBids(asset).call()


    async def get_num_bids_backstop(self, asset: str) -> int:
        return await self.contract.functions.getNumBidsBackstop(asset).call()


    async def get_open_interest(self, asset: str) -> tuple:
        return await self.contract.functions.getOpenInterest(asset).call()


    async def get_open_interest_backstop_book(self, asset: str) -> tuple:
        return await self.contract.functions.getOpenInterestBackstopBook(asset).call()


    async def get_open_interest_book(self, asset: str) -> tuple:
        return await self.contract.functions.getOpenInterestBook(asset).call()


    async def get_partial_liquidation_rate(self, asset: str) -> int:
        return await self.contract.functions.getPartialLiquidationRate(asset).call()


    async def get_partial_liquidation_threshold(self, asset: str) -> int:
        return await self.contract.functions.getPartialLiquidationThreshold(asset).call()


    async def get_position(self, asset: str, account: ChecksumAddress, subaccount: int) -> Position:
        tpl = await self.contract.functions.getPosition(asset, account, subaccount).call()
        return Position(
            is_long=tpl[0],
            amount=tpl[1],
            open_notional=tpl[2],
            margin=tpl[3],
            last_cumulative_funding=tpl[4],
        )

    async def get_positions(self, account: ChecksumAddress, subaccount: int) -> list:
        return await self.contract.functions.getPositions(account, subaccount).call()

    async def get_reduce_only_cap(self, asset: bytes) -> int:
        return await self.contract.functions.getReduceOnlyCap(asset).call()

    async def get_tick_size(self, asset: bytes) -> int:
        return await self.contract.functions.getTickSize(asset).call()

    async def get_traded_price_twap(self, asset: bytes, interval: int) -> int:
        return await self.contract.functions.getTradedPriceTwap(asset, interval).call()

    async def get_traded_price_vwap(self, asset: bytes, interval: int) -> int:
        return await self.contract.functions.getTradedPriceVwap(asset, interval).call()

    async def has_all_roles(self, user: ChecksumAddress, roles: int) -> bool:
        return await self.contract.functions.hasAllRoles(user, roles).call()

    async def has_any_role(self, user: ChecksumAddress, roles: int) -> bool:
        return await self.contract.functions.hasAnyRole(user, roles).call()

    async def is_cross_margin_enabled(self, asset: bytes) -> bool:
        return await self.contract.functions.isCrossMarginEnabled(asset).call()

    async def is_liquidatable(self, account: ChecksumAddress, subaccount: int) -> bool:
        return await self.contract.functions.isLiquidatable(account, subaccount).call()

    async def is_liquidatable_backstop(self, account: ChecksumAddress, subaccount: int) -> bool:
        return await self.contract.functions.isLiquidatableBackstop(account, subaccount).call()

    async def owner(self) -> ChecksumAddress:
        return await self.contract.functions.owner().call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        return await self.contract.functions.ownershipHandoverExpiresAt(pending_owner).call()

    async def roles_of(self, user: ChecksumAddress) -> int:
        return await self.contract.functions.rolesOf(user).call()


    # ================= WRITE METHODS =================


    def activate_market(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.activateMarket(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def activate_protocol(self, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.activateProtocol()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def amend_limit_order(self, account: ChecksumAddress, subaccount: int, args: dict, settlement: int, **kwargs) -> TypedContractFunction[int]:
        func = self.contract.functions.amendLimitOrder(account, subaccount, args, settlement)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def backstop_liquidate(self, account: ChecksumAddress, subaccount: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.backstopLiquidate(account, subaccount)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def cancel_limit_orders(self, asset: str, account: ChecksumAddress, subaccount: int, order_ids: list[int], settlement: int, **kwargs) -> TypedContractFunction[int]:
        func = self.contract.functions.cancelLimitOrders(asset, account, subaccount, order_ids, settlement)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def cancel_limit_orders_backstop(self, asset: str, account: ChecksumAddress, subaccount: int, order_ids: list[int], settlement: int, **kwargs) -> TypedContractFunction[int]:
        func = self.contract.functions.cancelLimitOrdersBackstop(asset, account, subaccount, order_ids, settlement)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.cancelOwnershipHandover()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def create_market(self, asset: str, params_struct: MarketConfig, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.createMarket(asset, params_struct)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def deactivate_market(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.deactivateMarket(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def deactivate_protocol(self, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.deactivateProtocol()
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def delist_market(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.delistMarket(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def deposit_collateral(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.depositCollateral(account, amount)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def disable_cross_margin(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.disableCrossMargin(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def enable_cross_margin(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.enableCrossMargin(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def grant_admin(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.grantAdmin(account)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def grant_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.grantRoles(user, roles)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def initialize(self, owner_: ChecksumAddress, taker_fees: list[int], maker_fees: list[int], **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.initialize(owner_, taker_fees, maker_fees)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def insurance_fund_deposit(self, amount: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.insuranceFundDeposit(amount)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def insurance_fund_withdraw(self, amount: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.insuranceFundWithdraw(amount)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def liquidate(self, account: ChecksumAddress, subaccount: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.liquidate(account, subaccount)
        params = {**kwargs}
        return TypedContractFunction(func, params)



    def post_fill_order(self, account: ChecksumAddress, args: PostFillOrderArgs, settlement: int, **kwargs) -> TypedContractFunction[dict]:
        func = self.contract.functions.postFillOrder(account, args, settlement)
        params = {**kwargs}
        return TypedContractFunction(func, params)



    def post_limit_order(self, account: ChecksumAddress, args: PostLimitOrderArgs, settlement: int, **kwargs) -> TypedContractFunction[dict]:
        func = self.contract.functions.postLimitOrder(account, args, settlement)
        params = {**kwargs}
        return TypedContractFunction(func, params)



    def post_limit_order_backstop(self, account: ChecksumAddress, args: PostLimitOrderArgs, settlement: int, **kwargs) -> TypedContractFunction[dict]:
        func = self.contract.functions.postLimitOrderBackstop(account, args, settlement)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def relist_market(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.relistMarket(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.renounceOwnership()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def renounce_roles(self, roles: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.renounceRoles(roles)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def request_ownership_handover(self, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.requestOwnershipHandover()
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def revoke_admin(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.revokeAdmin(account)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def revoke_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.revokeRoles(user, roles)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_divergence_cap(self, asset: str, divergence_cap: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setDivergenceCap(asset, divergence_cap)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def set_fee_tier(self, account: ChecksumAddress, fee_tier: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setFeeTier(account, fee_tier)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_funding_interval(self, asset: str, funding_interval: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setFundingInterval(asset, funding_interval)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_liquidation_fee_rate(self, asset: str, liquidation_fee_rate: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setLiquidationFeeRate(asset, liquidation_fee_rate)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def set_maker_fee_rates(self, maker_fee_rates: list, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMakerFeeRates(maker_fee_rates)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_mark_price(self, asset: str, mark_price: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMarkPrice(asset, mark_price)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_max_funding_rate(self, asset: str, max_funding_rate: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMaxFundingRate(asset, max_funding_rate)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_max_leverage(self, asset: str, max_open_leverage: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMaxLeverage(asset, max_open_leverage)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_max_limits_per_tx(self, asset: str, max_limits_per_tx: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMaxLimitsPerTx(asset, max_limits_per_tx)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_max_num_orders(self, asset: str, max_num_orders: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMaxNumOrders(asset, max_num_orders)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_min_limit_order_amount_in_base(self, asset: str, min_limit_order_amount_in_base: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setMinLimitOrderAmountInBase(asset, min_limit_order_amount_in_base)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_partial_liquidation_rate(self, asset: str, partial_liquidation_rate: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setPartialLiquidationRate(asset, partial_liquidation_rate)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_partial_liquidation_threshold(self, asset: str, partial_liquidation_threshold: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setPartialLiquidationThreshold(asset, partial_liquidation_threshold)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_reduce_only_cap(self, asset: str, reduce_only_cap: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setReduceOnlyCap(asset, reduce_only_cap)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def set_taker_fee_rates(self, taker_fee_rates: list, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setTakerFeeRates(taker_fee_rates)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def set_tick_size(self, asset: str, tick_size: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.setTickSize(asset, tick_size)
        params = {**kwargs}
        return TypedContractFunction(func, params)


    def settle_funding(self, asset: str, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.settleFunding(asset)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.transferOwnership(new_owner)
        params = {**kwargs}
        return TypedContractFunction(func, params)

    def withdraw_collateral(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[None]:
        func = self.contract.functions.withdrawCollateral(account, amount)
        params = {**kwargs}
        return TypedContractFunction(func, params)

