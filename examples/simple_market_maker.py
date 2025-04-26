import asyncio
import aiohttp
import numpy as np
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from web3 import Web3
from eth_typing import ChecksumAddress, HexStr
from gte_py import Client
from gte_py.config import TESTNET_CONFIG
from gte_py.models import OrderSide, TimeInForce, Market
from gte_py.contracts.erc20 import ERC20
from gte_py.contracts.iclob import ICLOB

# --- Config ---
BINANCE_BOOK_URL = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5"
ORDER_SIZE = 0.2  # BTC
UPDATE_INTERVAL = 0.0  # seconds
RISK_AVERSION = 0.05
VOL_EMA_ALPHA = 0.1
GBTC_CUSD_MARKET_ADDRESS = "0x0F3642714B9516e3d17a936bAced4de47A6FFa5F"
TARGET_SPREAD = 1.0

# Load environment variables for wallet
load_dotenv()
WALLET_ADDRESS_RAW = os.getenv("WALLET_ADDRESS")
WALLET_PRIVATE_KEY_RAW = os.getenv("WALLET_PRIVATE_KEY")

if not WALLET_ADDRESS_RAW or not WALLET_PRIVATE_KEY_RAW:
    raise ValueError("WALLET_ADDRESS and WALLET_PRIVATE_KEY must be set in your environment.")
WALLET_ADDRESS: ChecksumAddress = Web3.to_checksum_address(WALLET_ADDRESS_RAW)
WALLET_PRIVATE_KEY: HexStr = HexStr(WALLET_PRIVATE_KEY_RAW)

# --- Microprice Index ---
class MicropriceIndex:
    def __init__(self):
        self.last = None

    async def compute(self, session):
        async with session.get(BINANCE_BOOK_URL) as resp:
            data = await resp.json()
            bid = float(data['bids'][0][0])
            ask = float(data['asks'][0][0])
            micro = (bid + ask) / 2
            self.last = micro
            return micro

# --- EMA Volatility Estimator ---
class EMAEstimator:
    def __init__(self, alpha=VOL_EMA_ALPHA):
        self.alpha = alpha
        self.prev = None
        self.ema = 0.0

    def update(self, price):
        if self.prev is None:
            self.prev = price
            return self.ema
        ret = np.log(price / self.prev)
        self.ema = self.alpha * abs(ret) + (1 - self.alpha) * self.ema
        self.prev = price
        return self.ema

    def ema_vol(self, price):
        return self.update(price)

# --- Avellaneda-Stoikov Model ---
@dataclass
class Quotes:
    bid: float
    ask: float

class Stoikov:
    def __init__(
        self,
        risk_aversion: float = RISK_AVERSION,
        target_spread: float = TARGET_SPREAD,
    ):
        """
        risk_aversion – Avellaneda-Stoikov γ parameter  
        target_spread – desired *total* USD spread (ask-bid) we want to quote.
        """
        self.gamma = risk_aversion
        self.target_spread = target_spread

    def compute_quotes(self, microprice, sigma, inv=0, k=3):
        # Theoretical optimal spread suggested by Avellaneda-Stoikov
        theo_spread = self.gamma * sigma**2 / k

        # Keep the spread at least `target_spread` wide
        spread = max(theo_spread, self.target_spread)

        mid_adj = -inv * self.gamma * sigma**2
        bid = microprice + mid_adj - spread / 2
        ask = microprice + mid_adj + spread / 2
        return Quotes(bid=bid, ask=ask)

async def cancel_all_orders(client, market, open_orders, web3):
    for order_id in open_orders:
        try:
            tx_func = await client.cancel_order(market=market, order_id=order_id, gas=200000)
            tx_func.send_wait(WALLET_PRIVATE_KEY)
        except Exception as e:
            print(f"Cancel error for order {order_id}: {e}")
    open_orders.clear()

