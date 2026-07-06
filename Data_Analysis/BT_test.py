import pandas as pd
import datetime

from fontTools.varLib import plot

from Pairs import Pairs
from Data_Layer.Timeframes import Timeframe
import MetaTrader5 as mt5

days = 20
ALPHA = 0.1066848579749114
BETA = 1.064581787322044

if not mt5.initialize():
    print("Can not connect to MT5")
    mt5.shutdown()


# coint_days = []
# for i in range(251):
#     pairs = Pairs('GBPUSD', 'EURUSD', 'M30', i+1, 20)
#     print(pairs.cointegration())
#     if pairs.cointegration() < 0.06:
#         coint_days.append(i)
# print(coint_days)

# for i in range(2):
#     tfr = Timeframe('M30')
#     pairs = Pairs('GBPUSD', 'EURUSD', 'M30', 154, 40, days*tfr.bars*(i+2))
#     bt = pairs.backtest(0.25,1,0.2)
#     print(f'test No.{i}: {bt.pnl()}')
#     bt.plot()
#
#
# for i in range(2):
#     tfr = Timeframe('M30')
#     pairs = Pairs('GBPUSD', 'EURUSD', 'M30', 154, 40, days*tfr.bars*i)
#     bt = pairs.backtest(0.25,1,0.2)
#     print(f'Verification No.{i}: {bt.pnl()}')
#     bt.plot()


pairs = Pairs('GBPUSD', 'EURUSD', 'M30', 154, 40,6)
print (pairs.backtest.plot())
