import math

from utility.formula import Formula


class ShortIn:
    def __init__(self):
        self.open = None
        self.close = None
        self.high = None
        self.low = None
        self.volume = None
        self.time = None
        self.lowest = None

        self.highest_volume1_low = None
        self.highest_volume2_low = None

        # 进出点交互变量
        self.short_out_low = None

    def update_ohlc(self, series, lowest, highest_volume1_low, highest_volume2_low):
        self.open = series['open']
        self.close = series['close']
        self.high = series['high']
        self.low = series['low']
        self.volume = series['volume']

        self.lowest = lowest

        self.highest_volume1_low = highest_volume1_low
        self.highest_volume2_low = highest_volume2_low

    def update_short_out_value(self, series, volume_spike, switched_second_volume):
        if (volume_spike or switched_second_volume) and series['close'].iloc[-1] >= (series['low'].iloc[-1] + (series['high'].iloc[-1] - series['low'].iloc[-1]) * 0.85) and series['close'].iloc[-1] > series['open'].iloc[-1]:
            self.short_out_low = series['low'].iloc[-1]

    def clean_short_out_value(self):
        self.short_out_low = None

    def is_short_in(self):

        # ***************  单独进点条件  ************** #

        # sma rate condition
        sma_rate_condition = (Formula.ema(self.close, 120) - Formula.ema(self.close[:-1], 120)) <= 0

        # sma condition
        sma_condition = Formula.ema(self.close, 20) < Formula.ema(self.close, 60) < Formula.ema(self.close, 120) and Formula.ema(self.close, 60) < Formula.ema(self.close, 200)

        # macd condition
        macd_condition = Formula.macd(self.close, 12, 26, 9) > 0 and Formula.macd(self.close, 36, 78, 27) < -0.5

        # price condition
        price_condition = self.close.iloc[-1] <= self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.382
        price_condition = price_condition and self.close.iloc[-1] < self.open.iloc[-1] and self.close.iloc[-1] < Formula.ema(self.close, 20)
        price_condition = price_condition and self.lowest < self.close.iloc[-1] < Formula.sma(self.close, 20)

        if self.highest_volume2_low == 0:
            price_condition = price_condition and self.close.iloc[-1] < self.highest_volume1_low
        else:
            if self.highest_volume2_low < self.highest_volume1_low:
                price_condition = price_condition and self.close.iloc[-1] < self.highest_volume2_low
            else:
                price_condition = price_condition and self.close.iloc[-1] < self.highest_volume1_low

        # ************************************** #

        # ***********  进出点 交互条件  *********** #

        # 如果上次出点 是 因为大量+针信号，下次进点的 close必须要小于上次出点的high
        interactive_condition = True
        if self.short_out_low is not None:
            if self.close.iloc[-1] < self.short_out_low:
                interactive_condition = True
            else:
                interactive_condition = False
        # ************************************** #

        is_short_in_condition = sma_rate_condition and sma_condition and macd_condition and price_condition and interactive_condition

        return is_short_in_condition

    def get_a(self):
        # ***************  单独进点条件  ************** #

        # sma rate condition
        sma_rate_condition = (Formula.ema(self.close, 120) - Formula.ema(self.close[:-1], 120)) <= 0

        # sma condition
        sma_condition = Formula.ema(self.close, 20) < Formula.ema(self.close, 60) < Formula.ema(self.close, 120) and Formula.ema(self.close, 60) < Formula.ema(self.close, 200)

        # macd condition
        macd_condition = Formula.macd(self.close, 12, 26, 9) > 0 and Formula.macd(self.close, 36, 78, 27) < -0.5

        # price condition
        price_condition = self.close.iloc[-1] <= self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.382
        price_condition = price_condition and self.close.iloc[-1] < self.open.iloc[-1] and self.close.iloc[-1] < Formula.ema(self.close, 20)
        price_condition = price_condition and self.lowest < self.close.iloc[-1] < Formula.sma(self.close, 20)

        if self.highest_volume2_low == 0:
            price_condition = price_condition and self.close.iloc[-1] < self.highest_volume1_low
        else:
            if self.highest_volume2_low < self.highest_volume1_low:
                price_condition = price_condition and self.close.iloc[-1] < self.highest_volume2_low
            else:
                price_condition = price_condition and self.close.iloc[-1] < self.highest_volume1_low

        # ************************************** #

        # ***********  进出点 交互条件  *********** #

        # 如果上次出点 是 因为大量+针信号，下次进点的 close必须要小于上次出点的high
        interactive_condition = True
        if self.short_out_low is not None:
            if self.close.iloc[-1] < self.short_out_low:
                interactive_condition = True
            else:
                interactive_condition = False
        # ************************************** #
        # print("sma: ", sma_condition, ", sma rate: ", sma_rate_condition, ", macd: ", macd_condition, ", price: ", price_condition, ", inter: ", interactive_condition)
        # print("sma 60: ", Formula.ema(self.close, 60))
        # print("sma 200: ", Formula.ema(self.close, 200))
        # print("test: ", self.close.iloc[-1] <= self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.382)
        # print("close: ", self.close.iloc[-1])
        # print("low: ", self.low.iloc[-1])
        # print("high: ", self.close.iloc[-1] < self.highest_volume2_low)