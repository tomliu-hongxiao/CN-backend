import datetime
import pandas as pd
import backtrader as bt

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from strategy.tsla.trend import TSLATrend
from strategy.futu.trend import FUTUTrend


# ********************************************************************************** #

trade_list = {"tradeId": [], "type1": [], "datetime1": [], "price1": [], "type2": [], "datetime2": [], "price2": [],
              "quantity": [], "profit": [], "entryBarIndex": [], "exitBarIndex": []}

performance_summary = {"netProfit": 0, "netProfitPercentage": 0.0, "longProfit": 0, "longProfitPercentage": 0.0,
                       "shortProfit": 0, "shortProfitPercentage": 0.0, "maxGain": 0.0, "maxLoss": 0.0,
                       "maxGainShort": 0.0, "maxGainLong": 0.0, "maxLossShort": 0.0, 'maxLossLong': 0.0,
                       "totalTrades": 0, "totalShortTrades": 0, "totalLongTrades": 0, 'equity': [], 'short_equity': [],
                       'long_equity': []}

# ********************************************************************************** #

series = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

symbol = None

# Create a Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        da = dt or self.datas[0].datetime.date(0)
        dt = dt or self.datas[0].datetime.time(0)

    #         print('%s, %s, %s' % (da.isoformat(), dt.isoformat(), txt))

    def __init__(self):
        self.original_cash = 10000
        self.net_cash = 10000
        self.short_in_cash = 0
        self.long_in_cash = 0

        self.position_size = 0
        self.trend = None

        if symbol == "TSLA":
            self.trend = TSLATrend()
        elif symbol == "FUTU":
            self.trend = FUTUTrend()

        self.short_position = False
        self.long_position = False

        self.tradeId = 1
        self.bar_number = 0

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        self.datadatetime = self.datas[0].datetime

        self.series = None

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                if self.long_position:
                    trade_list['price1'].append(order.executed.price)
                    trade_list["datetime1"].append(self.datas[0].datetime.datetime().strftime("%Y%m%d, %H:%M:%S"))
                else:
                    trade_list['price2'].append(order.executed.price)
                    trade_list["datetime2"].append(self.datas[0].datetime.datetime().strftime("%Y%m%d, %H:%M:%S"))
                    trade_list["profit"].append(round((trade_list["price1"][-1] - trade_list["price2"][-1]) * self.position_size,2))

            elif order.issell():
                if self.short_position:
                    trade_list['price1'].append(order.executed.price)
                    trade_list["datetime1"].append(self.datas[0].datetime.datetime().strftime("%Y%m%d, %H:%M:%S"))
                else:
                    trade_list['price2'].append(order.executed.price)
                    trade_list["datetime2"].append(self.datas[0].datetime.datetime().strftime("%Y%m%d, %H:%M:%S"))
                    trade_list["profit"].append(round((trade_list["price2"][-1] - trade_list["price1"][-1]) * self.position_size,2))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.bar_number += 1

        series['date'].append(self.datas[0].datetime.time().strftime("%H:%M:%S"))
        series['close'].append(self.dataclose[0])
        series['open'].append(self.dataopen[0])
        series['high'].append(self.datahigh[0])
        series['low'].append(self.datalow[0])
        series['volume'].append(self.datavolume[0])
        self.series = pd.DataFrame(series)

        if len(self.series) > 250:

            if self.datas[0].datetime.time().strftime("%H:%M:%S") == "09:25:00":
                self.trend.reset()
            self.trend.update_trend(self.series)

            if self.datas[0].datetime.datetime().strftime("%Y-%m-%d, %H:%M:%S") == "2021-04-29, 12:25:00":
                print(self.trend.short_in.get_a())

            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.order:
                return

            # Check if we are in the market
            if not self.position:

                if self.trend.is_trade_short_in():
                    self.position_size = int(self.net_cash / self.dataclose[0])
                    self.net_cash = self.net_cash + (self.position_size * self.dataclose[0])
                    print("SELL net cash: ", self.net_cash, ", SELL quantity: ", self.position_size)
                    self.order = self.sell()
                    self.trend.clean_short_in_values()
                    self.trend.record_short_in_values(self.series)
                    self.short_position = True

                    # record trade list
                    trade_list['tradeId'].append(self.tradeId)
                    trade_list['type1'].append("Entry Short")
                    trade_list['quantity'].append(self.position_size)
                    trade_list['entryBarIndex'].append(self.bar_number)

                elif self.trend.is_trade_long_in():
                    self.position_size = int(self.net_cash / self.dataclose[0])
                    self.net_cash = self.net_cash - (self.position_size * self.dataclose[0])
                    print("BUY net cash : ", self.net_cash, self.position_size)
                    self.order = self.buy()
                    self.trend.clean_long_in_values()
                    self.trend.record_long_in_values(self.series)
                    self.long_position = True

                    # record trade list
                    trade_list['tradeId'].append(self.tradeId)
                    trade_list['type1'].append("Entry Long")
                    trade_list['quantity'].append(self.position_size)
                    trade_list['entryBarIndex'].append(self.bar_number)

            else:

                # Already in the market ... we might sell
                if self.short_position and self.trend.is_trade_short_out():
                    self.net_cash = self.net_cash - (self.position_size * self.dataclose[0]) - 2
                    print("BUY net cash: ", self.net_cash, ", BUY quantity: ", self.position_size)
                    self.order = self.buy()
                    self.trend.clean_short_out_values()
                    self.trend.record_short_out_values(self.series)
                    self.short_position = False

                    # record trade list
                    trade_list['type2'].append("Exit Short")
                    trade_list['exitBarIndex'].append(self.bar_number)
                    self.tradeId += 1

                    performance_summary["netProfit"] = self.net_cash - self.original_cash
                    net_profit_percentage = performance_summary["netProfit"] / \
                                            (performance_summary["netProfit"] + self.original_cash)
                    performance_summary["netProfitPercentage"] = round(net_profit_percentage * 100, 3)

                elif self.long_position and self.trend.is_trade_long_out():
                    self.net_cash = self.net_cash + (self.position_size * self.dataclose[0])
                    print("SELL net cash : ", self.net_cash, "SELL quantity: ", self.position_size)
                    self.order = self.sell()
                    self.trend.clean_long_out_values()
                    self.trend.record_long_out_values(self.series)
                    self.long_position = False

                    #  record trade list
                    trade_list['type2'].append("Exit Long")
                    trade_list['exitBarIndex'].append(self.bar_number)
                    self.tradeId += 1

                    performance_summary["netProfit"] = self.net_cash - self.original_cash
                    net_profit_percentage = performance_summary["netProfit"] / \
                                            (performance_summary["netProfit"] + self.original_cash)
                    performance_summary["netProfitPercentage"] = round(net_profit_percentage * 100, 3)


