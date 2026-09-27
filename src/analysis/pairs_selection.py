import pandas as pd
from src.data.sqlite_db import SQLiteDB
from datetime import date
from src.analysis.cointegration import screen_global_pairs
from src.data.market_session import get_trading_dates, get_session_prices
from tqdm import tqdm


def select_candidate_pairs(historical_screening : pd.DataFrame, sessions : int = 2) -> pd.DataFrame:
    successful_pairs = historical_screening[historical_screening['reject_no_coint']]

    successful_pairs = (
        successful_pairs.groupby(['first_symbol', 'second_symbol'], as_index=False)
        .agg(sessions_count = ('session_date', 'nunique'))
    )

    candidate_pairs = successful_pairs[successful_pairs['sessions_count'] == sessions]

    return candidate_pairs[['first_symbol', 'second_symbol']].reset_index(drop = True)


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
        coint_results = screen_global_pairs(close_prices)
        coint_results.insert(0, 'session_date', session_date)
        historical_data.append(coint_results)

    return pd.concat(historical_data, ignore_index=True)
