from datetime import date
import pandas as pd
from src.data.timeframes import TIME_FREQUENCIES
from src.analysis.liquidity_filtration import (
    filter_symbols_by_liquidity,
    get_liquidity_params_quantiles)
from src.analysis.pairs_parameters_calculation import calculate_pair_spread, calculate_pair_spread_z_score
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import get_full_session_bar_range, get_local_session_bar_range, get_session_prices
from src.strategy.intraday_strategy.general_tools import (
    get_symbols_liquidity,
    get_strat_dates,
    get_global_candidate_pairs,
    confirm_local_candidate_pairs,
    get_pairs_parameters,
    standartize_lot)
from decimal import Decimal
from matplotlib import pyplot as plt


def simulate_trades(
        tradable_pairs_data : pd.DataFrame,
        timeframe : str,
        hedge_ratio: float,
        half_time_minutes : float,
        symbols_info : pd.DataFrame,
        half_time_multiplier: float = 2.0,
        entry_z_score : float = 2.0,
        exit_z_score : float = 0.5,
        acceptable_z_score : float = 4.5,
        base_lot : float = 1.0
) -> pd.DataFrame:

    if tradable_pairs_data.empty:
        return pd.DataFrame()
    if half_time_minutes <= 0:
        raise ValueError (f'Half_time should be positive')
    if not 0 <= exit_z_score < entry_z_score < acceptable_z_score:
        raise ValueError (f'Exit-Z-score should be between 0 and Entry-Z-score'\
                          'Acceptable-Z-score should be greater than Entry-Z-score')
    if half_time_multiplier <= 0:
        raise ValueError (f'Holding-multiplier should be positive')

    prices = tradable_pairs_data.sort_values('time').reset_index(drop=True)
    symbol_1 = prices['symbol_1'].iloc[0]
    symbol_2 = prices['symbol_2'].iloc[0]
    symbol_1_info = symbols_info[symbols_info['symbol'] == symbol_1].iloc[0]
    symbol_2_info = symbols_info[symbols_info['symbol'] == symbol_2].iloc[0]
    contract_size_1 = symbol_1_info.contract_size
    contract_size_2 = symbol_2_info.contract_size
    lot_1 = standartize_lot(Decimal(str(base_lot)), symbol_1_info)
    if lot_1 is None:
        return pd.DataFrame()
    lot_2 = standartize_lot(
        Decimal(str(lot_1))
        * abs(Decimal(str(hedge_ratio)))
        * Decimal(str(contract_size_1))/Decimal(str(contract_size_2)),
        symbol_2_info
    )
    if lot_2 is None:
        return pd.DataFrame()
    stop_loss_time = half_time_minutes * half_time_multiplier
    last_bar = len(prices) - 1

    direction = 0
    trades = []
    entry_time = None

    for i in range(1, len(prices)):
        signal_bar = prices.iloc[i-1]
        signal_z_score = signal_bar.z_score
        current_bar = prices.iloc[i]
        # open time + timeframes time = close time
        current_time = current_bar.time + pd.Timedelta(TIME_FREQUENCIES[timeframe])

        if direction == 0:
            if i == last_bar:
                continue

            if abs(signal_z_score) >= acceptable_z_score:
                continue

            if signal_z_score > entry_z_score:
                direction = -1
            elif signal_z_score < -entry_z_score:
                direction = 1
            else: continue

            entry_time = current_time
            entry_price_1 = current_bar.symbol_1_close
            entry_price_2 = current_bar.symbol_2_close
            quantity_1 = direction * lot_1 * symbol_1_info.contract_size
            if hedge_ratio > 0:
                quantity_2 = -direction * lot_2 * symbol_2_info.contract_size
            else:
                quantity_2 = direction * lot_2 * symbol_2_info.contract_size

            continue

        time_passed = (current_time - entry_time).total_seconds() / 60

        if (
            (direction == 1 and signal_z_score <= -acceptable_z_score)
            or
            (direction == -1 and signal_z_score >= acceptable_z_score)
        ):
            exit_reason = 'max_accepted_z_score'

        elif i == last_bar:
            exit_reason = 'session_end'

        elif time_passed >= stop_loss_time:
            exit_reason = 'time_stop_loss'

        elif (
                (direction == 1 and signal_z_score > -exit_z_score)
                or
                (direction == -1 and signal_z_score < exit_z_score)
        ):
            exit_reason = 'mean revertion'

        else: continue

        exit_time = current_time
        exit_price_1 = current_bar.symbol_1_close
        exit_price_2 = current_bar.symbol_2_close
        gross_pnl_1 = quantity_1 * (exit_price_1 - entry_price_1)
        gross_pnl_2 = quantity_2 * (exit_price_2 - entry_price_2)
        gross_pnl = gross_pnl_1 + gross_pnl_2


        trades.append(
            {
                'symbol_1' : current_bar.symbol_1,
                'symbol_2' : current_bar.symbol_2,
                'direction' : direction,
                'entry_time' : entry_time,
                'exit_time' : exit_time,
                'entry_price_1' : entry_price_1,
                'exit_price_1' : exit_price_1,
                'entry_price_2' : entry_price_2,
                'exit_price_2' : exit_price_2,
                'holding_time_(min)' : time_passed,
                'quantity_1' : quantity_1,
                'quantity_2' : quantity_2,
                'gross_pnl_1' : gross_pnl_1,
                'gross_pnl_2' : gross_pnl_2,
                'gross_pnl' : gross_pnl,
                'exit_reason' : exit_reason
            }
        )

        direction = 0
        entry_bar = None
        entry_time = None

        if exit_reason == 'max_accepted_z_score':
            break

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
        global_fdr_level: float = 0.1,
        local_fdr_level : float = 0.05,
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

    global_candidate_pairs = get_global_candidate_pairs(db, filtered_symbols, timeframe, coint_dates, global_fdr_level)

    if global_candidate_pairs.empty:
        return pd.DataFrame()

    confirmed_pairs = confirm_local_candidate_pairs(
        db, global_candidate_pairs, timeframe, session_date, opening_minutes, local_fdr_level)

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
    symbols_info = db.load_symbols()

    results = []
    for i in range(1,29):
        try:
            session_date = date(2026, 7, 30-i)
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
                global_fdr_level= 0.05,
                local_fdr_level=0.05)
            tradable_data = get_tradable_data(db, pairs_parameters, session_date, timeframe, 90)
            # print(tradable_data)

            for row in pairs_parameters.itertuples():
                tradable_pair = tradable_data[tradable_data['symbol_1'].eq(row.first_symbol) & tradable_data['symbol_2'].eq(row.second_symbol)]
                # plt.plot(tradable_pair.time, tradable_pair.z_score)
                # plt.show()
                trades = simulate_trades(
                    tradable_pair,
                    'M1',
                    row.hedge_ratio,
                    row.half_life_minutes,
                    symbols_info,
                    3,
                    2, 0.5, 3.5, 1)
                if not trades.empty:
                    sum_pnl = trades['gross_pnl'].sum()
                    results.append(sum_pnl)
        except Exception as e: print(e)
        print(sum(results))
    total_pnl = sum(results)
    print(total_pnl)


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
