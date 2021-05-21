import math
import pandas as pd
import numpy as np


class Formula:

    @staticmethod
    def sma_series(series, periods: int, fillna: bool = False):
        min_periods = 0 if fillna else periods
        return series.rolling(window=periods, min_periods=min_periods).mean().round(4)

    @staticmethod
    def sma(series, periods):
        return series[-periods:].mean()

    @staticmethod
    def ema_series(series, periods, fillna=False):
        min_periods = 0 if fillna else periods
        return series.ewm(span=periods, min_periods=min_periods, adjust=False).mean().round(2)

    @staticmethod
    def ema(series, periods, fillna=False):
        return Formula.ema_series(series, periods, fillna).iloc[-1]

    @staticmethod
    def macd_series(series, fastlen, slowlen, siglen):
        dif = Formula.ema_series(series, fastlen) - Formula.ema_series(series, slowlen)
        dea = Formula.ema_series(dif, siglen)
        return round((dif - dea) * 2, 2)

    @staticmethod
    def macd(series, fastlen, slowlen, siglen):
        return (Formula.macd_series(series, fastlen, slowlen, siglen)).iloc[-1]

    @staticmethod
    def volume_spike(series):
        if series.iloc[-1] > 2 * Formula.sma(series[:-1], 10):
            return True
        else:
            return False