def process_performance_summary(trade_lists):
    max_gain = 0
    max_gain_short = 0
    max_gain_long = 0
    max_loss = 0
    max_loss_short = 0
    max_loss_long = 0

    total_trades = 0
    total_short_trades = 0
    total_long_trades = 0

    long_profit = 0
    short_profit = 0

    equity = 0
    short_equity = 0
    long_equity = 0

    index = 0
    for trade in trade_lists["type2"]:
        if trade == "Exit Long":
            long_profit = long_profit + trade_lists["profit"][index]

            equity += trade_lists["profit"][index]
            long_equity += trade_lists["profit"][index]
            performance_summary['equity'].append(round(equity, 2))
            performance_summary['long_equity'].append(round(long_equity, 2))

            total_trades += 1
            total_long_trades += 1

            if trade_lists["profit"][index] > 0:
                if trade_lists["profit"][index] > max_gain:
                    max_gain = trade_lists["profit"][index]
                if trade_lists["profit"][index] > max_gain_long:
                    max_gain_long = trade_lists["profit"][index]
            else:
                if trade_lists["profit"][index] < max_loss:
                    max_loss = trade_lists["profit"][index]
                if trade_lists["profit"][index] < max_loss_long:
                    max_loss_long = trade_lists["profit"][index]

        elif trade == "Exit Short":
            short_profit = short_profit + trade_lists["profit"][index]

            equity += trade_lists["profit"][index]
            short_equity += trade_lists["profit"][index]

            performance_summary['equity'].append(round(equity, 2))
            performance_summary['short_equity'].append(round(short_equity, 2))

            total_trades += 1
            total_short_trades += 1

            if trade_lists["profit"][index] > 0:
                if trade_lists["profit"][index] > max_gain:
                    max_gain = trade_lists["profit"][index]
                if trade_lists["profit"][index] > max_gain_short:
                    max_gain_short = trade_lists["profit"][index]
            else:
                if trade_lists["profit"][index] < max_loss:
                    max_loss = trade_lists["profit"][index]
                if trade_lists["profit"][index] < max_loss_short:
                    max_loss_short = trade_lists["profit"][index]

        index += 1

    short_profit_percent = short_profit / (short_profit + 10000)
    long_profit_percent = long_profit / (long_profit + 10000)
    short_profit_percent = round(short_profit_percent * 100, 1)
    long_profit_percent = round(long_profit_percent * 100, 1)

    performance_summary['maxGain'] = max_gain
    performance_summary['maxLoss'] = max_loss
    performance_summary['maxGainShort'] = max_gain_short
    performance_summary['maxGainLong'] = max_gain_long
    performance_summary['maxLossShort'] = max_loss_short
    performance_summary['maxLossLong'] = max_loss_long
    performance_summary['totalTrades'] = total_trades
    performance_summary['totalShortTrades'] = total_short_trades
    performance_summary['totalLongTrades'] = total_long_trades

    performance_summary["longProfit"] = round(long_profit, 1)
    performance_summary["longProfitPercentage"] = long_profit_percent
    performance_summary["shortProfit"] = round(short_profit, 1)
    performance_summary["shortProfitPercentage"] = short_profit_percent

    performance_summary["netProfit"] = round(long_profit + short_profit, 1)


