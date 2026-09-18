from datetime import date
import pandas as pd
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_session_bar_range, get_trading_dates
from src.data.timeframes import TIME_FREQUENCIES
from pathlib import Path
from tqdm import tqdm
from time import perf_counter
from matplotlib import pyplot as plt


def get_daily_quality_statistics(daily_quality : pd.DataFrame) -> None:
    fig, axes = plt.subplots(1,3, figsize = (12,7))
    axes[0].boxplot(daily_quality['coverage_pct'])
    axes[0].set_title('Data Coverage (%)')
    coverage_pct_medain = daily_quality['coverage_pct'].median()
    axes[0].annotate(f'Median:{coverage_pct_medain:.2f}', xy=(1.1, coverage_pct_medain))

    axes[1].boxplot(daily_quality['median_tick_volume'])
    axes[1].set_title('Median Tick Volume')
    median_tick_volume_median = daily_quality['median_tick_volume'].median()
    axes[1].annotate(f'Median:{median_tick_volume_median:.2f}', xy=(1.1, median_tick_volume_median))

    axes[2].boxplot(daily_quality['median_spread_pct'])
    axes[2].set_title('Spread (%)')
    median_spread_pct_medain = daily_quality['median_spread_pct'].median()
    axes[2].annotate(f'Median:{median_spread_pct_medain:.2f}', xy=(1.1, median_spread_pct_medain))

    plt.show()

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
                 median_tick_volume = ('tick_volume', 'median')
                 )
            .reset_index()
        )

        quality["session_date"] = session_date
        quality['expected_bars_count'] = expected_bars_count
        quality['coverage_pct'] = 100 * quality['actual_bars_count'] / quality['expected_bars_count']
        daily_quality_results.append(quality)

    daily_quality = pd.concat(daily_quality_results, ignore_index = True)

    return daily_quality

db = SQLiteDB(Path("Pepperstone_market_data_(utc).db"))
db.connect()
start_time = perf_counter()
daily_q = historical_symbols_quality(db, 'M1', date(2026, 8, 1), date(2026, 8, 31))
get_daily_quality_statistics(daily_q)
