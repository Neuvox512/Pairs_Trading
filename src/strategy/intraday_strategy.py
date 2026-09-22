from datetime import date
import pandas as pd
from src.analysis.cointegration import screen_local_pairs
from src.analysis.liquidity_filtration import get_historical_symbols_quality, get_symbols_liquidity_quality
from src.data.sqlite_db import SQLiteDB
from src.analysis.pairs_selection import historical_screening, select_candidate_pairs
from src.data.market_session import get_previous_trading_dates, get_local_session_bar_range


def confirm_local_candidate_pairs (
        db : SQLiteDB,
        candidate_pairs : pd.DataFrame,
        timeframe : str,
        session_date : date,
        opening_minutes : int = 90,
        fdr_level : float = 0.1
):

    candidate_symbols = pd.concat(
            [
                candidate_pairs['first_symbol'],
                candidate_pairs['second_symbol']
            ], ignore_index=True
        ).drop_duplicates().tolist()

    local_prices =get_local_prices(db, candidate_symbols, session_date, timeframe, opening_minutes)
    local_screening = screen_local_pairs(local_prices, candidate_pairs, fdr_level)
    confirmed_pairs = local_screening[local_screening['reject_no_coint']]

    return confirmed_pairs.reset_index(drop=True)


def get_local_prices (
        db : SQLiteDB,
        symbols : list[str],
        session_date : date,
        timeframe : str,
        opening_minutes : int
) -> pd.DataFrame:

    local_start_time, local_end_time = get_local_session_bar_range(session_date, timeframe, opening_minutes)

    local_close_prices = db.load_close_prices(symbols, timeframe, local_start_time, local_end_time)
    local_close_prices = local_close_prices.ffill().dropna()

    return local_close_prices


def get_historical_candidate_pairs(
        db : SQLiteDB,
        symbols : list[str],
        timeframe : str,
        coint_dates : list[date]
) -> pd.DataFrame:

    historical_results = historical_screening(db, symbols, timeframe, coint_dates[0], coint_dates[-1])

    return select_candidate_pairs(historical_results, sessions=len(coint_dates))


def get_liquidity_results(
        db : SQLiteDB,
        timeframe : str,
        start_date : date,
        end_date : date,
        window : int = 5
) -> pd.DataFrame:

    historical_results = get_historical_symbols_quality(db, timeframe, start_date, end_date)

    return get_symbols_liquidity_quality(historical_results, window=window)


def get_strat_dates(
        session_date : date,
        liquidity_sessions : int = 20,
        coint_days : int = 2
) -> tuple[list[date], list[date]]:

    previous_trading_dates = get_previous_trading_dates(session_date, liquidity_sessions + coint_days)

    liquidity_dates = previous_trading_dates[:-coint_days]

    coint_dates = previous_trading_dates[-coint_days:]

    return liquidity_dates, coint_dates

