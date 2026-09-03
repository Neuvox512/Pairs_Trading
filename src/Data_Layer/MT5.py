import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime


class MT5_Provider:
    def __init__(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 can not be started: {mt5.last_error()}")

    def fetch_bars_from(self, symbol: str, timeframe_id, date_from : datetime, date_to : datetime):

        rates = mt5.copy_rates_range(symbol, timeframe_id, date_from, date_to)

        if rates is None or len(rates) == 0:
            print(f"Error while getting {symbol}: {mt5.last_error()}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def get_stocks(self):

        stocks = mt5.symbols_get()
        stock_list = []
        for symbol in stocks:
            path = symbol.path.lower()
            if 'stock' in path:
                stock_list.append(symbol.name)
        return stock_list

    def close_connection(self):
        mt5.shutdown()
