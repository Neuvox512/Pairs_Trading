from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5


class MT5Terminal:
    def connect(self) -> None:
        if not mt5.initialize():
            raise RuntimeError(f'Could not connect to MT5 {mt5.last_error()}')

    def close(self) -> None:
        mt5.shutdown()

    def fetch_bars(self, symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_time, end_time)

        if rates is None:
            raise RuntimeError(f'Could not fetch rates for {symbol}: {mt5.last_error()}')

        bars = pd.DataFrame(rates)
        bars['time'] = pd.to_datetime(bars['time'], unit='s', utc=True)
        bars = bars.rename(columns={'time': 'time_utc'})

        return bars


if __name__ == "__main__":
    terminal = MT5Terminal()
    terminal.connect()

    try:
        bars = terminal.fetch_bars(
            "JPM",
            start_time=datetime(2026, 2, 9, 17, 30),
            end_time=datetime(2026, 2, 9, 17, 31),
        )
        print(bars.transpose())
    finally:
        terminal.close()