from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import MetaTrader5 as mt5
import pandas as pd
from DBManager import DBManager
from MT5 import MT5_Provider
from Timeframes import timeframes
import Timeframes as tf

def update_pair(symbol: str, timeframe):

    timeframe = tf.Timeframe(timeframe)
    db = DBManager(timeframe.frame)
    provider = MT5_Provider()

    local_data = db.get_bars(symbol, limit=1)
    data_from_mt5 = pd.DataFrame(mt5.copy_rates_from_pos('GS', timeframe.id, 1, 1))

    if not data_from_mt5.empty and not data_from_mt5.empty:
        last_local_time = local_data['time'].iloc[0]
        actual_time = pd.to_datetime(data_from_mt5.iloc[0]['time'], unit='s')
        if last_local_time == actual_time:
            print("Data are already up-to-date!")
            provider.close_connection()
            return
        else:
            print(f" Updating {symbol}...")
            missing_data = provider.fetch_bars_from(symbol, timeframe.id, last_local_time, actual_time)

            if not missing_data.empty:
                db.save_bars(symbol, missing_data)

    provider.close_connection()


def mass_update():
    print(f"\n==================================================")
    print(f"Mass update: {datetime.now(ZoneInfo("Europe/Bucharest")).strftime('%Y-%m-%d %H:%M')}")
    print(f"==================================================")

    stocks_list = ['GOOGL', 'MSFT', 'IBM', 'VZ', 'INTC', 'HPE', 'EA', 'ORCL', 'NVDA', 'CSCO', 'ADBE', 'TSLA',
                   'CMCSA', 'DIS', 'FOXA', 'AMZN', 'UPS', 'NFLX', 'MCD', 'SBUX', 'EBAY', 'WMT', 'DAL', 'XOM',
                   'CVX', 'NEM', 'JPM', 'BAC', 'C', 'WFC', 'V', 'GS', 'PYPL', 'PRU', 'BRK.B', 'AAPL', 'KO',
                   'PEP', 'PG', 'PM', 'NKE', 'GM', 'GE', 'MMM', 'CAT', 'BA', 'JNJ', 'PFE', 'LLY', 'META']

    for timeframe in timeframes.keys():
        for stock in stocks_list:
            try:
                update_pair(stock, timeframe)
            except Exception as e:
                print(f"Can not update {stock}: {e}")
        print(f' {timeframe} is up-to-date!')
    print(f"Mass update complete!")


def new_pair(symbol: str, timeframe, days : int):
    timeframe = tf.Timeframe(timeframe)
    db = DBManager(timeframe.frame)
    provider = MT5_Provider()
    date_from = datetime.now(ZoneInfo("Europe/Bucharest")) - timedelta(days=days)

    df_from_db = db.get_bars(symbol, limit=1)
    if not df_from_db.empty:
        print(f" Symbol {symbol} is already in database!")
    else:
        print(f" Adding {symbol}...")
        df_raw = provider.fetch_bars_from(symbol, timeframe.id, date_from)
        if not df_raw.empty:
            db.save_bars(symbol, df_raw)
        print(f" {symbol} is successfully added to database!")

    provider.close_connection()