async def get_market_info(client, market_address) -> Market:
    """Get market information."""
    if not market_address:
        raise ValueError("No market address provided. Set MARKET_ADDRESS in .env file.")

    print(f"Using configured market: {market_address}")
    market = client.get_market(market_address)

    print(f"Market: {market.pair}")
    print(f"Base token: {market.base_asset.symbol} ({market.base_token_address})")
    print(f"Quote token: {market.quote_asset.symbol} ({market.quote_token_address})")
    print(f"Tick size: {market.tick_size} {market.tick_size_in_quote}")
    print(f"Lot size: {market.lot_size} {market.lot_size_in_base}")

    return market

async def main():
    network = TESTNET_CONFIG
    web3 = Web3(Web3.HTTPProvider(network.rpc_http))
    client = Client(web3=web3, config=network, sender_address=WALLET_ADDRESS)
    price_index = MicropriceIndex()
    estimator = EMAEstimator()
    stoikov = Stoikov()
    inv = 0  # Inventory, can be improved to track fills
    open_orders = []
    market = await get_market_info(client, GBTC_CUSD_MARKET_ADDRESS)
    print(f"Using market: {market.pair} ({market.address})")

    base_token = ERC20(web3, market.base_token_address)
    base_balance = base_token.balance_of(WALLET_ADDRESS)
    approve_tx = base_token.approve_max(TESTNET_CONFIG.clob_manager_address, WALLET_ADDRESS)
    approve_tx.send_wait(WALLET_PRIVATE_KEY)
    allowance = base_token.allowance(WALLET_ADDRESS, TESTNET_CONFIG.clob_manager_address)
    print(f"Base balance: {base_balance}")
    print(f"Base allowance: {allowance}")

  
    quote_token = ERC20(web3, market.quote_token_address)
    approve_tx = quote_token.approve_max(TESTNET_CONFIG.clob_manager_address, WALLET_ADDRESS)
    approve_tx.send_wait(WALLET_PRIVATE_KEY)
    quote_balance = quote_token.balance_of(WALLET_ADDRESS)
    allowance = quote_token.allowance(WALLET_ADDRESS, TESTNET_CONFIG.clob_manager_address)
    print(f"Quote balance: {quote_balance}")
    print(f"Quote allowance: {allowance}")

    clob = ICLOB(web3, GBTC_CUSD_MARKET_ADDRESS)

    print("\n========Starting Trades========\n")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # [max_bid, min_ask] = clob.get_tob()
                # book_spread = min_ask - max_bid
                microprice = await price_index.compute(session)
                sigma = estimator.ema_vol(microprice)
                quotes = stoikov.compute_quotes(microprice, sigma, inv=inv)

                # Cancel previous orders
                # await cancel_all_orders(client, market, open_orders, web3)

                # Place new buy order
                print(f"Placing buy order at price: {quotes.bid} and amount: {ORDER_SIZE}")
                buy_tx = await client.place_limit_order(
                    market=market,
                    side=OrderSide.BUY,
                    amount=ORDER_SIZE,
                    price=quotes.bid,
                    time_in_force=TimeInForce.GTC,
                )
                buy_tx.send(WALLET_PRIVATE_KEY)
                open_orders.append(None)  # Placeholder: order_id tracking requires API support

                # Place new sell order
                print(f"Placing sell order at price: {quotes.ask} and amount: {ORDER_SIZE}")
                sell_tx = await client.place_limit_order(
                    market=market,
                    side=OrderSide.SELL,
                    amount=ORDER_SIZE,
                    price=quotes.ask,
                    time_in_force=TimeInForce.GTC,
                )
                sell_tx.send(WALLET_PRIVATE_KEY)
                open_orders.append(None)  # Placeholder: order_id tracking requires API support

                print(f"Quotes: bid={quotes.bid:.2f}, ask={quotes.ask:.2f}, sigma={sigma:.6f}")
                # print("NOTE: To cancel specific orders, you must fetch order IDs from the API after placement.")
            except Exception as e:
                print(f"Error: {e}")
            await asyncio.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())