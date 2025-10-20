# This file is auto-generated. Do not edit manually.
from typing import Any
from .utils import TypedContractFunction, load_abi
from eth_typing import ChecksumAddress
from web3 import AsyncWeb3
from hexbytes import HexBytes
from .structs import AmendArgs, Limit, MarketConfig, MarketSettings, Order, OrderProcessedData, PlaceOrderArgs, PlaceOrderResult
from .events import BuilderRevShareBpsUpdatedEvent, CancelFailedEvent, InitializedEvent, LotSizeInBaseUpdatedEvent, MaxLimitOrdersPerTxUpdatedEvent, MinLimitOrderAmountInBaseUpdatedEvent, OrderAmendedEvent, OrderCanceledEvent, OrderProcessedEvent, OwnershipTransferStartedEvent, OwnershipTransferredEvent, TickSizeUpdatedEvent


class Clob:
    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):
        self.web3 = web3
        self.address = address
        loaded_abi = load_abi("clob")
        self.contract = web3.eth.contract(address=address, abi=loaded_abi)

    async def abi_version(self) -> int:
        func = self.contract.functions.ABI_VERSION()
        return await func.call()

    def accept_ownership(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.acceptOwnership()
        return TypedContractFunction(func, params={**kwargs})

    async def account_manager(self) -> ChecksumAddress:
        func = self.contract.functions.accountManager()
        return await func.call()

    def admin_cancel_expired_orders(self, ids: list[int], side: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.adminCancelExpiredOrders(ids, side)
        return TypedContractFunction(func, params={**kwargs})

    def amend(self, account: ChecksumAddress, args: AmendArgs, **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (quote_delta, base_delta)
        """
        func = self.contract.functions.amend(account, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def cancel(self, account: ChecksumAddress, order_or_client_ids: list[int], **kwargs) -> TypedContractFunction[Any]:
        """
        Returns:
            TypedContractFunction that returns tuple: (cancel_result0, cancel_result1)
        """
        func = self.contract.functions.cancel(account, order_or_client_ids)
        return TypedContractFunction(func, params={**kwargs})

    async def factory(self) -> ChecksumAddress:
        func = self.contract.functions.factory()
        return await func.call()

    async def get_base_quanta(self) -> int:
        func = self.contract.functions.getBaseQuanta()
        return await func.call()

    async def get_base_token(self) -> ChecksumAddress:
        func = self.contract.functions.getBaseToken()
        return await func.call()

    async def get_base_token_amount(self, price: int, quote_amount: int) -> int:
        func = self.contract.functions.getBaseTokenAmount(price, quote_amount)
        return await func.call()

    async def get_event_nonce(self) -> int:
        func = self.contract.functions.getEventNonce()
        return await func.call()

    async def get_limit(self, price: int, side: int) -> Limit:
        func = self.contract.functions.getLimit(price, side)
        return await func.call()

    async def get_lot_size_in_base(self) -> int:
        func = self.contract.functions.getLotSizeInBase()
        return await func.call()

    async def get_market_config(self) -> MarketConfig:
        func = self.contract.functions.getMarketConfig()
        return await func.call()

    async def get_market_settings(self) -> MarketSettings:
        func = self.contract.functions.getMarketSettings()
        return await func.call()

    async def get_next_biggest_price(self, price: int, side: int) -> int:
        func = self.contract.functions.getNextBiggestPrice(price, side)
        return await func.call()

    async def get_next_order_id(self) -> int:
        func = self.contract.functions.getNextOrderId()
        return await func.call()

    async def get_next_orders(self, start_order_id: int, num_orders: int) -> list[Any]:
        func = self.contract.functions.getNextOrders(start_order_id, num_orders)
        return await func.call()

    async def get_next_smallest_price(self, price: int, side: int) -> int:
        func = self.contract.functions.getNextSmallestPrice(price, side)
        return await func.call()

    async def get_num_asks(self) -> int:
        func = self.contract.functions.getNumAsks()
        return await func.call()

    async def get_num_bids(self) -> int:
        func = self.contract.functions.getNumBids()
        return await func.call()

    async def get_open_interest(self) -> tuple[int, int]:
        """
        Returns:
            tuple: (quote_oi, base_oi)
        """
        func = self.contract.functions.getOpenInterest()
        return await func.call()

    async def get_order(self, order_id: int) -> Order:
        func = self.contract.functions.getOrder(order_id)
        return await func.call()

    async def get_order_id_by_client_id(self, client_order_id: int) -> int:
        func = self.contract.functions.getOrderIdByClientId(client_order_id)
        return await func.call()

    async def get_orders_paginated_(self, start_order_id: int, page_size: int) -> tuple[Any, Order]:
        """
        Returns:
            tuple: (result, next_order)
        """
        func = self.contract.functions.getOrdersPaginated(start_order_id, page_size)
        return await func.call()

    async def get_orders_paginated(self, start_price: int, side: int, page_size: int) -> tuple[Any, Order]:
        """
        Returns:
            tuple: (result, next_order)
        """
        func = self.contract.functions.getOrdersPaginated(start_price, side, page_size)
        return await func.call()

    async def get_quote_token(self) -> ChecksumAddress:
        func = self.contract.functions.getQuoteToken()
        return await func.call()

    async def get_quote_token_amount(self, price: int, base_amount: int) -> int:
        func = self.contract.functions.getQuoteTokenAmount(price, base_amount)
        return await func.call()

    async def get_tob(self) -> tuple[int, int]:
        """
        Returns:
            tuple: (max_bid, min_ask)
        """
        func = self.contract.functions.getTOB()
        return await func.call()

    async def get_tick_size(self) -> int:
        func = self.contract.functions.getTickSize()
        return await func.call()

    async def gte_router(self) -> ChecksumAddress:
        func = self.contract.functions.gteRouter()
        return await func.call()

    def initialize(self, market_config: MarketConfig, market_settings: MarketSettings, initial_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.initialize(tuple(market_config), tuple(market_settings), initial_owner)
        return TypedContractFunction(func, params={**kwargs})

    async def max_num_orders_per_side(self) -> int:
        func = self.contract.functions.maxNumOrdersPerSide()
        return await func.call()

    async def owner(self) -> ChecksumAddress:
        func = self.contract.functions.owner()
        return await func.call()

    async def pending_owner(self) -> ChecksumAddress:
        func = self.contract.functions.pendingOwner()
        return await func.call()

    def place_order(self, account: ChecksumAddress, args: PlaceOrderArgs, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.placeOrder(account, tuple(args))
        return TypedContractFunction(func, params={**kwargs})

    def renounce_ownership(self, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.renounceOwnership()
        return TypedContractFunction(func, params={**kwargs})

    def set_builder_rev_share_bps(self, new_builder_rev_share_bps: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setBuilderRevShareBps(new_builder_rev_share_bps)
        return TypedContractFunction(func, params={**kwargs})

    def set_lot_size_in_base(self, new_lot_size_in_base: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setLotSizeInBase(new_lot_size_in_base)
        return TypedContractFunction(func, params={**kwargs})

    def set_max_limits_per_tx(self, new_max_limits: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMaxLimitsPerTx(new_max_limits)
        return TypedContractFunction(func, params={**kwargs})

    def set_min_limit_order_amount_in_base(self, new_min_limit_order_amount_in_base: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setMinLimitOrderAmountInBase(new_min_limit_order_amount_in_base)
        return TypedContractFunction(func, params={**kwargs})

    def set_tick_size(self, tick_size: int, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.setTickSize(tick_size)
        return TypedContractFunction(func, params={**kwargs})

    def transfer_ownership(self, new_owner: ChecksumAddress, **kwargs) -> TypedContractFunction[Any]:
        func = self.contract.functions.transferOwnership(new_owner)
        return TypedContractFunction(func, params={**kwargs})