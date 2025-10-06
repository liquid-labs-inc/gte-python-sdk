# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import AmendLimitOrderArgsPerp, BookSettingsPerp, ConditionPerp, FundingRateSettingsPerp, MarketParamsPerp, MarketSettingsPerp, MerkleDataPerp, OrderPerp, OrderProcessedDataPerp, PlaceOrderArgsPerp, PlaceOrderResultPerp, PositionPerp, SignDataPerp, TwapOrderArgsPerp
from .events import BuilderCodeRegisteredPerpEvent, BuilderRevShareBpsUpdatedPerpEvent, CancelFailedPerpEvent, ConditionalCanceledPerpEvent, CrossMarginDisabledPerpEvent, CrossMarginEnabledPerpEvent, DepositPerpEvent, DivergenceCapUpdatedPerpEvent, FeeTierUpdatedPerpEvent, FundingClampsUpdatedPerpEvent, FundingIntervalUpdatedPerpEvent, FundingSettledPerpEvent, IndexFairClampUpdatedPerpEvent, InitializedPerpEvent, InsuranceFundDepositPerpEvent, InsuranceFundWithdrawalPerpEvent, InterestRateUpdatedPerpEvent, LiquidationFeeRateUpdatedPerpEvent, LiquidationPerpEvent, LiquidatorPointsSetPerpEvent, MaintenanceMarginRatioUpdatedPerpEvent, MakerFeeRatesUpdatedPerpEvent, MarginAddedPerpEvent, MarginRemovedPerpEvent, MarkPriceUpdatedPerpEvent, MarketCreatedPerpEvent, MarketStatusUpdatedPerpEvent, MaxLeverageUpdatedPerpEvent, MaxLimitsPerTxUpdatedPerpEvent, MaxNumOrdersUpdatedPerpEvent, MicroPriceClipBpsUpdatedPerpEvent, MinLimitOrderAmountInBaseUpdatedPerpEvent, OperatorApprovedPerpEvent, OperatorDisapprovedPerpEvent, OrderAmendedPerpEvent, OrderCanceledPerpEvent, OrderProcessedPerpEvent, OwnershipHandoverCanceledPerpEvent, OwnershipHandoverRequestedPerpEvent, OwnershipTransferredPerpEvent, PartialLiquidationRateUpdatedPerpEvent, PartialLiquidationThresholdUpdatedPerpEvent, PositionLeverageSetPerpEvent, ProtocolActivatedPerpEvent, ProtocolDeactivatedPerpEvent, ReduceOnlyCapUpdatedPerpEvent, RemoveExemptFromLimitPerTxCapPerpEvent, ResetIterationsUpdatedPerpEvent, RolesUpdatedPerpEvent, SetExemptFromLimitPerTxCapPerpEvent, TakerFeeRatesUpdatedPerpEvent, TickSizeUpdatedPerpEvent, TwapCanceledPerpEvent, WithdrawPerpEvent


