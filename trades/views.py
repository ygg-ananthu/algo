
from accounts.models import User
import requests
import logging
from datetime import datetime
from accounts.auth import UpstoxAuth
import os
import django

import ssl
import asyncio
import websockets
import json
from google.protobuf.json_format import MessageToDict

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trading_bot.settings")
django.setup()


class OptionTradingBot:

    API_BASE_URL = "https://api.upstox.com/v2"
    OPTION_CHAIN_ENDPOINT = "/option/chain"
    ORDER_ENDPOINT = "https://api-hft.upstox.com/v2/order/place"
    INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"
    # as per requirement expiry day will be a friday
    EXPIRY_DATE = datetime.today().strftime('%Y-%m-%d')

    def __init__(self, user):
        self.user = user
        self.auth = UpstoxAuth(user)
        self.access_token = self.auth.get_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "accept": "application/json"
        }
        self.placed_trade = None
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")

    def fetch_option_chain(self):
        """Fetches the option chain data."""
        url = f"{self.API_BASE_URL}{self.OPTION_CHAIN_ENDPOINT}?instrument_key={self.INSTRUMENT_KEY}&expiry_date={self.EXPIRY_DATE}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            logging.error(f"Failed to fetch option chain: {response.text}")
            return []

    def get_market_data_feed_authorize_v3(self):
        """Get WebSocket authorization URL."""
        url = 'https://api.upstox.com/v3/feed/market-data-feed/authorize'
        response = requests.get(url=url, headers=self.headers)
        return response.json()

    def decode_protobuf(self, buffer):
        """Decode protobuf message."""
        import MarketDataFeed_pb2 as pb
        feed_response = pb.FeedResponse()
        feed_response.ParseFromString(buffer)
        return feed_response

    def calculate_pcr(self, options_data):
        """Calculates the Put-Call Ratio (PCR)."""
        total_call_oi = sum(item["call_options"]["market_data"]["oi"]
                            for item in options_data)
        total_put_oi = sum(item["put_options"]["market_data"]["oi"]
                           for item in options_data)
        pcr = total_put_oi / \
            total_call_oi if total_call_oi > 0 else float('inf')
        logging.info(f"Put-Call Ratio (PCR): {pcr:.2f}")
        return pcr

    def find_best_option(self, options_data, pcr):
        """Finds the best option to sell based on delta condition."""
        target_delta = -0.12 if pcr < 1 else 0.12
        best_option = None
        min_delta_diff = float("inf")

        for item in options_data:
            option = item["put_options"] if pcr < 1 else item["call_options"]
            delta = option["option_greeks"]["delta"]

            if delta <= target_delta:  # Find the nearest or just lower delta
                delta_diff = abs(target_delta - delta)
                if delta_diff < min_delta_diff:
                    min_delta_diff = delta_diff
                    best_option = option

        if best_option:
            logging.info(
                f"Selected Option: {best_option['instrument_key']} (Delta: {best_option['option_greeks']['delta']})")
            return best_option

        else:
            logging.warning("No suitable option found for trading.")
        return best_option

    async def track_live_prices(self):
        """Monitor LTP updates of the traded stock and check for exit conditions."""
        if not self.placed_trade:
            logging.warning("No trade placed, skipping WebSocket monitoring.")
            return

        stock_symbol = self.placed_trade["instrument_key"]
        target_price = self.placed_trade["target"]
        stop_loss = self.placed_trade["stop_loss"]

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Get WebSocket authorization
        response = self.get_market_data_feed_authorize_v3()
        async with websockets.connect(response["data"]["authorized_redirect_uri"], ssl=ssl_context) as websocket:
            logging.info("WebSocket Connection established.")

            data = {
                "guid": "someguid",
                "method": "sub",
                "data": {
                    "mode": "ltpc",
                    "instrumentKeys": [stock_symbol]
                }
            }
            await websocket.send(json.dumps(data).encode('utf-8'))

            while True:
                message = await websocket.recv()
                decoded_data = self.decode_protobuf(message)
                data_dict = MessageToDict(decoded_data)
                print(data_dict)
                # Extract LTP from WebSocket data
                try:
                    ltp = data_dict["feeds"][stock_symbol]["ltpc"]['ltp']
                    logging.info(f"Live LTP for {stock_symbol}: {ltp}")

                    # Check for exit conditions
                    if ltp <= target_price:
                        logging.info("Target price reached. Exiting trade.")

                        # update balance
                        amount = ltp*75
                        self.user.update_balance(amount, 'INCREASE')
                        self.exit_trade(ltp, stock_symbol)
                        break
                    elif ltp >= stop_loss:
                        logging.info("Stop-loss hit. Exiting trade.")
                        self.user.update_balance(amount, 'INCREASE')
                        self.exit_trade(ltp, stock_symbol)
                        break
                except KeyError:
                    logging.warning("Unexpected WebSocket response format.")

    def exit_trade(self, entry, instrument_key):
        """Exit the trade when target/stop-loss is hit."""
        self.place_order(entry, instrument_key, 'BUY')
        logging.info("Exiting the trade...")

    def place_order(self, entry, instrument_key, type):
        order_payload = {
            "quantity": 1,
            "product": "D",
            "validity": "DAY",
            "price": entry,
            "tag": "string",
            "instrument_token": instrument_key,
            "order_type": "MARKET",
            "transaction_type": type,
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }
        url = self.ORDER_ENDPOINT
        response = requests.post(url, json=order_payload, headers=self.headers)

        return response

    def place__sell_order(self, instrument_key="NSE_INDEX|Nifty 50", entry=0, target=0, stop_loss=0):
        """Places a sell order for the selected option."""

        response = self.place_order(entry, instrument_key, type='SELL')

        if response.status_code == 200:

            # update the balance
            trade_amount = entry*75
            self.user.update_balance(trade_amount, 'DECREASE')

            self.placed_trade = {
                "instrument_key": instrument_key,
                "entry": entry,
                "target": target,
                "stop_loss": stop_loss
            }
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(self.track_live_prices())  # Non-blocking

            logging.info(f"Order placed successfully: {response.json()}")
        else:
            logging.error(f"Failed to place order: {response.text}")

    def execute_strategy(self):
        """Main function to execute the trading strategy."""
        options_data = self.fetch_option_chain()
        if not options_data:
            logging.error("No options data available.")
            return

        pcr = self.calculate_pcr(options_data)
        best_option = self.find_best_option(options_data, pcr)

        if best_option:
            entry = best_option["market_data"]["ltp"]
            target = 1
            stop_loss = entry*4
            if self.user.virtual_balance < entry*75:  # 75 is the lot size
                logging.warning("Skipping order due to low balance")
                return
            if entry > 0:
                self.place__sell_order(
                    best_option["instrument_key"], entry, target, stop_loss)
                logging.info("Order placed ")
            else:
                logging.warning("Skipping order placement due to zero LTP.")
        else:
            logging.warning("No trade executed due to missing option.")
