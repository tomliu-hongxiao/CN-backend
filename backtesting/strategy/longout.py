import datetime
import math

from utility.formula import Formula


class LongOut:
    def __init__(self):
        self.open = None
        self.close = None
        self.high = None
        self.low = None
        self.volume = None
        self.datetime = None

        self.highest_volume1_high = None
        self.highest_volume2_high = None

        self.volume_spike = False
        self.switched_second_volume = False

        # trading hours parameter
        self.current_time = datetime.datetime.now().time()
        self.close_position_time = self.current_time.replace(hour=15, minute=55, second=0, microsecond=0)

        # 进出点交互变量
        self.long_in_low = 0

    def update_ohlc(self, series, highest_volume1_high, highest_volume2_high, volume_spike, switched_second_volume):
        self.open = series['open']
        self.close = series['close']
        self.high = series['high']
        self.low = series['low']
        self.volume = series['volume']
        self.datetime = datetime.datetime.strptime(series['date'].iloc[-1], "%H:%M:%S").time()

        self.highest_volume1_high = highest_volume1_high
        self.highest_volume2_high = highest_volume2_high

        self.volume_spike = volume_spike
        self.switched_second_volume = switched_second_volume

    def update_long_in_value(self, series):
        self.long_in_low = series['low'].iloc[-1]

    def clean_long_in_value(self):
        self.long_in_low = 0

    def is_long_out(self):

        # ***************  单独进点条件  ************** #

        # 有 volume 大于开盘前的 第二根volume 时，close position
        spike_condition1 = self.switched_second_volume

        # 大量+斜率 close
        spike_condition2_1 = self.volume_spike
        spike_condition2_2 = (self.close.iloc[-1] - self.close.iloc[-3]) / 3 >= math.tan(math.pi * 11 / 36)
        spike_condition2_3 = self.close.iloc[-1] <= self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.5 and self.close.iloc[-1] <= self.open.iloc[-1]
        spike_condition2 = (spike_condition2_1 and spike_condition2_2) or (spike_condition2_1 and spike_condition2_3) or (spike_condition2_2 and spike_condition2_3)

        # 破线拐头出点信号
        sma_condition = self.close.iloc[-1] < Formula.ema(self.close, 20) and self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.618 < Formula.sma(self.close, 20)

        # stop loss
        stop_loss_condition = self.close.iloc[-1] < Formula.sma(self.close, 60)

        # 当天结束
        end_of_day_condition = self.datetime == self.close_position_time

        # ************************************** #

        # ***********  进出点 交互条件  *********** #

        # 出点大于近点close price
        price_condition = self.close.iloc[-1] < self.long_in_low - 1.5  # 超过进点止损信号， 0.5 是一个针对tsla的值，可以调整，这个策略是为了保护为远离sma20的short进点

        # ************************************** #

        is_long_out_condition = spike_condition1 or spike_condition2 or sma_condition or price_condition or stop_loss_condition or end_of_day_condition
        return is_long_out_condition
