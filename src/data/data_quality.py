from datetime import date
import pandas as pd
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_session_bar_range, get_trading_dates
from src.data.timeframes import TIME_FREQUENCIES
from pathlib import Path
from tqdm import tqdm
from time import perf_counter



def get_daily_quality_statistics(daily_quality : pd.DataFrame) -> pd.DataFrame:
    rolling_quality = (
        daily_quality
        .sort_values(by=['symbol', 'session_date'])
        .groupby('symbol')
        .rolling(window =5)
        .agg(
            avg_tick_volume = ('count_tick_volume', 'mean'),
            coverage_pct = ('coverage_pct', 'median'),
            avg_spread_pct = ('median_spread_pct', 'mean')
        ).reset_index()
    )
    latest_session_date = rolling_quality['session_date'].max()
    latest_quality = rolling_quality[rolling_quality['session_date'] == latest_session_date].reset_index()

    return latest_quality

def historical_symbols_quality(db : SQLiteDB, timeframe : str, start_date : date, end_date : date) -> None | pd.DataFrame:
    daily_quality_results = []
    trading_dates = get_trading_dates(start_date, end_date)

    for session_date in tqdm(trading_dates):
        session_bar_range = get_session_bar_range(session_date, timeframe)
        if session_bar_range is None:
            print("No session in this date")
            return None

        start_time, end_time = session_bar_range
        bars = db.load_quality_data(timeframe, start_time, end_time)
        bars['spread_pct'] = 100 * bars['spread'] * bars['point']/bars['close']
        bars = bars.drop(columns='spread')
        expected_bars_count = len(pd.date_range(start=start_time, end=end_time, freq=TIME_FREQUENCIES[timeframe]))

        quality = (
            bars.groupby('symbol')
            .agg(actual_bars_count = ('time_utc', 'count'),
                 median_close = ('close', 'median'),
                 median_spread_pct = ('spread_pct', 'median'),
                 count_tick_volume = ('tick_volume', 'count')
                 )
            .reset_index()
        )

        quality["session_date"] = session_date
        quality['expected_bars_count'] = expected_bars_count
        quality['coverage_pct'] = 100 * quality['actual_bars_count'] / quality['expected_bars_count']
        daily_quality_results.append(quality)

    daily_quality = pd.concat(daily_quality_results, ignore_index = True)
    daily_quality = daily_quality.sort_values(['symbol', 'session_date']).set_index(['session_date'])

    return daily_quality

db = SQLiteDB(Path("Pepperstone_market_data_(utc).db"))
db.connect()
start_time = perf_counter()
daily_q = historical_symbols_quality(db, 'M1', date(2026, 8, 1), date(2026, 8, 31))
qual = get_daily_quality_statistics(daily_q)
qual.to_excel('daily_quality_statistics.xlsx')

