import pandas as pd
from src.data.sqlite_db import SQLiteDB
from datetime import date
from src.analysis.cointegration import screen_pairs
from src.data.market_session import get_trading_dates, get_session_prices
from tqdm import tqdm


def select_stable_pairs(
        pairs_summary : pd.DataFrame,
        min_test_sessions : int,
        min_persistence : float) -> pd.DataFrame:
    selected_pairs = pairs_summary[
        (pairs_summary['persistence'] >= min_persistence)
        & (pairs_summary['tested_sessions'] >= min_test_sessions)
    ]

    return selected_pairs


def historical_screening_summary(historical_screening : pd.DataFrame) -> pd.DataFrame:
    pairs_summary = historical_screening.groupby(['first_symbol', 'second_symbol'], as_index=False).agg(
        tested_sessions=('session_date', 'nunique'),
        coint_sessions=('reject_no_coint', 'sum')
    )
    pairs_summary['total_sessions'] = historical_screening['session_date'].nunique()
    pairs_summary['persistence'] = (pairs_summary['coint_sessions'] / pairs_summary['total_sessions'])

    return pairs_summary


def historical_screening(
    db : SQLiteDB,
    symbols : list[str],
    timeframe : str,
    start_date : date,
    end_date : date
) -> pd.DataFrame:

    trading_dates = get_trading_dates(start_date, end_date)
    historical_data = []

    for session_date in tqdm(trading_dates):
        close_prices = get_session_prices(db, symbols, timeframe, session_date)
        coint_results = screen_pairs(close_prices)
        coint_results.insert(0, 'session_date', session_date)
        historical_data.append(coint_results)

    return pd.concat(historical_data, ignore_index=True)
