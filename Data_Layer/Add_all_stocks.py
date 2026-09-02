from MT5 import MT5_Provider
from Timeframes import *
from data_update import new_pair


stocks = MT5_Provider().get_stocks()
MT5_Provider().close_connection()

for timeframe in timeframes.keys():
    for symbol in stocks:
        new_pair(symbol, timeframe, 730)
    print('============================================================')
    print(f'{timeframe} is done!')
    print('============================================================')