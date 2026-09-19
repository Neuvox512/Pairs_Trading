from datetime import date
import pandas as pd
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_session_bar_range, get_trading_dates
from src.data.timeframes import TIME_FREQUENCIES
from pathlib import Path
from tqdm import tqdm
from matplotlib import pyplot as plt


def filter_symbols_by_liquidity(
        symbols_liquidity_quality : pd.DataFrame,
        min_coverage_pct : float,
        min_tick_volume: float,
        max_spread_pct : float
) -> list[str]:
    filtered_symbols = symbols_liquidity_quality[
        (symbols_liquidity_quality['coverage_pct'] >= min_coverage_pct)
        & (symbols_liquidity_quality['avg_tick_volume'] >= min_tick_volume)
        & (symbols_liquidity_quality['avg_spread_pct'] <= max_spread_pct)
    ]

    return filtered_symbols['symbol'].to_list()


def get_liquidity_params_quantiles(symbols_liquidity_quality : pd.DataFrame) -> pd.DataFrame:
    quality_columns = [
        "avg_tick_volume",
        "coverage_pct",
        "avg_spread_pct",
    ]

    quantiles = symbols_liquidity_quality[quality_columns].quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    quantiles.rename_axis('quantile', inplace=True)

    return quantiles

def show_liquidity_params_distribution(symbols_liquidity_quality : pd.DataFrame) -> None:
    fig, ax = plt.subplots(1,3, figsize = (12,7))
    ax[0].hist(symbols_liquidity_quality['avg_tick_volume'], bins = 50)
    ax[0].set_title('Average daily tick volume')

    ax[1].hist(symbols_liquidity_quality['coverage_pct'], bins = 50)
    ax[1].set_title('Coverage (%)')

    ax[2].hist(symbols_liquidity_quality['avg_spread_pct'], bins = 50)
    ax[2].set_title('Average spread (%)')

    plt.show()


def get_symbols_liquidity_quality(daily_quality : pd.DataFrame, window : int = 5) -> pd.DataFrame:
    rolling_quality = (
        daily_quality
        .sort_values(by=['symbol', 'session_date'])
        .set_index('session_date')
        .groupby('symbol')
        .rolling(window =window)
        .agg(
            avg_tick_volume = ('count_tick_volume', 'mean'),
            coverage_pct = ('coverage_pct', 'mean'),
            avg_spread_pct = ('median_spread_pct', 'mean')
        ).reset_index()
    )
    latest_session_date = rolling_quality['session_date'].max()
    latest_quality = rolling_quality[rolling_quality['session_date'] == latest_session_date].reset_index(drop = True)

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
                 count_tick_volume = ('tick_volume', 'sum')
                 )
            .reset_index()
        )

        quality["session_date"] = session_date
        quality['expected_bars_count'] = expected_bars_count
        quality['coverage_pct'] = 100 * quality['actual_bars_count'] / quality['expected_bars_count']
        daily_quality_results.append(quality)

    daily_quality = pd.concat(daily_quality_results, ignore_index = True)

    #Hard filter for all trading sessions
    session_counts = daily_quality.groupby('symbol').agg(session_count=('session_date', 'nunique'))
    complete_symbols = session_counts[session_counts['session_count'] == len(trading_dates)]
    daily_quality = daily_quality[daily_quality['symbol'].isin(complete_symbols.index)]

    return daily_quality

# db = SQLiteDB(Path("../data/Pepperstone_market_data_(utc).db"))
# db.connect()
# daily_q = historical_symbols_quality(db, 'M1', date(2026, 8, 1), date(2026, 8, 31))
# qual = get_symbols_liquidity_quality(daily_q)
# # qual.to_excel('daily_quality_statistics.xlsx')
# # daily_q.to_excel('daily_q.xlsx')
# # print(get_liquidity_params_quantiles(qual))
# print(filter_symbols_by_liquidity(qual, 98, 2400, 0.08))