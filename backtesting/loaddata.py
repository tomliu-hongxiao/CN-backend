from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import *
import threading
import pandas as pd
import time


def tsla_contract():
    contract = Contract()
    contract.symbol = "TSLA"
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    return contract


class Bot(EClient, EWrapper):
    def __init__(self, symbol):
        EClient.__init__(self, self)

        self.symbol = symbol

        self.end_date_time = ""
        self.duration_str = "100 D"
        self.bar_size = "5 mins"
        self.bar_size_in_int = 1  # minute
        self.what_to_show = "TRADES"
        self.use_RTH = 0
        self.formatDate = 1
        self.keep_up_to_date = True
        self.chart_options = []

        self.previous_date = None
        self.current_date = None

        self.series = {"datetime": [], "open": [], "close": [], "high": [], "low": [], "volume": [], "openinterest":[]}

        # *************    连接 TWS     ***************#

        self.connect("127.0.0.1", 7497, 1)
        ib_thread = threading.Thread(target=self.run_loop, daemon=True)
        ib_thread.start()
        time.sleep(1)

        # *******************************************#

        # *************    订阅 数据    ***************#

        # request historical and live data
        self.reqHistoricalData(1, tsla_contract(), self.end_date_time, self.duration_str,
                               self.bar_size, self.what_to_show, self.use_RTH, self.formatDate,
                               self.keep_up_to_date, self.chart_options)

    def on_bar_update(self, reqId, bar, realtime):
        # historical data to catch up
        if not realtime:
            self.series['datetime'].append(bar.date[0:-3])
            self.series['open'].append(bar.open)
            self.series['close'].append(bar.close)
            self.series['high'].append(bar.high)
            self.series['low'].append(bar.low)
            self.series['volume'].append(bar.volume)
            self.series['openinterest'].append(None)

    def historicalData(self, reqId, bar):
        try:
            self.on_bar_update(reqId, bar, False)
        except Exception as e:
            print(e)

    def historicalDataEnd(self, reqId, start, end):
        self.store_data()
        print("Finish receiving historical data")

    def store_data(self):
        self.series = pd.DataFrame(self.series)
        file_name = "TSLA_IB_backtesting.csv"
        self.series.to_csv(file_name)

    def run_loop(self):
        try:
            self.run()
        except Exception as e:
            print(e)

    def error(self, id, errorCode, errorMsg):
        print(errorCode)
        print(errorMsg)



if __name__ == '__main__':
    bot = Bot("TSLA")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
