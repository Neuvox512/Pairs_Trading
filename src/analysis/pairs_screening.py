from datetime import datetime

import pandas as pd

from src.analysis.cointegration import *
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import *


def screen_pairs(close_prices : pd.DataFrame) -> pd.DataFrame:
    i1_symbols = select_i1_symbols(close_prices)

    coint_pairs = calculate_pair_p_values(close_prices, i1_symbols)

    corrected_coint_pairs = bh_correction(coint_pairs)

    return corrected_coint_pairs


def screen_historical_sessions(
        db : SQLiteDB,
        symbols : list[str],
        timeframe, start_date : datetime,
        end_date : datetime) -> pd.DataFrame:
    trading_dates = get_trading_dates(start_date, end_date)
    historical_data = []

    for session_date in trading_dates:
        close_prices = get_session_prices(db, symbols, timeframe, session_date)
        coint_results = screen_pairs(close_prices)
        coint_results.insert(0, 'session_date', session_date)
        historical_data.append(coint_results)

    return pd.concat(historical_data, ignore_index=True)


