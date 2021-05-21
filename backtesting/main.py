import datetime  # For datetime objects
import pandas as pd
import backtrader as bt

from strategy.trend import Trend

trade_list = {"tradeId": [], "type": [], "datetime": [], "price": [], "quantity": []}
trade_detail = {}
performance_summary = {"netProfit": 0, "netProfitPercentage": 0.0, "longProfit": 0, "longProfitPercentage": 0.0,
                       "shortProfit": 0, "shortProfitPercentage": 0.0}

series = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}


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
        self.trend = Trend()

        self.short_position = False
        self.long_position = False

        self.tradeId = 1

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
                trade_list['price'].append(order.executed.price)
            elif order.issell():
                trade_list['price'].append(order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference

        series['date'].append(self.datas[0].datetime.time().strftime("%H:%M:%S"))
        series['close'].append(self.dataclose[0])
        series['open'].append(self.dataopen[0])
        series['high'].append(self.datahigh[0])
        series['low'].append(self.datalow[0])
        series['volume'].append(self.datavolume[0])
        self.series = pd.DataFrame(series)

        if len(self.series) > 250:

            if self.datas[0].datetime.time().strftime("%H:%M:%S") == "04:00:00":
                self.trend.reset()
            self.trend.update_trend(self.series)

            if self.datas[0].datetime.datetime().strftime("%Y-%m-%d, %H:%M:%S") == "2021-05-13, 12:25:00":
                print(self.trend.get_a())

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
                    self.update_trade_list("Entry Short")

                elif self.trend.is_trade_long_in():
                    self.position_size = int(self.net_cash / self.dataclose[0])
                    self.net_cash = self.net_cash - (self.position_size * self.dataclose[0])
                    print("BUY net cash : ", self.net_cash, self.position_size)
                    self.order = self.buy()
                    self.trend.clean_long_in_values()
                    self.trend.record_long_in_values(self.series)
                    self.long_position = True
                    self.update_trade_list("Entry Long")

            else:

                # Already in the market ... we might sell
                if self.short_position and self.trend.is_trade_short_out():
                    self.net_cash = self.net_cash - (self.position_size * self.dataclose[0]) - 2
                    print("BUY net cash: ", self.net_cash, ", BUY quantity: ", self.position_size)
                    self.order = self.buy()
                    self.trend.clean_short_out_values()
                    self.trend.record_short_out_values(self.series)
                    self.short_position = False
                    self.update_trade_list("Exit Short")
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
                    self.update_trade_list("Exit Long")
                    self.tradeId += 1

                    performance_summary["netProfit"] = self.net_cash - self.original_cash
                    net_profit_percentage = performance_summary["netProfit"] / \
                                            (performance_summary["netProfit"] + self.original_cash)
                    performance_summary["netProfitPercentage"] = round(net_profit_percentage * 100, 3)

    def update_trade_list(self, order_type):
        trade_list['tradeId'].append(self.tradeId)
        trade_list["type"].append(order_type)
        trade_list["datetime"].append(self.datas[0].datetime.datetime().strftime("%Y%m%d, %H:%M:%S"))
        trade_list["quantity"].append(self.position_size)


def process_performance_summary(trade_lists):
    long_profit = 0
    short_profit = 0
    index = 0
    for trade in trade_lists["type"]:
        if trade == "Exit Long":
            long_profit = long_profit + (trade_lists["price"][index] - trade_list["price"][index-1]) * trade_lists["quantity"][index]
        elif trade == "Exit Short":
            short_profit = short_profit + (trade_lists["price"][index - 1] - trade_list["price"][index]) * trade_lists["quantity"][index]
        index += 1

    short_profit_percent = short_profit / (short_profit + 10000)
    long_profit_percent = long_profit / (long_profit + 10000)
    short_profit_percent = round(short_profit_percent * 100, 3)
    long_profit_percent = round(long_profit_percent * 100, 3)

    return [round(long_profit, 1), long_profit_percent, round(short_profit, 1), short_profit_percent]


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
        dataname="TSLA_IB_backtesting.csv",

        fromdate=datetime.datetime(2021, 2, 24),
        todate=datetime.datetime(2021, 5, 19),

        dtformat=("%Y%m%d  %H:%M"),
        timeframe=bt.TimeFrame.Minutes, compression=5,

        datetime=1,
        open=2,
        close=3,
        high=4,
        low=5,
        volume=6,
        openinterest=7,
        reverse=True
    )
    cerebro.adddata(data)

    cerebro.broker.setcash(20000.0)
    cerebro.broker.setcommission(commission=0.001)
    # cerebro.addsizer(bt.sizers.SizerFix, stake=33)

    cerebro.run()

    df = pd.DataFrame(trade_list)
    file_name = "trade_list.csv"
    df.to_csv(file_name)

    # # *************************************** # #

    summary = process_performance_summary(trade_list)
    performance_summary["longProfit"] = summary[0]
    performance_summary["longProfitPercentage"] = summary[1]
    performance_summary["shortProfit"] = summary[2]
    performance_summary["shortProfitPercentage"] = summary[3]
    performance_summary["netProfit"] = round(performance_summary["netProfit"], 1)
    df = pd.DataFrame(performance_summary, index=[0])
    file_name = "performance_summary.csv"
    df.to_csv(file_name)
