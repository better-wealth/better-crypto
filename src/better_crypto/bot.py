import decimal
import json
import math
import statistics
import sys
import time
from datetime import datetime
from datetime import timedelta

import pandas as pd

import requests
from creds import API_KEY_CREDENTIALS
from creds import BASE_ASSETS
from creds import CANDLE_RESOLUTION
from creds import ETHEREUM_ADDRESS
from creds import INFURA_API_KEY
from creds import QUOTATION_ASSET
from creds import STARK_PRIVATE_KEY
from creds import WEB3_HOST
from dydx3 import Client
from dydx3.constants import API_HOST_MAINNET
from dydx3.constants import MARKET_ETH_USD
from dydx3.constants import NETWORK_ID_MAINNET
from dydx3.constants import ORDER_SIDE_BUY
from dydx3.constants import ORDER_SIDE_SELL
from dydx3.constants import ORDER_STATUS_OPEN
from dydx3.constants import ORDER_TYPE_LIMIT
from dydx3.constants import POSITION_STATUS_OPEN
from web3 import Web3


class Bot:
    """Generate a class for the bot."""

    def __init__(
        self,
        num_samples=20,
        num_std=3,
        take_profit_multiplier=1.001,
        stop_loss_multiplier=0.98,
        records_fname="records",
    ):
        self.total_mins = 525600
        self.pages = math.ceil(self.total_mins / 100)
        self.client = Client(
            network_id=NETWORK_ID_MAINNET,
            host=API_HOST_MAINNET,
            web3=Web3(Web3.HTTPProvider(WEB3_HOST + INFURA_API_KEY)),
            default_ethereum_address=ETHEREUM_ADDRESS,
            stark_private_key=STARK_PRIVATE_KEY,
            api_key_credentials=API_KEY_CREDENTIALS,
        )
        self.start_time = self.client.public.get_time()
        self.start_time_iso = datetime.strptime(
            self.start_time.data["iso"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.windows = [
            self.start_time_iso - timedelta(minutes=page * 100)
            for page in range(self.pages)
        ]
        self.coinbase_api = "https://api.pro.coinbase.com"
        self.market = None
        self.num_samples = num_samples
        self.num_std = num_std
        self.take_profit_multiplier = take_profit_multiplier
        self.stop_loss_multiplier = stop_loss_multiplier
        self.records_fname = records_fname
        self.data = pd.concat(
            [
                pd.DataFrame(
                    self.client.public.get_candles(
                        market=MARKET_ETH_USD,
                        resolution=CANDLE_RESOLUTION,
                        to_iso=window,
                        limit=100,
                    ).data["candles"]
                )
                for window in self.windows
            ],
            ignore_index=True,
        )
        self.df = pd.DataFrame(self.data)
        self.price_history = []
        self.mean_price = None
        self.mean_std = None
        self.market_info = {}
        self.orderbook = {}
        self.account = {}
        self.positions = {}
        self.buy_orders = []
        self.sell_orders = []
        self.account = self.get_account()
        self.positions = self.account["openPositions"]

    def get_account(self):
        account = self.client.private.get_account()
        if account.data:
            return account.data["account"]
        print("ERROR: NO ACCOUNT DATA... EXITING")
        sys.exit(1)

    def load_all_histories(self):
        with open(f"{self.histories_fname}.json") as f:
            histories = json.load(f)
        return histories

    def load_market_history(self):
        histories = self.load_all_histories()
        return histories[self.market] if histories.get(self.market) else []

    def save_market_history(self, data):
        histories = self.load_all_histories()
        histories[self.market] = data
        with open(f"{self.histories_fname}.json", "w") as f:
            json.dump(histories, f)

    def get_price_history(self):
        endpoint = f"/products/{self.market}/candles"
        r = requests.get(self.coinbase_api + endpoint, timeout=5)
        data = r.json()[: self.num_samples][::-1]
        self.price_history = [float(x[4]) for x in data]

    def calculate_price_stats(self):
        self.mean_price = statistics.mean(self.price_history)
        self.mean_std = statistics.stdev(self.price_history)

    def get_entry_signal(self, price):
        return price < self.mean_price - self.num_std * self.mean_std

    def get_take_profit_signal(self, entry_price, price):
        return entry_price * self.take_profit_multiplier < price

    def get_stop_signal(self, entry_price, price):
        return price < entry_price * self.stop_loss_multiplier

    def get_market_info(self):
        r = self.client.public.get_markets(self.market)
        self.market_info = r["markets"][self.market]

    def get_orderbook(self):
        self.orderbook = self.client.public.get_orderbook(market=self.market)

    def get_buy_orders(self):
        orders = self.client.private.get_orders(
            market=self.market,
            status=ORDER_STATUS_OPEN,
            side=ORDER_SIDE_BUY,
            limit=1,
        )
        self.buy_orders = orders["orders"]

    def get_sell_orders(self):
        orders = self.client.private.get_orders(
            market=self.market,
            status=ORDER_STATUS_OPEN,
            side=ORDER_SIDE_SELL,
            limit=1,
        )
        self.sell_orders = orders["orders"]

    def get_positions(self):
        positions = self.client.private.get_positions(
            market=self.market, status=POSITION_STATUS_OPEN
        )["positions"]
        self.positions = {
            "long": [x for x in positions if x["side"] == "LONG"],
            "short": [x for x in positions if x["side"] == "SHORT"],
        }

    def calculate_mid_market_price(self):
        bid_price = float(self.orderbook["bids"][0]["price"])
        ask_price = float(self.orderbook["asks"][0]["price"])
        return bid_price + (ask_price - bid_price) * 0.5

    """
    STRATEGIES
    """

    def run_meanreversion_strategy(self):
        for market in [f"{b}-{QUOTATION_ASSET}" for b in BASE_ASSETS]:
            self.market = market
            self.get_market_info()
            self.get_price_history()
            self.calculate_price_stats()
            self.get_orderbook()
            self.get_buy_orders()
            self.get_sell_orders()
            self.get_positions()

            step_size = self.market_info["stepSize"]
            step_exp = abs(decimal.Decimal(step_size).as_tuple().exponent)

            buy_orders = self.client.private.get_orders(
                market=market,
                status=ORDER_STATUS_OPEN,
                side=ORDER_SIDE_BUY,
                order_type=ORDER_TYPE_LIMIT,
                limit=1,
            )
            buy_order = (
                buy_orders["orders"][0] if buy_orders["orders"] else None
            )

            sell_orders = self.client.private.get_orders(
                market=market,
                status=ORDER_STATUS_OPEN,
                side=ORDER_SIDE_SELL,
                order_type=ORDER_TYPE_LIMIT,
                limit=1,
            )
            sell_order = (
                sell_orders["orders"][0] if sell_orders["orders"] else None
            )

            if not self.positions["long"]:
                price = self.orderbook["bids"][0]["price"]
                if self.get_entry_signal(float(price)) and not buy_order:
                    equity = float(self.account["equity"])
                    size = min(equity, 10000)
                    size = size / float(self.market_info["indexPrice"])
                    size = round(size - size % float(step_size), step_exp)
                    size = str(
                        max(size, float(self.market_info["minOrderSize"]))
                    )
                    order_params = {
                        "position_id": self.account["positionId"],
                        "market": market,
                        "side": ORDER_SIDE_BUY,
                        "order_type": ORDER_TYPE_LIMIT,
                        "post_only": True,
                        "size": size,
                        "price": price,
                        "limit_fee": "0.0005",
                        "expiration_epoch_seconds": time.time() + 3600,
                    }
                    self.client.private.create_order(**order_params)

            else:
                entry_price = float(self.positions["long"][0]["entryPrice"])
                price = self.orderbook["asks"][0]["price"]
                size = self.positions["long"][0]["sumOpen"]
                order_params = {
                    "position_id": self.account["positionId"],
                    "market": market,
                    "side": ORDER_SIDE_SELL,
                    "order_type": ORDER_TYPE_LIMIT,
                    "post_only": True,
                    "size": size,
                    "price": price,
                    "limit_fee": "0.0005",
                    "expiration_epoch_seconds": time.time() + 3600,
                }
                if float(size) < float(self.market_info["minOrderSize"]):
                    order_params |= {
                        "side": ORDER_SIDE_BUY,
                        "size": self.market_info["minOrderSize"],
                        "price": self.orderbook["bids"][0]["price"],
                    }

                    if buy_order:
                        order_params["cancel_id"] = buy_order["id"]
                    self.client.private.create_order(**order_params)
                elif self.get_take_profit_signal(entry_price, float(price)):
                    if not sell_order:
                        self.client.private.create_order(**order_params)
                if self.get_stop_signal(entry_price, float(price)):
                    if buy_order:
                        self.client.private.cancel_order(
                            order_id=buy_order["id"]
                        )
                    if sell_order:
                        self.client.private.cancel_order(
                            order_id=sell_order["id"]
                        )
                    order_params = {
                        "position_id": self.account["positionId"],
                        "market": market,
                        "side": ORDER_SIDE_SELL,
                        "order_type": "MARKET",
                        "post_only": False,
                        "size": size,
                        "price": str(self.orderbook["bids"][10]["price"]),
                        "limit_fee": "0.002",
                        "time_in_force": "FOK",
                        "expiration_epoch_seconds": time.time() + 3600,
                    }
                    self.client.private.create_order(**order_params)


if __name__ == "__main__":
    bot = Bot()
    print(bot.data)