class PerpManager:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("perp_manager")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    def activate_market(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.activateMarket(asset)
        return TypedContractFunction(func, params={**kwargs})

    def activate_protocol(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.activateProtocol()
        return TypedContractFunction(func, params={**kwargs})

    def add_margin(self, account: ChecksumAddress, subaccount: int, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.addMargin(account, subaccount, amount)
        return TypedContractFunction(func, params={**kwargs})

    def amend_limit_order(self, account: ChecksumAddress, args: AmendLimitOrderArgsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.amendLimitOrder(account, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def amend_limit_order_backstop(self, account: ChecksumAddress, args: AmendLimitOrderArgsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.amendLimitOrderBackstop(account, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def approve_operator(self, account: ChecksumAddress, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.approveOperator(account, operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    def backstop_liquidate(self, asset: HexBytes, account: ChecksumAddress, subaccount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.backstopLiquidate(asset, account, subaccount)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_conditional_orders(self, account: ChecksumAddress, nonces: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelConditionalOrders(account, nonces)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_limit_orders(self, asset: HexBytes, account: ChecksumAddress, subaccount: int, order_ids: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelLimitOrders(asset, account, subaccount, order_ids)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_limit_orders_backstop(self, asset: HexBytes, account: ChecksumAddress, subaccount: int, order_ids: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelLimitOrdersBackstop(asset, account, subaccount, order_ids)
        return TypedContractFunction(func, params={**kwargs})

    def cancel_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def cancel_twap_order(self, account: ChecksumAddress, root: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.cancelTwapOrder(account, root)
        return TypedContractFunction(func, params={**kwargs})

    def complete_ownership_handover(self, pending_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.completeOwnershipHandover(pending_owner)
        return TypedContractFunction(func, params={**kwargs})

    def create_market(self, asset: HexBytes, params: MarketParamsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.createMarket(asset, tuple(params))
        return TypedContractFunction(func, params={**kwargs})

    def deactivate_market(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.deactivateMarket(asset)
        return TypedContractFunction(func, params={**kwargs})

    def deactivate_protocol(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.deactivateProtocol()
        return TypedContractFunction(func, params={**kwargs})

    def deleverage(self, asset: HexBytes, pairs: list[Any], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.deleverage(asset, pairs)
        return TypedContractFunction(func, params={**kwargs})

    def delist_close(self, asset: HexBytes, accounts: list[Any], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.delistClose(asset, accounts)
        return TypedContractFunction(func, params={**kwargs})

    def delist_market(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.delistMarket(asset)
        return TypedContractFunction(func, params={**kwargs})

    def deposit(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.deposit(account, amount)
        return TypedContractFunction(func, params={**kwargs})

    def deposit_from_spot(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.depositFromSpot(account, amount)
        return TypedContractFunction(func, params={**kwargs})

    def deposit_to(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.depositTo(account, amount)
        return TypedContractFunction(func, params={**kwargs})

    def disable_cross_margin(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.disableCrossMargin(asset)
        return TypedContractFunction(func, params={**kwargs})

    def disapprove_operator(self, account: ChecksumAddress, operator: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.disapproveOperator(account, operator, roles)
        return TypedContractFunction(func, params={**kwargs})

    def enable_cross_margin(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.enableCrossMargin(asset)
        return TypedContractFunction(func, params={**kwargs})

    async def get_account_value(self, account: ChecksumAddress, subaccount: int) -> int:
        func = self.contract.functions.getAccountValue(account, subaccount)
        return await func.call()

    async def get_assets(self, account: ChecksumAddress, subaccount: int) -> list[HexBytes]:
        func = self.contract.functions.getAssets(account, subaccount)
        return await func.call()

    async def get_best_ask(self, asset: HexBytes) -> int:
        func = self.contract.functions.getBestAsk(asset)
        return await func.call()

    async def get_best_bid(self, asset: HexBytes) -> int:
        func = self.contract.functions.getBestBid(asset)
        return await func.call()

    async def get_builder_code_owner(self, builder_code: HexBytes) -> ChecksumAddress:
        func = self.contract.functions.getBuilderCodeOwner(builder_code)
        return await func.call()

    async def get_builder_rev_share_bps(self, asset: HexBytes) -> int:
        func = self.contract.functions.getBuilderRevShareBps(asset)
        return await func.call()

    async def get_collateral_asset(self) -> ChecksumAddress:
        func = self.contract.functions.getCollateralAsset()
        return await func.call()

    async def get_cumulative_funding(self, asset: HexBytes) -> int:
        func = self.contract.functions.getCumulativeFunding(asset)
        return await func.call()

    async def get_current_funding_interval(self, asset: HexBytes) -> int:
        func = self.contract.functions.getCurrentFundingInterval(asset)
        return await func.call()

    async def get_divergence_cap(self, asset: HexBytes) -> int:
        func = self.contract.functions.getDivergenceCap(asset)
        return await func.call()

    async def get_fee_tier(self, account: ChecksumAddress) -> int:
        func = self.contract.functions.getFeeTier(account)
        return await func.call()

    async def get_fee_tier_maker_rate(self, fee_tier: int) -> Any:
        func = self.contract.functions.getFeeTierMakerRate(fee_tier)
        return await func.call()

    async def get_fee_tier_taker_rate(self, fee_tier: int) -> Any:
        func = self.contract.functions.getFeeTierTakerRate(fee_tier)
        return await func.call()

    async def get_free_collateral_balance(self, account: ChecksumAddress) -> int:
        func = self.contract.functions.getFreeCollateralBalance(account)
        return await func.call()

    async def get_funding_clamps(self, asset: HexBytes) -> tuple[int, int]:
        """
        Returns:
            tuple: (inner_clamp, outer_clamp)
        """
        func = self.contract.functions.getFundingClamps(asset)
        return await func.call()

    async def get_funding_interval(self, asset: HexBytes) -> int:
        func = self.contract.functions.getFundingInterval(asset)
        return await func.call()

    async def get_funding_rate(self, asset: HexBytes) -> int:
        func = self.contract.functions.getFundingRate(asset)
        return await func.call()

    async def get_impact_ask(self, asset: HexBytes, impact_notional: int) -> int:
        func = self.contract.functions.getImpactAsk(asset, impact_notional)
        return await func.call()

    async def get_impact_bid(self, asset: HexBytes, impact_notional: int) -> int:
        func = self.contract.functions.getImpactBid(asset, impact_notional)
        return await func.call()

    async def get_impact_price(self, asset: HexBytes, impact_notional: int) -> int:
        func = self.contract.functions.getImpactPrice(asset, impact_notional)
        return await func.call()

    async def get_index_fair_clamp(self, asset: HexBytes) -> int:
        func = self.contract.functions.getIndexFairClamp(asset)
        return await func.call()

    async def get_index_price(self, asset: HexBytes) -> int:
        func = self.contract.functions.getIndexPrice(asset)
        return await func.call()

    async def get_insurance_fund_balance(self) -> int:
        func = self.contract.functions.getInsuranceFundBalance()
        return await func.call()

    async def get_intended_margin_and_upnl(self, asset: HexBytes, position: PositionPerp) -> tuple[int, int]:
        """
        Returns:
            tuple: (intended_margin, upnl)
        """
        func = self.contract.functions.getIntendedMarginAndUpnl(asset, tuple(position))
        return await func.call()

    async def get_interest_rate(self, asset: HexBytes) -> int:
        func = self.contract.functions.getInterestRate(asset)
        return await func.call()

    async def get_last_funding_time(self, asset: HexBytes) -> int:
        func = self.contract.functions.getLastFundingTime(asset)
        return await func.call()

    async def get_limit_order(self, asset: HexBytes, order_id: int) -> OrderPerp:
        func = self.contract.functions.getLimitOrder(asset, order_id)
        return await func.call()

    async def get_limit_order_backstop(self, asset: HexBytes, order_id: int) -> OrderPerp:
        func = self.contract.functions.getLimitOrderBackstop(asset, order_id)
        return await func.call()

    async def get_liquidation_fee_rate(self, asset: HexBytes) -> int:
        func = self.contract.functions.getLiquidationFeeRate(asset)
        return await func.call()

    async def get_liquidator_points(self, account: ChecksumAddress) -> int:
        func = self.contract.functions.getLiquidatorPoints(account)
        return await func.call()

    async def get_lot_size(self, asset: HexBytes) -> int:
        func = self.contract.functions.getLotSize(asset)
        return await func.call()

    async def get_maintenance_margin(self, asset: HexBytes, position_amount: int) -> int:
        func = self.contract.functions.getMaintenanceMargin(asset, position_amount)
        return await func.call()

    async def get_maker_fee_rates(self) -> int:
        func = self.contract.functions.getMakerFeeRates()
        return await func.call()

    async def get_margin_balance(self, account: ChecksumAddress, subaccount: int) -> int:
        func = self.contract.functions.getMarginBalance(account, subaccount)
        return await func.call()

    async def get_mark_price(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMarkPrice(asset)
        return await func.call()

    async def get_market_status(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMarketStatus(asset)
        return await func.call()

    async def get_max_leverage(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMaxLeverage(asset)
        return await func.call()

    async def get_max_limits_per_tx(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMaxLimitsPerTx(asset)
        return await func.call()

    async def get_max_num_orders(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMaxNumOrders(asset)
        return await func.call()

    async def get_micro_price_clip_bps(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMicroPriceClipBps(asset)
        return await func.call()

    async def get_min_limit_order_amount_in_base(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMinLimitOrderAmountInBase(asset)
        return await func.call()

    async def get_min_margin_ratio(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMinMarginRatio(asset)
        return await func.call()

    async def get_min_margin_ratio_backstop(self, asset: HexBytes) -> int:
        func = self.contract.functions.getMinMarginRatioBackstop(asset)
        return await func.call()

    async def get_next_empty_subaccount(self, account: ChecksumAddress) -> int:
        func = self.contract.functions.getNextEmptySubaccount(account)
        return await func.call()

    async def get_next_order_id(self, asset: HexBytes) -> int:
        func = self.contract.functions.getNextOrderId(asset)
        return await func.call()

    async def get_next_order_id_backstop(self, asset: HexBytes) -> int:
        func = self.contract.functions.getNextOrderIdBackstop(asset)
        return await func.call()

    async def get_nonce(self) -> int:
        func = self.contract.functions.getNonce()
        return await func.call()

    async def get_num_asks(self, asset: HexBytes) -> int:
        func = self.contract.functions.getNumAsks(asset)
        return await func.call()

    async def get_num_asks_backstop(self, asset: HexBytes) -> int:
        func = self.contract.functions.getNumAsksBackstop(asset)
        return await func.call()

    async def get_num_bids(self, asset: HexBytes) -> int:
        func = self.contract.functions.getNumBids(asset)
        return await func.call()

    async def get_num_bids_backstop(self, asset: HexBytes) -> int:
        func = self.contract.functions.getNumBidsBackstop(asset)
        return await func.call()

    async def get_open_interest(self, asset: HexBytes) -> tuple[int, int]:
        """
        Returns:
            tuple: (long_oi, short_oi)
        """
        func = self.contract.functions.getOpenInterest(asset)
        return await func.call()

    async def get_open_interest_backstop_book(self, asset: HexBytes) -> tuple[int, int]:
        """
        Returns:
            tuple: (base_oi, quote_oi)
        """
        func = self.contract.functions.getOpenInterestBackstopBook(asset)
        return await func.call()

    async def get_open_interest_book(self, asset: HexBytes) -> tuple[int, int]:
        """
        Returns:
            tuple: (base_oi, quote_oi)
        """
        func = self.contract.functions.getOpenInterestBook(asset)
        return await func.call()

    async def get_operator_event_nonce(self) -> int:
        func = self.contract.functions.getOperatorEventNonce()
        return await func.call()

    async def get_operator_role_approvals(self, account: ChecksumAddress, operator: ChecksumAddress) -> int:
        func = self.contract.functions.getOperatorRoleApprovals(account, operator)
        return await func.call()

    async def get_orderbook_collateral(self, account: ChecksumAddress, subaccount: int) -> int:
        func = self.contract.functions.getOrderbookCollateral(account, subaccount)
        return await func.call()

    async def get_orderbook_notional(self, asset: HexBytes, account: ChecksumAddress, subaccount: int) -> int:
        func = self.contract.functions.getOrderbookNotional(asset, account, subaccount)
        return await func.call()

    async def get_partial_liquidation_rate(self, asset: HexBytes) -> int:
        func = self.contract.functions.getPartialLiquidationRate(asset)
        return await func.call()

    async def get_partial_liquidation_threshold(self, asset: HexBytes) -> int:
        func = self.contract.functions.getPartialLiquidationThreshold(asset)
        return await func.call()

    async def get_pending_funding_payment(self, account: ChecksumAddress, subaccount: int) -> int:
        func = self.contract.functions.getPendingFundingPayment(account, subaccount)
        return await func.call()

    async def get_position(self, asset: HexBytes, account: ChecksumAddress, subaccount: int) -> PositionPerp:
        func = self.contract.functions.getPosition(asset, account, subaccount)
        return await func.call()

    async def get_position_leverage(self, asset: HexBytes, account: ChecksumAddress, subaccount: int) -> int:
        func = self.contract.functions.getPositionLeverage(asset, account, subaccount)
        return await func.call()

    async def get_reduce_only_cap(self, asset: HexBytes) -> int:
        func = self.contract.functions.getReduceOnlyCap(asset)
        return await func.call()

    async def get_reduce_only_orders(self, asset: HexBytes, account: ChecksumAddress, subaccount: int) -> list[int]:
        func = self.contract.functions.getReduceOnlyOrders(asset, account, subaccount)
        return await func.call()

    async def get_reset_interval(self, asset: HexBytes) -> int:
        func = self.contract.functions.getResetInterval(asset)
        return await func.call()

    async def get_reset_iterations(self, asset: HexBytes) -> int:
        func = self.contract.functions.getResetIterations(asset)
        return await func.call()

    async def get_taker_fee_rates(self) -> int:
        func = self.contract.functions.getTakerFeeRates()
        return await func.call()

    async def get_tick_size(self, asset: HexBytes) -> int:
        func = self.contract.functions.getTickSize(asset)
        return await func.call()

    def grant_admin(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantAdmin(account)
        return TypedContractFunction(func, params={**kwargs})

    def grant_backstop_liquidator(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantBackstopLiquidator(account)
        return TypedContractFunction(func, params={**kwargs})

    def grant_backstop_maker(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantBackstopMaker(account)
        return TypedContractFunction(func, params={**kwargs})

    def grant_exempt_from_max_limits(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantExemptFromMaxLimits(account)
        return TypedContractFunction(func, params={**kwargs})

    def grant_keeper(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantKeeper(account)
        return TypedContractFunction(func, params={**kwargs})

    def grant_liquidator(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantLiquidator(account)
        return TypedContractFunction(func, params={**kwargs})

    def grant_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.grantRoles(user, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def has_all_roles(self, user: ChecksumAddress, roles: int) -> bool:
        func = self.contract.functions.hasAllRoles(user, roles)
        return await func.call()

    async def has_any_role(self, user: ChecksumAddress, roles: int) -> bool:
        func = self.contract.functions.hasAnyRole(user, roles)
        return await func.call()

    def initialize(self, owner_: ChecksumAddress, taker_fees: list[Any], maker_fees: list[Any], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(owner_, taker_fees, maker_fees)
        return TypedContractFunction(func, params={**kwargs})

    def insurance_fund_deposit(self, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.insuranceFundDeposit(amount)
        return TypedContractFunction(func, params={**kwargs})

    def insurance_fund_withdraw(self, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.insuranceFundWithdraw(amount)
        return TypedContractFunction(func, params={**kwargs})

    async def is_admin(self, account: ChecksumAddress) -> bool:
        func = self.contract.functions.isAdmin(account)
        return await func.call()

    async def is_backstop_liquidator(self, account: ChecksumAddress) -> bool:
        func = self.contract.functions.isBackstopLiquidator(account)
        return await func.call()

    async def is_backstop_maker(self, account: ChecksumAddress) -> bool:
        func = self.contract.functions.isBackstopMaker(account)
        return await func.call()

    async def is_cross_margin_enabled(self, asset: HexBytes) -> bool:
        func = self.contract.functions.isCrossMarginEnabled(asset)
        return await func.call()

    async def is_keeper(self, account: ChecksumAddress) -> bool:
        func = self.contract.functions.isKeeper(account)
        return await func.call()

    async def is_leaf_used(self, account: ChecksumAddress, root: HexBytes, leaf: HexBytes) -> bool:
        func = self.contract.functions.isLeafUsed(account, root, leaf)
        return await func.call()

    async def is_liquidatable(self, account: ChecksumAddress, subaccount: int) -> bool:
        func = self.contract.functions.isLiquidatable(account, subaccount)
        return await func.call()

    async def is_liquidatable_backstop(self, account: ChecksumAddress, subaccount: int) -> bool:
        func = self.contract.functions.isLiquidatableBackstop(account, subaccount)
        return await func.call()

    async def is_liquidator(self, account: ChecksumAddress) -> bool:
        func = self.contract.functions.isLiquidator(account)
        return await func.call()

    async def is_root_canceled(self, account: ChecksumAddress, root: HexBytes) -> bool:
        func = self.contract.functions.isRootCanceled(account, root)
        return await func.call()

    def liquidate(self, asset: HexBytes, account: ChecksumAddress, subaccount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.liquidate(asset, account, subaccount)
        return TypedContractFunction(func, params={**kwargs})

    async def operator_hub(self) -> ChecksumAddress:
        func = self.contract.functions.operatorHub()
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def ownership_handover_expires_at(self, pending_owner: ChecksumAddress) -> int:
        func = self.contract.functions.ownershipHandoverExpiresAt(pending_owner)
        return await func.call()

    def place_order(self, account: ChecksumAddress, args: PlaceOrderArgsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.placeOrder(account, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def place_tpsl_order(self, account: ChecksumAddress, args: PlaceOrderArgsPerp, condition: ConditionPerp, sign_data: SignDataPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.placeTPSLOrder(account, tuple(args), tuple(condition), tuple(sign_data))
        return TypedContractFunction(func, params={**kwargs})

    def place_twap_order(self, args: TwapOrderArgsPerp, merkle_data: MerkleDataPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.placeTwapOrder(tuple(args), tuple(merkle_data))
        return TypedContractFunction(func, params={**kwargs})

    def post_limit_order_backstop(self, account: ChecksumAddress, args: PlaceOrderArgsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.postLimitOrderBackstop(account, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    async def quote_backstop_book_in_base(self, asset: HexBytes, base_amount: int, side: int) -> tuple[int, int]:
        """
        Returns:
            tuple: (quote_amount, base_used)
        """
        func = self.contract.functions.quoteBackstopBookInBase(asset, base_amount, side)
        return await func.call()

    async def quote_backstop_book_in_quote(self, asset: HexBytes, quote_amount: int, side: int) -> tuple[int, int]:
        """
        Returns:
            tuple: (base_amount, quote_used)
        """
        func = self.contract.functions.quoteBackstopBookInQuote(asset, quote_amount, side)
        return await func.call()

    async def quote_book_in_base(self, asset: HexBytes, base_amount: int, side: int) -> tuple[int, int]:
        """
        Returns:
            tuple: (quote_amount, base_used)
        """
        func = self.contract.functions.quoteBookInBase(asset, base_amount, side)
        return await func.call()

    async def quote_book_in_quote(self, asset: HexBytes, quote_amount: int, side: int) -> tuple[int, int]:
        """
        Returns:
            tuple: (base_amount, quote_used)
        """
        func = self.contract.functions.quoteBookInQuote(asset, quote_amount, side)
        return await func.call()

    def register_builder_code(self, account: ChecksumAddress, builder_code: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.registerBuilderCode(account, builder_code)
        return TypedContractFunction(func, params={**kwargs})

    def relist_market(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.relistMarket(asset)
        return TypedContractFunction(func, params={**kwargs})

    def remove_margin(self, account: ChecksumAddress, subaccount: int, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.removeMargin(account, subaccount, amount)
        return TypedContractFunction(func, params={**kwargs})

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceOwnership()
        return TypedContractFunction(func, params={**kwargs})

    def renounce_roles(self, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceRoles(roles)
        return TypedContractFunction(func, params={**kwargs})

    def request_ownership_handover(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.requestOwnershipHandover()
        return TypedContractFunction(func, params={**kwargs})

    def revoke_admin(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeAdmin(account)
        return TypedContractFunction(func, params={**kwargs})

    def revoke_backstop_liquidator(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeBackstopLiquidator(account)
        return TypedContractFunction(func, params={**kwargs})

    def revoke_backstop_maker(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeBackstopMaker(account)
        return TypedContractFunction(func, params={**kwargs})

    def revoke_exempt_from_max_limits(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeExemptFromMaxLimits(account)
        return TypedContractFunction(func, params={**kwargs})

    def revoke_keeper(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeKeeper(account)
        return TypedContractFunction(func, params={**kwargs})

    def revoke_liquidator(self, account: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeLiquidator(account)
        return TypedContractFunction(func, params={**kwargs})

    def revoke_roles(self, user: ChecksumAddress, roles: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.revokeRoles(user, roles)
        return TypedContractFunction(func, params={**kwargs})

    async def roles_of(self, user: ChecksumAddress) -> int:
        func = self.contract.functions.rolesOf(user)
        return await func.call()

    def set_book_settings(self, asset: HexBytes, settings: BookSettingsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setBookSettings(asset, tuple(settings))
        return TypedContractFunction(func, params={**kwargs})

    def set_builder_rev_share_bps(self, asset: HexBytes, builder_rev_share_bps: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setBuilderRevShareBps(asset, builder_rev_share_bps)
        return TypedContractFunction(func, params={**kwargs})

    def set_divergence_cap(self, asset: HexBytes, divergence_cap: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setDivergenceCap(asset, divergence_cap)
        return TypedContractFunction(func, params={**kwargs})

    def set_fee_tiers(self, accounts: list[ChecksumAddress], fee_tiers: list[int], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFeeTiers(accounts, fee_tiers)
        return TypedContractFunction(func, params={**kwargs})

    def set_funding_clamps(self, asset: HexBytes, inner_clamp: int, outer_clamp: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFundingClamps(asset, inner_clamp, outer_clamp)
        return TypedContractFunction(func, params={**kwargs})

    def set_funding_interval(self, asset: HexBytes, funding_interval: int, reset_interval: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFundingInterval(asset, funding_interval, reset_interval)
        return TypedContractFunction(func, params={**kwargs})

    def set_funding_rate_settings(self, asset: HexBytes, settings: FundingRateSettingsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setFundingRateSettings(asset, tuple(settings))
        return TypedContractFunction(func, params={**kwargs})

    def set_index_fair_clamp(self, asset: HexBytes, index_fair_clamp: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setIndexFairClamp(asset, index_fair_clamp)
        return TypedContractFunction(func, params={**kwargs})

    def set_interest_rate(self, asset: HexBytes, interest_rate: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setInterestRate(asset, interest_rate)
        return TypedContractFunction(func, params={**kwargs})

    def set_liquidation_fee_rate(self, asset: HexBytes, liquidation_fee_rate: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setLiquidationFeeRate(asset, liquidation_fee_rate)
        return TypedContractFunction(func, params={**kwargs})

    def set_liquidator_points(self, account: ChecksumAddress, points: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setLiquidatorPoints(account, points)
        return TypedContractFunction(func, params={**kwargs})

    def set_maker_fee_rates(self, maker_fee_rates: list[Any], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMakerFeeRates(maker_fee_rates)
        return TypedContractFunction(func, params={**kwargs})

    def set_mark_price(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMarkPrice(asset)
        return TypedContractFunction(func, params={**kwargs})

    def set_market_settings(self, asset: HexBytes, settings: MarketSettingsPerp, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMarketSettings(asset, tuple(settings))
        return TypedContractFunction(func, params={**kwargs})

    def set_max_leverage(self, asset: HexBytes, max_open_leverage: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMaxLeverage(asset, max_open_leverage)
        return TypedContractFunction(func, params={**kwargs})

    def set_max_limits_per_tx(self, asset: HexBytes, max_limits_per_tx: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMaxLimitsPerTx(asset, max_limits_per_tx)
        return TypedContractFunction(func, params={**kwargs})

    def set_max_num_orders(self, asset: HexBytes, max_num_orders: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMaxNumOrders(asset, max_num_orders)
        return TypedContractFunction(func, params={**kwargs})

    def set_micro_price_clip_bps(self, asset: HexBytes, micro_price_clip_bps: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMicroPriceClipBps(asset, micro_price_clip_bps)
        return TypedContractFunction(func, params={**kwargs})

    def set_min_limit_order_amount_in_base(self, asset: HexBytes, min_limit_order_amount_in_base: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMinLimitOrderAmountInBase(asset, min_limit_order_amount_in_base)
        return TypedContractFunction(func, params={**kwargs})

    def set_min_margin_ratio(self, asset: HexBytes, maintenance_margin_ratio: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMinMarginRatio(asset, maintenance_margin_ratio)
        return TypedContractFunction(func, params={**kwargs})

    def set_partial_liquidation_rate(self, asset: HexBytes, partial_liquidation_rate: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setPartialLiquidationRate(asset, partial_liquidation_rate)
        return TypedContractFunction(func, params={**kwargs})

    def set_partial_liquidation_threshold(self, asset: HexBytes, partial_liquidation_threshold: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setPartialLiquidationThreshold(asset, partial_liquidation_threshold)
        return TypedContractFunction(func, params={**kwargs})

    def set_position_leverage(self, asset: HexBytes, account: ChecksumAddress, subaccount: int, new_leverage: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setPositionLeverage(asset, account, subaccount, new_leverage)
        return TypedContractFunction(func, params={**kwargs})

    def set_reduce_only_cap(self, asset: HexBytes, reduce_only_cap: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setReduceOnlyCap(asset, reduce_only_cap)
        return TypedContractFunction(func, params={**kwargs})

    def set_reset_iterations(self, asset: HexBytes, reset_iterations: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setResetIterations(asset, reset_iterations)
        return TypedContractFunction(func, params={**kwargs})

    def set_taker_fee_rates(self, taker_fee_rates: list[Any], **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setTakerFeeRates(taker_fee_rates)
        return TypedContractFunction(func, params={**kwargs})

    def set_tick_size(self, asset: HexBytes, tick_size: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setTickSize(asset, tick_size)
        return TypedContractFunction(func, params={**kwargs})

    def settle_funding(self, asset: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.settleFunding(asset)
        return TypedContractFunction(func, params={**kwargs})

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})

    def unregister_builder_code(self, builder_code: HexBytes, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.unregisterBuilderCode(builder_code)
        return TypedContractFunction(func, params={**kwargs})

    def withdraw(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.withdraw(account, amount)
        return TypedContractFunction(func, params={**kwargs})

    def withdraw_to_spot(self, account: ChecksumAddress, amount: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.withdrawToSpot(account, amount)
        return TypedContractFunction(func, params={**kwargs})