if __name__ == '__main__':
    # *************** connect to firestore *************** #
    cred = credentials.Certificate('cred.json')
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    # ********************************************** #

    symbol = input("Enter the stock symbol that you want to test: ")

    data_file = ""
    if symbol == "TSLA":
        data_file = "TSLA_5m.csv"
    elif symbol == "FUTU":
        data_file = "FUTU_5m.csv"


    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
        dataname=data_file,

        fromdate=datetime.datetime(2020, 12, 1),
        todate=datetime.datetime(2021, 5, 21),

        dtformat=("%Y%m%d  %H:%M:%S"),
        timeframe=bt.TimeFrame.Minutes, compression=5,

        datetime=0,
        open=1,
        close=2,
        high=3,
        low=4,
        volume=5,
        openinterest=6,
        reverse=True
    )
    cerebro.adddata(data)

    cerebro.broker.setcash(20000.0)

    cerebro.run()

    # ************************************************************* #

    process_performance_summary(trade_list)

    trades = []
    df = pd.DataFrame(trade_list)
    for index, row in df.iterrows():
        trades.append(row.to_dict())

    # ******************* upload to fire store ********************* #

    if symbol == "TSLA":
        db.collection(u'backtesting').document(u'TSLA_Summary').delete()
        db.collection(u'backtesting').document(u'TSLA_TradeList').delete()

        doc_ref = db.collection(u'backtesting').document(u'TSLA_Summary')
        doc_ref.set(performance_summary)
        doc_ref = db.collection(u'backtesting').document(u'TSLA_TradeList')
        doc_ref.set({'trades': trades})

    elif symbol == "FUTU":
        db.collection(u'backtesting').document(u'FUTU_Summary').delete()
        db.collection(u'backtesting').document(u'FUTU_TradeList').delete()

        doc_ref = db.collection(u'backtesting').document(u'FUTU_Summary')
        doc_ref.set(performance_summary)
        doc_ref = db.collection(u'backtesting').document(u'FUTU_TradeList')
        doc_ref.set({'trades': trades})

    print("SUCCESSFULLY FINISHING BACKTESTING")
