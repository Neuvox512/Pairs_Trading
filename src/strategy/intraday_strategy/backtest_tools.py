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
    get_pairs_parameters)


def simulate_trades(
        tradable_pairs_data : pd.DataFrame,
        half_time_minutes : float,
        entry_z_score : float = 2.0,
        exit_z_score : float = 0.5,
        half_time_multiplier : float = 2.0
) -> pd.DataFrame:

    if tradable_pairs_data.empty:
        return pd.DataFrame()
    if half_time_minutes <= 0:
        raise ValueError (f'Half_time should be positive')
    if not 0 <= exit_z_score <= entry_z_score:
        raise ValueError (f'Exit-Z-score should be between 0 and Entry-Z-score')
    if half_time_multiplier < 0:
        raise ValueError (f'Holding-multiplier should be positive')

    prices = tradable_pairs_data.sort_values('time').reset_index(drop=True)
    stop_loss_time = half_time_minutes * half_time_multiplier
    last_bar = prices.iloc[-1]

    direction = 0
    trades = []
    entry_time = None

    for i in range(1, len(prices)):
        current_bar = prices.iloc[i]
        current_z_score = current_bar.z_score
        current_time = current_bar.time
        time_passed = (current_time - entry_time).total_seconds() / 60

        if current_bar == last_bar:
            exit_reason = 'session_end'
            exit_time = current_bar.at_time
            break

        elif direction == 0:

            if current_z_score > entry_z_score:
                direction = -1
                entry_time = current_bar.time
                entry_price_1 = current_bar.symbol_1_close
                entry_price_2 = current_bar.symbol_2_close
            elif current_z_score < -entry_z_score:
                direction = 1
                entry_time = current_bar.time
                entry_price_1 = current_bar.symbol_1_close
                entry_price_2 = current_bar.symbol_2_close
            else: continue

        elif time_passed >= stop_loss_time:
            exit_reason = 'time_stop_loss'
            exit_time = current_bar.time
            exit_price_1 = current_bar.symbol_1_close
            exit_price_2 = current_bar.symbol_2_close

        elif (direction == 1 and current_z_score > -exit_z_score
              or direction == -1 and current_z_score < exit_z_score):
            exit_reason = 'mean revertion'
            exit_time = current_bar.time
            exit_price_1 = current_bar.symbol_1_close
            exit_price_2 = current_bar.symbol_2_close

        else: continue

        trades.append(
            {
                'symbol_1' : current_bar.symbol_1,
                'symbol_2' : current_bar.symbol_2,
                'direction' : direction,
                'entry_time' : entry_time,
                'exit_time' : current_time,
                'entry_price_1' : entry_price_1,
                'exit_price_1' : exit_price_1,
                'entry_price_2' : entry_price_2,
                'exit_price_2' : exit_price_2,
                'holding_time_(min)' : time_passed,
                'exit_reason' : exit_reason
            }
        )

        direction = 0
        entry_bar = None
        entry_time = None

        return pd.DataFrame(trades)


def get_tradable_data(
        db: SQLiteDB,
        pairs_parameters: pd.DataFrame,
        session_date: date,
        timeframe: str,
        opening_minutes: int
) -> pd.DataFrame:

    if pairs_parameters.empty:
        return pd.DataFrame()

    symbols = list(set(pairs_parameters['first_symbol'].tolist() + pairs_parameters['second_symbol'].tolist()))

    all_session_prices = get_session_prices(db, symbols, timeframe, session_date)
    local_start, local_end = get_local_session_bar_range(session_date, timeframe, opening_minutes)
    tradable_session_prices = all_session_prices[all_session_prices.index > local_end]

    if tradable_session_prices.empty:
        return pd.DataFrame()

    results = []
    for pair in pairs_parameters.itertuples():
        pair_spread = calculate_pair_spread(
            tradable_session_prices,
            pair.first_symbol,
            pair.second_symbol,
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
        liquidity_sessions: int = 20,
        coint_sessions: int = 2,
        min_coverage_quantile : float = 0.9,
        min_tick_volume_quantile : float = 0.9,
        max_spread_quantile : float = 0.1,
        opening_minutes: int = 90,
) -> pd.DataFrame:

    if get_full_session_bar_range(session_date, timeframe) is None:
        raise ValueError(f'No session in date {session_date}')

    liquidity_dates, coint_dates = get_strat_dates(session_date, liquidity_sessions, coint_sessions)
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

    confirmed_pairs = confirm_local_candidate_pairs(db, global_candidate_pairs, timeframe, session_date, opening_minutes)

    return get_pairs_parameters(db, confirmed_pairs, timeframe, coint_dates)


if __name__ == "__main__":
    from pathlib import Path
    from time import perf_counter
    from src.config import SQLITE_DB_PATH

    db_path = Path(SQLITE_DB_PATH)

    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}")

    count = []
    db = SQLiteDB(db_path)
    session_date = date(2026, 8, 27)
    timeframe = "M1"
    pairs_parameters = prepare_trading_day(
                db=db,
                session_date=session_date,
                timeframe=timeframe,
                liquidity_sessions=10,
                coint_sessions=1,
                min_coverage_quantile=0.75,
                min_tick_volume_quantile=0.75,
                max_spread_quantile=0.25,
            )
    tradable_data = get_tradable_data(db, pairs_parameters, session_date, timeframe, 90)
    tradable_pair = tradable_data[tradable_data['symbol_1'].eq('ACWI.US') & tradable_data['symbol_2'].eq('ORCL.US')]
    raw = tradable_pair.iloc[0]
    trades = simulate_trades(tradable_pair, 20, 2, 0.5, 2)
    print(trades)

    # for i in range(1,30):
    #     try:
    #         session_date = date(2026, 3, 31-i)
    #         timeframe = "M1"
    #
    #         liquidity_dates, coint_dates = get_strat_dates(session_date, liquidity_sessions=10, coint_days=1)
    #
    #         print("Торговая дата:", session_date)
    #         print("Таймфрейм:", timeframe)
    #         print(
    #             "Период оценки ликвидности:",
    #             liquidity_dates[0],
    #             "—",
    #             liquidity_dates[-1],
    #         )
    #         print("Сессий для ликвидности:", len(liquidity_dates))
    #         print("Сессии для коинтеграции:", coint_dates)
    #         print("Утреннее подтверждение: первые 90 минут")
    #
    #         start = perf_counter()
    #
    #         pairs_parameters = prepare_trading_day(
    #             db=db,
    #             session_date=session_date,
    #             timeframe=timeframe,
    #             liquidity_sessions=10,
    #             coint_sessions=1,
    #             min_coverage_quantile=0.75,
    #             min_tick_volume_quantile=0.75,
    #             max_spread_quantile=0.25,
    #         )
    #
    #         print("\nИтоговых пар:", len(pairs_parameters))
    #
    #         if pairs_parameters.empty:
    #             print("На выбранную дату подходящих пар нет.")
    #         else:
    #             print(pairs_parameters.to_string(index=False))
    #             count.append(pairs_parameters)
    #
    #         print(f"\nВремя выполнения: {perf_counter() - start:.2f} секунд")
    #     except:
    #         print (f'Выходной в {session_date}')
    #
    # print (len(count))
    # print(pd.concat(count))
