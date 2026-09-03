from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
from pandas import to_datetime
from pygments.formatters import terminal


class MT5Terminal:
    def connect(self) -> None:
        if not mt5.initialize():
            raise RuntimeError('Could not connect to MT5 {mt5.last_error()}')

    def close(self) -> None:
        mt5.shutdown()

    def fetch_bars(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_time, end_time)

        if rates is None:
            raise RuntimeError('Could not fetch rates for {symbol}: {mt5.last_error()}')

        bars = pd.DataFrame(rates)
        bars['time'] = pd.to_datetime(bars['time'], unit='s', utc=True)

        return bars

terminal = MT5Terminal()
terminal.connect()
print(terminal.fetch_bars('JPM',
                          start_time=datetime(2026, 2, 9, 16, 30),
                          end_time=datetime(2026, 2, 9, 17, 30)))
