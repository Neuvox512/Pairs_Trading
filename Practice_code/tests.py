import time
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as sm

SYMBOL_A = "GBPUSD"
SYMBOL_B = "EURUSD"
BETA = 1.037547782539148
ALPHA = 0.13512473198059174

WINDOW_SMALL = 10*24*2

if not mt5.initialize():
    print("Ошибка подключения к MT5. Бот остановлен.")
    mt5.shutdown()


# bars_a = mt5.copy_rates_from_pos(SYMBOL_A, mt5.TIMEFRAME_M30, 12 , WINDOW_SMALL + 2)
# bars_b = mt5.copy_rates_from_pos(SYMBOL_B, mt5.TIMEFRAME_M30, 12, WINDOW_SMALL + 2)
#
# df_a = pd.DataFrame(bars_a)
# df_b = pd.DataFrame(bars_b)
#
# symbol_B_with_const = sm.add_constant(df_b['close'])
# lin_reg = sm.OLS(df_a['close'], symbol_B_with_const).fit()
# intercept = lin_reg.params['const']
# slope = lin_reg.params['close']
# spread = df_a["close"] - (slope * df_b["close"] + intercept)
#
# df_s1 = spread[1:].values
# df_s2 = spread[:-1].values
# s_2_with_const = sm.add_constant(df_s2)
#
# model = sm.OLS(df_s1, s_2_with_const).fit()
# if model.pvalues[1] > 0.05:
#     raise ValueError(f'Mean revertion is impossible: no cointegration')
# a = model.params[0]
# b = model.params[1]
# std_residuals = np.std(model.resid)
# if b >= 1.0 or b <= 0:
#     raise ValueError(f'Mean revertion is impossible: b = {b}')
#
# theta = -np.log(b) / 1.0
# mu = a / (1 - b)
# sigma = std_residuals * np.sqrt((-2 * np.log(b)) / (1.0 * (1 - b ** 2)))
# half_time = np.log(2) / theta
# print('half_time:', half_time)
#
# z_score = (df_s2[-1] - mu) / (sigma / (np.sqrt(2 * theta)))
# spread_centered = df_s2[-1] - mu
# print('spread: ',df_s2[-1])
# print('average: ',mu)
# print('alfa:',intercept)
# print('beta:',slope)