import datetime

from utility.formula import Formula
from strategy.shortin import ShortIn
from strategy.shortout import ShortOut
from strategy.longin import LongIn
from strategy.longout import LongOut


class Trend:
    def __init__(self):
        self.short_in = ShortIn()
        self.short_out = ShortOut()
        self.long_in = LongIn()
        self.long_out = LongOut()

        # indicator
        self.lowest_close = 10000  #初始值，用于比较
        self.highest_close = 0

        self.highest_volume1 = 0
        self.highest_volume2 = 0
        self.highest_volume1_low = None
        self.highest_volume1_high = None
        self.highest_volume2_low = None
        self.highest_volume2_high = None

        self.volume_spike = False
        self.switched_second_volume = False

        # OHLC
        self.series = None
        self.volume_series = None
        self.high_series = None
        self.low_series = None
        self.close_series = None
        self.open_series = None
        self.date_series = None

        # trading hours parameter
        self.current_time = datetime.datetime.now().time()
        self.opening_time = self.current_time.replace(hour=9, minute=30, second=0, microsecond=0)
        self.trade_begin_time = self.current_time.replace(hour=9, minute=50, second=0, microsecond=0)
        self.trade_end_time = self.current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        self.trade_in_end_time = self.current_time.replace(hour=15, minute=25, second=0, microsecond=0)

    def reset(self):
        # indicator
        self.lowest_close = 10000  #初始值，用于比较
        self.highest_close = 0

        self.highest_volume1 = 0
        self.highest_volume2 = 0
        self.highest_volume1_low = None
        self.highest_volume1_high = None
        self.highest_volume2_low = None
        self.highest_volume2_high = None

        self.volume_spike = False
        self.switched_second_volume = False

        # OHLC
        self.series = None
        self.volume_series = None
        self.high_series = None
        self.low_series = None
        self.close_series = None
        self.open_series = None
        self.date_series = None

        # trading hours parameter
        self.current_time = datetime.datetime.now().time()
        self.opening_time = self.current_time.replace(hour=9, minute=30, second=0, microsecond=0)
        self.trade_begin_time = self.current_time.replace(hour=9, minute=50, second=0, microsecond=0)
        self.trade_end_time = self.current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        self.trade_in_end_time = self.current_time.replace(hour=15, minute=25, second=0, microsecond=0)


    # ***************  做空   ************** #

    def is_trade_short_in(self):
        self.current_time = datetime.datetime.strptime(self.date_series.iloc[-1], "%H:%M:%S").time()
        # 判断当前时间是否在9：50 到 15：30之间， 做空进点时间只发生在9：50 到 15：30之间
        if self.trade_begin_time < self.current_time <= self.trade_in_end_time:

            self.short_in.update_ohlc(self.series, self.lowest_close, self.highest_volume1_low,
                                      self.highest_volume2_low)

            return self.short_in.is_short_in()
        else:
            return False

    def is_trade_short_out(self):
        self.current_time = datetime.datetime.strptime(self.date_series.iloc[-1], "%H:%M:%S").time()
        # 判断当前时间是否在9：50 到 16：00之间
        if self.trade_begin_time < self.current_time <= self.trade_end_time:

            self.short_out.update_ohlc(self.series, self.highest_volume1_low, self.highest_volume2_low,
                                       self.volume_spike, self.switched_second_volume)

            return self.short_out.is_short_out()
        else:
            return False

    def clean_short_in_values(self):
        self.short_in.clean_short_out_value()

    def clean_short_out_values(self):
        self.short_out.clean_short_in_value()

    def record_short_in_values(self, series):
        self.short_out.update_short_in_value(series)

    def record_short_out_values(self, series):
        self.short_in.update_short_out_value(series, self.volume_spike, self.switched_second_volume)

    # ************************************** #

    # ***************  做涨   ************** #

    def is_trade_long_in(self):
        self.current_time = datetime.datetime.strptime(self.date_series.iloc[-1], "%H:%M:%S").time()
        # 判断当前时间是否在9：50到16：00之间，做涨进点时间只发生在9：50 到 15：35之间
        if self.trade_begin_time < self.current_time <= self.trade_in_end_time:
            self.long_in.update_ohlc(self.series, self.highest_close, self.highest_volume1_high,
                                     self.highest_volume2_high)

            return self.long_in.is_long_in()
        else:
            return False

    def is_trade_long_out(self):
        self.current_time = datetime.datetime.strptime(self.date_series.iloc[-1], "%H:%M:%S").time()
        # 判断当前时间是否在9：50到16：00之间
        if self.trade_begin_time < self.current_time <= self.trade_end_time:
            self.long_out.update_ohlc(self.series, self.highest_volume1_high, self.highest_volume2_high,
                                      self.volume_spike, self.switched_second_volume)

            return self.long_out.is_long_out()
        else:
            return False

    def clean_long_in_values(self):
        self.long_in.clean_long_out_value()

    def clean_long_out_values(self):
        self.long_out.clean_long_in_value()

    def record_long_in_values(self, series):
        self.long_out.update_long_in_value(series)

    def record_long_out_values(self, series):
        self.long_in.update_long_out_value(series, self.volume_spike, self.switched_second_volume)

    # ************************************** #

    # ***********  更新 条件条件  *********** #

    def update_trend(self, series) -> None:  # tested
        # 更新OHLC数据
        self.series = series
        self.open_series = series['open']
        self.high_series = series['high']
        self.low_series = series['low']
        self.close_series = series['close']
        self.volume_series = series['volume']
        self.date_series = series['date']

        # 更新当前时间
        self.current_time = datetime.datetime.strptime(self.date_series.iloc[-1], "%H:%M:%S").time()
        # print("当前时间 ：", self.current_time)

        # 交易时间 9：30 - 16：00
        if self.opening_time <= self.current_time <= self.trade_end_time:

            # 判断是否是volume spike
            self.volume_spike = Formula.volume_spike(self.volume_series)

            # 记录当天最大和最小的close价格
            if self.close_series.iloc[-1] > self.highest_close:
                self.highest_close = self.close_series.iloc[-1]
            if self.close_series.iloc[-1] < self.lowest_close:
                self.lowest_close = self.close_series.iloc[-1]

            # 开盘时间 9：30 - 9：50   ### 开盘前计算并记录两跟最大volume bar
            if self.current_time <= self.trade_begin_time:
                if self.volume_series.iloc[-1] > self.highest_volume1:
                    self.highest_volume2 = self.highest_volume1
                    self.highest_volume2_low = self.highest_volume1_low
                    self.highest_volume2_high = self.highest_volume1_high

                    self.highest_volume1 = self.volume_series.iloc[-1]
                    self.highest_volume1_high = self.high_series.iloc[-1]
                    self.highest_volume1_low = self.low_series.iloc[-1]

                    if self.highest_volume2 <= self.highest_volume1 * 0.7:
                        self.highest_volume2 = 0
                        self.highest_volume2_high = 0
                        self.highest_volume2_low = 0

                elif self.volume_series.iloc[-1] > self.highest_volume2 and self.volume_series.iloc[-1] > self.highest_volume1 * 0.7:
                    self.highest_volume2 = self.volume_series.iloc[-1]
                    self.highest_volume2_high = self.high_series.iloc[-1]
                    self.highest_volume2_low = self.low_series.iloc[-1]

            #  时间 9：50  ### 如果开盘时间结束，并且第二根volume bar始终是0，那就给第二根赋值为 第一根volume bar的70%
            if self.trade_begin_time == self.current_time and self.highest_volume2 == 0:
                self.highest_volume2 = self.highest_volume1 * 0.7

            # 交易时间 9：50 - 16：00
            if self.trade_begin_time < self.current_time < self.trade_end_time:
                # 如果出现一根比第二根volume 大的volume bar，那就和当前第二根volume bar替换
                if self.volume_series.iloc[-1] > self.highest_volume2:
                    self.highest_volume2 = self.volume_series.iloc[-1]
                    self.highest_volume2_high = self.high_series.iloc[-1]
                    self.highest_volume2_low = self.low_series.iloc[-1]
                    self.switched_second_volume = True
                else:
                    self.switched_second_volume = False

            # test print
            # print("volume1 : ", self.highest_volume1)
            # print("volume1 high : ", self.highest_volume1_high)
            # print("volume1 low : ", self.highest_volume1_low)
            # print("volume2 : ", self.highest_volume2)
            # print("volume2 high : ", self.highest_volume2_high)
            # print("volume2 low : ", self.highest_volume2_low)
            # print("lowest : ", self.lowest_close)
            # print("highest : ", self.highest_close)

    def get_a(self):

        print("volume1 : ", self.highest_volume1)
        print("volume1 high : ", self.highest_volume1_high)
        print("volume1 low : ", self.highest_volume1_low)
        print("volume2 : ", self.highest_volume2)
        print("volume2 high : ", self.highest_volume2_high)
        print("volume2 low : ", self.highest_volume2_low)
        print("lowest : ", self.lowest_close)
        print("highest : ", self.highest_close)

    def config_opening_indicator(self, series) -> None:
        # 更新OHLC数据
        self.series = series
        self.open_series = series['open']
        self.high_series = series['high']
        self.low_series = series['low']
        self.close_series = series['close']
        self.volume_series = series['volume']
        self.date_series = series['date']

        # 处理并记录开盘前的数值
        index = -1
        item = datetime.datetime.strptime(self.date_series.iloc[index], "%H:%M:%S").time()
        while item >= self.opening_time:
            if self.close_series.iloc[index] > self.highest_close:
                self.highest_close = self.close_series.iloc[index]
            if self.close_series.iloc[index] < self.lowest_close:
                self.lowest_close = self.close_series.iloc[index]

            # 开盘前 9：30 - 9：50
            if item <= self.trade_begin_time:
                # 开盘前计算并记录两跟最大volume bar
                if self.volume_series.iloc[index] > self.highest_volume1:
                    self.highest_volume2 = self.highest_volume1
                    self.highest_volume2_low = self.highest_volume1_low
                    self.highest_volume2_high = self.highest_volume1_high

                    self.highest_volume1 = self.volume_series.iloc[index]
                    self.highest_volume1_high = self.high_series.iloc[index]
                    self.highest_volume1_low = self.low_series.iloc[index]

                    if (self.highest_volume2 <= self.highest_volume1 * 0.7):
                        self.highest_volume2 = 0
                        self.highest_volume2_high = 0
                        self.highest_volume2_low = 0

                elif self.volume_series.iloc[index] > self.highest_volume2 and self.volume_series.iloc[index] >= self.highest_volume1 * 0.7:
                    self.highest_volume2 = self.volume_series.iloc[index]
                    self.highest_volume2_high = self.high_series.iloc[index]
                    self.highest_volume2_low = self.low_series.iloc[index]

            index = index - 1
            item = datetime.datetime.strptime(self.date_series.iloc[index], "%H:%M:%S").time()

        # 如果开盘时间结束，并且第二根volume bar始终是0，那就给第二根赋值为 第一根volume bar的70%
        index = -1
        item = datetime.datetime.strptime(self.date_series.iloc[index], "%H:%M:%S").time()
        if  item >= self.trade_begin_time and self.highest_volume2 == 0:
            self.highest_volume2 = self.highest_volume1 * 0.7

        # 处理并记录开盘后的数值
        index = -1
        item = datetime.datetime.strptime(self.date_series.iloc[index], "%H:%M:%S").time()
        while item >= self.trade_begin_time:

            # 开盘时间结束后， 如果出现一根比第二根volume 大的volume bar，那就和当前第二根volume bar替换
            if self.volume_series.iloc[index] > self.highest_volume2:
                self.highest_volume2 = self.volume_series.iloc[index]
                self.highest_volume2_high = self.high_series.iloc[index]
                self.highest_volume2_low = self.low_series.iloc[index]
            index = index - 1
            item = datetime.datetime.strptime(self.date_series.iloc[index], "%H:%M:%S").time()

        print("volume1 : ", self.highest_volume1)
        print("volume1 high : ", self.highest_volume1_high)
        print("volume1 low : ", self.highest_volume1_low)
        print("volume2 : ", self.highest_volume2)
        print("volume2 high : ", self.highest_volume2_high)
        print("volume2 low : ", self.highest_volume2_low)
        print("lowest : ", self.lowest_close)
        print("highest : ", self.highest_close)

    # ************************************* #


