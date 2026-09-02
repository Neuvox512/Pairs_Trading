from Pairs import Pairs
import pandas as pd
import datetime
from Data_Analysis.Coint_pairs import recursive_test_pairs
from Pairs import Pairs
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from Coint_pairs import coint_pairs_3
import numpy as np
from tqdm import tqdm


stocks_list = ['GOOGL', 'MSFT', 'IBM', 'VZ', 'INTC', 'HPE', 'EA', 'ORCL', 'NVDA', 'CSCO', 'ADBE', 'TSLA',
               'CMCSA', 'DIS', 'FOXA', 'AMZN', 'UPS', 'NFLX', 'MCD', 'SBUX', 'EBAY', 'WMT', 'DAL', 'XOM',
               'CVX', 'NEM', 'JPM', 'BAC', 'C', 'WFC', 'V', 'GS', 'PYPL', 'PRU', 'BRK.B', 'AAPL', 'KO',
               'PEP', 'PG', 'PM', 'NKE', 'GM', 'GE', 'MMM', 'CAT', 'BA', 'JNJ', 'PFE', 'LLY', 'META']

start = datetime(2026, 4, 24, 16, 30, 00)
end = datetime(2026, 4, 24, 22, 30, 00)
small_window = 30 #30 min


def first_check(big_window_start, big_window_end, small_window):
    bw_start = big_window_start
    bw_end = big_window_end - timedelta(hours = 5)
    coint_pairs = []
    for symbol_1 in tqdm(stocks_list):
        for symbol_2 in stocks_list:
            if symbol_1 == symbol_2:
                continue
            pairs = Pairs(symbol_1, symbol_2, 'M1', bw_start, bw_end, small_window)
            if pairs.cointegration() <= 0.05:
                coint_pairs.append((symbol_1, symbol_2))

    print(coint_pairs)
    print(len(coint_pairs))
    return coint_pairs


def coint(pairs : list, big_window_start : datetime, big_window_end : datetime, small_window : int, iter = 1):
    bw_start = big_window_start - timedelta(days=iter)
    bw_end = big_window_end - timedelta(days=iter)
    new_pairs = []
    try:
        for tuple in tqdm(pairs):
            pair = Pairs(tuple[0], tuple[1], 'M1', bw_start, bw_end, small_window)
            if pair.cointegration() <= 0.1:
                new_pairs.append(tuple)
        pairs = new_pairs
        print('Number of days: ', iter)
        if iter >= 6:
            print(pairs)
            return pairs
        else:return coint(pairs, big_window_start, big_window_end,small_window,iter+1)
    except Exception as e:
        print(e)
        # print(f"{big_window_start.strftime('%Y-%m-%d')} is weekend, holiday or no more pairs")
        print('Number of days: ', iter)
        return coint(pairs, big_window_start, big_window_end,small_window,iter+1)


def backtest(coint_pairs, big_window_start, big_window_end, small_window, hours : int):
    bw_start = big_window_start + timedelta(hours = (1 + hours)/2)
    bw_end = big_window_end - timedelta(hours = (9 - hours)/2)
    sum = 0
    df = pd.DataFrame()
    for pair in coint_pairs:
        pairs = Pairs(pair[0], pair[1], 'M1', bw_start, bw_end, small_window)
        bt = pairs.backtest(0.05, 2.5).df[['time', 'PnL']]
        if df.empty:
            df = bt
            continue
        df = pd.merge(df, bt, on='time', how='inner').dropna()
        df['total_PnL'] = df.iloc[:, 1] + df.iloc[:, 2]
        df = df[['time', 'total_PnL']]
    print(sum)
    return df



x = coint(first_check(start, end, small_window), start,end,small_window)
all_dfs = []
for hour in range (9):
    bt = backtest(x, start, end, small_window, hour)
    all_dfs.append(bt)
combined = pd.concat(all_dfs, ignore_index=True)
combined = combined[['time','total_PnL']]
print(combined)
std = combined['total_PnL'].std()
sum = combined['total_PnL'].sum()
print('Standard Deviation: ', std)
print('Sum: ', sum)
print (f'Sharpe ratio: {sum/std}')





