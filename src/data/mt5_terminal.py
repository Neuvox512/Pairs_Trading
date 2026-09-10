from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
from src.data.timeframes import MT5_TIMEFRAMES
from src.config import BROKER_TIMEZONE


class MT5Terminal:
    def connect(self) -> None:
        if not mt5.initialize():
            raise RuntimeError(f'Could not connect to MT5 {mt5.last_error()}')

    def close(self) -> None:
        mt5.shutdown()

    #Every query will always be in 'UTC'
    #Therefore our query time will be converted to server time act like 'UTC' to avoid further convertation
    def utc_to_mt5_server_time(self, time_utc: datetime) -> datetime:
        server_time = (pd.Timestamp(time_utc).tz_convert(BROKER_TIMEZONE).tz_localize(None).tz_localize("UTC"))

        return server_time.to_pydatetime()


    def fetch_bars(self,
                   symbol: str,
                   timeframe : str,
                   start_time: datetime,
                   end_time: datetime) -> pd.DataFrame:

        mt5_start_time = self.utc_to_mt5_server_time(start_time)
        mt5_end_time = self.utc_to_mt5_server_time(end_time)

        rates = mt5.copy_rates_range(symbol, MT5_TIMEFRAMES[timeframe], mt5_start_time, mt5_end_time)

        if rates is None:
            raise RuntimeError(f'Could not fetch rates for {symbol}: {mt5.last_error()}')

        bars = pd.DataFrame(rates)

        #Despite documentation mt5 return server time, so for convenient work 'time' was standardized to 'UTC'
        bars['time'] = pd.to_datetime(bars['time'], unit='s').dt.tz_localize(BROKER_TIMEZONE).dt.tz_convert('UTC')
        bars = bars.rename(columns={'time': 'time_utc'})

        return bars


    def get_all_symbols(self) -> list[str]:
        symbols = mt5.symbols_get()
        all_symbols = []
        for symbol in symbols:
            path = symbol.path.lower()
            if 'stock' in path:
                all_symbols.append(symbol.name)
        return all_symbols


    def get_latest_closed_bar_time(self, symbol: str, timeframe: str,) -> None | pd.Timestamp:
        rates = mt5.copy_rates_from_pos(symbol, MT5_TIMEFRAMES[timeframe], 1, 1)

        if rates is None:
            raise RuntimeError(f'Could not fetch rates for {symbol}: {mt5.last_error()}')

        if len(rates) == 0:
            return None

        return pd.to_datetime(rates[0]['time'], unit='s').tz_localize(BROKER_TIMEZONE).tz_convert('UTC')


