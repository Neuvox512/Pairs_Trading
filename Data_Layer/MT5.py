import MetaTrader5 as mt5
import pandas as pd

class MT5_Provider:
    def __init__(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 can not be started: {mt5.last_error()}")

    def fetch_bars_from(self, symbol: str, timeframe_id, count: int):

        rates = mt5.copy_rates_from_pos(symbol, timeframe_id, 1, count)

        if rates is None or len(rates) == 0:
            print(f"Error while getting {symbol}: {mt5.last_error()}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def close_connection(self):
        mt5.shutdown()
