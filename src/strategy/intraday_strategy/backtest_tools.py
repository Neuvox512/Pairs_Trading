from datetime import date
import pandas as pd
from src.analysis.liquidity_filtration import (
    filter_symbols_by_liquidity,
    get_liquidity_params_quantiles)
from src.analysis.pairs_parameters_calculation import calculate_pair_spread, calculate_pair_spread_z_score
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_full_session_bar_range, get_local_session_bar_range, get_session_prices
from src.strategy.intraday_strategy.tools import (
    get_symbols_liquidity,
    get_strat_dates,
    get_global_candidate_pairs,
    confirm_local_candidate_pairs,
    get_pairs_parameters,
    get_local_prices)



def get_tradable_prices(
        db: SQLiteDB,
        pairs_parameters: pd.DataFrame,
        session_date: date,
        timeframe: str,
        opening_minutes: int,
) -> pd.DataFrame:

    symbols = list(set(pairs_parameters['first_symbol'].tolist() + pairs_parameters['second_symbol'].tolist()))

    all_session_prices = get_session_prices(db, symbols, timeframe, session_date)
    local_session_prices = get_local_prices(db, symbols, session_date, timeframe, opening_minutes)
    tradable_session_prices = all_session_prices[all_session_prices.index > local_session_prices]

    if tradable_session_prices.empty:
        return pd.DataFrame()

    results = []
    for pair in pairs_parameters.itertuples():
        pair_spread = calculate_pair_spread(
            tradable_session_prices,
            pair.first_symbol,
            pair.second_symbol,
            timeframe,
            pair.intercept,
            pair.hedge_ratio
        )

        spread_z_score = calculate_pair_spread_z_score(pair_spread, pair.spread_mean, pair.spread_std)

        tradable_pairs_data = pd.DataFrame(
            {
            'symbol_1' : pair.first_symbol,
            'symbol_2' : pair.second_symbol,
            'time' : tradable_session_prices.index,
            'symbol_1_close' : tradable_session_prices[pair.first_symbol],
            'symbol_2_close' : tradable_session_prices[pair.second_symbol],
            'spread' : pair_spread,
            'z_score' : spread_z_score
            }
        )

        results.append(tradable_pairs_data)

    return pd.concat(results, ignore_index=True)


def prepare_trading_day(
        db : SQLiteDB,
        session_date : date,
        timeframe : str,
        min_coverage_quantile : float = 0.9,
        min_tick_volume_quantile : float = 0.9,
        max_spread_quantile : float = 0.1,
) -> pd.DataFrame:

    if get_full_session_bar_range(session_date, timeframe) is None:
        raise ValueError(f'No session in date {session_date}')

    liquidity_dates, coint_dates = get_strat_dates(session_date)
    symbols_liquidity = get_symbols_liquidity(db, timeframe, liquidity_dates[0], liquidity_dates[-1])
    filters = get_liquidity_params_quantiles(symbols_liquidity)
    filtered_symbols = filter_symbols_by_liquidity(
        symbols_liquidity,
        min_coverage_pct=filters.loc[min_coverage_quantile, 'coverage_pct'],
        min_tick_volume=filters.loc[min_tick_volume_quantile, 'avg_tick_volume'],
        max_spread_pct=filters.loc[max_spread_quantile, 'avg_spread_pct']
    )

    if len(filtered_symbols) < 2:
        return pd.DataFrame()

    global_candidate_pairs = get_global_candidate_pairs(db, filtered_symbols, timeframe, coint_dates)

    if global_candidate_pairs.empty:
        return pd.DataFrame()

    confirmed_pairs = confirm_local_candidate_pairs(db, global_candidate_pairs, timeframe, session_date)

    return get_pairs_parameters(db, confirmed_pairs, timeframe, coint_dates)