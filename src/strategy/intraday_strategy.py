from datetime import date
import pandas as pd
from src.analysis.cointegration import screen_local_pairs
from src.analysis.liquidity_filtration import (
    get_historical_symbols_quality,
    filter_symbols_by_liquidity,
    get_liquidity_params_quantiles,
    get_symbols_liquidity_quality)
from src.data.sqlite_db import SQLiteDB
from src.analysis.pairs_selection import historical_screening, select_candidate_pairs
from src.data.market_session import get_previous_trading_dates, get_local_session_bar_range
from src.analysis.pairs_parameters_calculation import calculate_pairs_parameters
from src.data.market_session import get_session_prices


def prepare_trading_day(
        db : SQLiteDB,
        session_date : date,
        timeframe : str,
        liquidity_quantile : float,
) -> pd.DataFrame:

    liquidity_dates, coint_dates = get_strat_dates(session_date)
    symbols_liquidity = get_symbols_liquidity(db, timeframe, liquidity_dates[0], liquidity_dates[-1])
    filters = get_liquidity_params_quantiles(symbols_liquidity)
    filtered_symbols = filter_symbols_by_liquidity(
        symbols_liquidity,
        min_coverage_pct=filters.loc[f'{liquidity_quantile}', 'coverage_pct'],
        min_tick_volume=filters.loc[f'{liquidity_quantile}', 'avg_tick_volume'],
        max_spread_pct=filters.loc[f'{liquidity_quantile}', 'avg_spread_pct']
    )

    if len(filtered_symbols) < 2:
        return pd.DataFrame()

    global_candidate_pairs = get_global_candidate_pairs(db, filtered_symbols, timeframe, coint_dates)

    confirmed_pairs = confirm_local_candidate_pairs(db, global_candidate_pairs, timeframe, session_date)

    return get_pairs_parameters(db, confirmed_pairs, timeframe, coint_dates)


def get_pairs_parameters(
        db : SQLiteDB,
        confirmed_pairs : pd.DataFrame,
        timeframe : str,
        coint_dates : list[date],
) -> pd.DataFrame:

    if confirmed_pairs.empty:
        return pd.DataFrame()

    confirmed_symbols = list(set(confirmed_pairs['first_symbol'].tolist() + confirmed_pairs['second_symbol'].tolist()))
    history = []

    for session in coint_dates:
        session_prices = get_session_prices(db, confirmed_symbols, timeframe, session)
        history.append(session_prices)

    historical_prices = pd.concat(history)

    parameters = calculate_pairs_parameters(historical_prices, confirmed_pairs, timeframe)

    return parameters


def confirm_local_candidate_pairs (
        db : SQLiteDB,
        candidate_pairs : pd.DataFrame,
        timeframe : str,
        session_date : date,
        opening_minutes : int = 90,
        fdr_level : float = 0.1
) -> pd.DataFrame:

    candidate_symbols = list(set(candidate_pairs['first_symbol'].tolist() + candidate_pairs['second_symbol'].tolist()))

    local_prices = get_local_prices(db, candidate_symbols, session_date, timeframe, opening_minutes)
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


def get_global_candidate_pairs(
        db : SQLiteDB,
        symbols : list[str],
        timeframe : str,
        coint_dates : list[date]
) -> pd.DataFrame:

    historical_results = historical_screening(db, symbols, timeframe, coint_dates[0], coint_dates[-1])

    if historical_results.empty:
        return pd.DataFrame()

    return select_candidate_pairs(historical_results, sessions=len(coint_dates))


def get_symbols_liquidity(
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

