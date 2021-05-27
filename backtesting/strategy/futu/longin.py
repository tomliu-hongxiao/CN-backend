import math

from utility.formula import Formula


class LongIn:
    def __init__(self):
        self.open = None
        self.close = None
        self.high = None
        self.low = None
        self.volume = None
        self.time = None
        self.highest = None

        self.highest_volume1_high = None
        self.highest_volume2_high = None

        # 进出点交互变量
        self.long_out_close = None

    def update_ohlc(self, series, highest, highest_volume1_high, highest_volume2_high):
        self.open = series['open']
        self.close = series['close']
        self.high = series['high']
        self.low = series['low']
        self.volume = series['volume']

        self.highest = highest

        self.highest_volume1_high = highest_volume1_high
        self.highest_volume2_high = highest_volume2_high

    def update_long_out_value(self, series, volume_spike, switched_second_volume):
        if (volume_spike or switched_second_volume) and series['close'].iloc[-1] <= series['low'].iloc[-1] + (series['high'].iloc[-1] - series['low'].iloc[-1]) * 0.5 and series['close'].iloc[-1] <= series['open'].iloc[-1]:
            self.long_out_close = series['close'].iloc[-1]

    def clean_long_out_value(self):
        self.long_out_close = None

    def is_long_in(self):

        # ***************  单独进点条件  ************** #

        # sma rate condition
        sma_rate_condition = (Formula.ema(self.close, 200) - Formula.ema(self.close[:-1], 200)) > 0

        # sma condition
        sma_condition = Formula.ema(self.close, 20) > Formula.ema(self.close, 60) > Formula.ema(self.close, 120) > Formula.ema(self.close, 200) and Formula.ema(self.close, 60) > Formula.ema(self.close, 180) and Formula.sma(self.close, 120) > Formula.sma(self.close, 200)

        # macd and 3macd condition
        macd_condition = Formula.macd(self.close, 12, 26, 9) < 0.05 and Formula.macd(self.close, 36, 78, 27) > 0.1

        # price condition
        price_condition = self.close.iloc[-1] >= self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.5
        price_condition = price_condition and self.close.iloc[-1] > self.open.iloc[-1] and self.close.iloc[-1] > Formula.ema(self.close, 20)
        price_condition = price_condition and self.highest > self.close.iloc[-1] > Formula.sma(self.close, 20)

        if self.highest_volume2_high == 0:
            price_condition = price_condition and self.close.iloc[-1] > self.highest_volume1_high
        else:
            if self.highest_volume2_high > self.highest_volume1_high:
                price_condition = price_condition and self.close.iloc[-1] > self.highest_volume2_high
            else:
                price_condition = price_condition and self.close.iloc[-1] > self.highest_volume1_high

        # ************************************** #

        # ***********  进出点 交互条件  *********** #

        interactive_condition = True

        # 如果上次出点 是 因为大量+针信号，下次进点的 close必须要大于上次出点的low
        if self.long_out_close is not None:
            if self.close.iloc[-1] > self.long_out_close:
                interactive_condition = True
            else:
                interactive_condition = False

        # ************************************** #

        is_long_in_condition = sma_rate_condition and sma_condition and macd_condition and price_condition and interactive_condition

        return is_long_in_condition

    def get_a(self):
        # ***************  单独进点条件  ************** #

        # sma rate condition
        sma_rate_condition = (Formula.ema(self.close, 200) - Formula.ema(self.close[:-1], 200)) > 0

        # sma condition
        sma_condition = Formula.ema(self.close, 20) > Formula.ema(self.close, 60) > Formula.ema(self.close, 120) > Formula.ema(self.close, 200) and Formula.ema(self.close, 60) > Formula.ema(self.close, 180) and Formula.sma(self.close, 120) > Formula.sma(self.close, 200)

        # macd and 3macd condition
        macd_condition = Formula.macd(self.close, 12, 26, 9) < 0.05 and Formula.macd(self.close, 36, 78, 27) > 0.1

        # price condition
        price_condition = self.close.iloc[-1] > self.low.iloc[-1] + (self.high.iloc[-1] - self.low.iloc[-1]) * 0.49
        price_condition = price_condition and self.close.iloc[-1] > self.open.iloc[-1] and self.close.iloc[-1] > Formula.ema(self.close, 20)
        price_condition = price_condition and self.highest > self.close.iloc[-1] > Formula.sma(self.close, 20)

        if self.highest_volume2_high == 0:
            price_condition = price_condition and self.close.iloc[-1] > self.highest_volume1_high
        else:
            if self.highest_volume2_high > self.highest_volume1_high:
                price_condition = price_condition and self.close.iloc[-1] > self.highest_volume2_high
            else:
                price_condition = price_condition and self.close.iloc[-1] > self.highest_volume1_high

        # ************************************** #

        # ***********  进出点 交互条件  *********** #

        interactive_condition = True

        # 如果上次出点 是 因为大量+针信号，下次进点的 close必须要大于上次出点的low
        if self.long_out_close is not None:
            if self.close.iloc[-1] > self.long_out_close:
                interactive_condition = True
            else:
                interactive_condition = False

        # ************************************** #
        print("sma rate: ", sma_rate_condition, ",sma: ", sma_condition, ",macd: ", Formula.macd(self.close, 12, 26, 9), ",price: ", price_condition, ",inter: ", interactive_condition)
