from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5
from src.data.timeframes import MT5_TIMEFRAMES
from src.config import MT5_TERMINAL_PATH, PEPPERSTONE_REFERENCE_TIMEZONE, PEPPERSTONE_SERVER_SHIFT_HOURS


class MT5Terminal:
    def connect(self) -> None:
        if not mt5.initialize(path=MT5_TERMINAL_PATH):
            raise RuntimeError(f'Could not connect to MT5 {mt5.last_error()}')

    def close(self) -> None:
        mt5.shutdown()

    #Every query will always be in 'UTC'
    #Therefore our query time will be converted to server time act like 'UTC' to avoid further convertation
    def utc_to_mt5_server_time(self, time_utc: datetime) -> datetime:
        if time_utc.tzinfo is None:
            raise ValueError("time_utc must be in UTC")

        new_york_time = pd.Timestamp(time_utc).tz_convert(PEPPERSTONE_REFERENCE_TIMEZONE)
        server_time = new_york_time.tz_localize(None) + timedelta(hours=PEPPERSTONE_SERVER_SHIFT_HOURS)
        #fake localization (if not localized, then time will be shifted in winter time shift)
        server_time = server_time.tz_localize('utc')

        return server_time.to_pydatetime()

    def mt5_timestamps_to_utc(self, timestamps : pd.Series) -> pd.Series:
        server_time = pd.to_datetime(timestamps, unit='s')
        new_york_time = server_time - timedelta(hours=PEPPERSTONE_SERVER_SHIFT_HOURS)

        return new_york_time.dt.tz_localize(PEPPERSTONE_REFERENCE_TIMEZONE).dt.tz_convert('utc')

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
        if len(rates) == 0:
            return pd.DataFrame()

        bars = pd.DataFrame(rates)

        #Despite documentation mt5 return server time, so for convenient work 'time' was standardized to 'UTC'
        bars['time'] = self.mt5_timestamps_to_utc(bars['time'])
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

        server_time = pd.Series([rates[0][0]])
        latest_bar_time = self.mt5_timestamps_to_utc(server_time)

        return latest_bar_time.iloc[0]


