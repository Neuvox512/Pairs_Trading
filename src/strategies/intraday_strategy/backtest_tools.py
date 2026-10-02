from datetime import date
import pandas as pd
from fontTools.misc.fixedTools import floatToFixed

from src.data.timeframes import TIME_FREQUENCIES
from src.analysis.liquidity_filtration import filter_symbols_by_liquidity, get_liquidity_params_quantiles
from src.analysis.pairs_parameters_calculation import calculate_pair_spread, calculate_pair_spread_z_score
from src.data.sqlite_db import SQLiteDB
from src.data.market_session import (
    get_full_session_bar_range,
    get_local_session_bar_range,
    get_session_data,
    get_trading_dates)
from src.strategies.intraday_strategy.general_tools import (
    get_symbols_liquidity,
    get_strat_dates,
    get_global_candidate_pairs,
    confirm_local_candidate_pairs,
    get_pairs_parameters,
    standartize_lot)
from decimal import Decimal
from tqdm import tqdm


def calculcate_pnl(period_history : pd.DataFrame) -> pd.DataFrame:
    result_columns = [
        'session_date', 'time', 'realized_pnl','unrealized_pnl', 'total_pnl'
    ]
    # if sessions.empty:
    #     raise ValueError('No sessions found')

    pnl_history = (
        period_history.groupby(['session_date','time'])
        .agg(unrealized_pnl = ('unrealized_pnl', 'sum'), realized_pnl = ('realized_pnl', 'sum'))
    )

    return pnl_history


def backtest_period(
        db : SQLiteDB,
        start_date : date,
        end_date : date,
        timeframe: str,
        half_life_multiplier: float = 2.0,
        entry_z_score: float = 2.0,
        exit_z_score: float = 0.5,
        acceptable_z_score: float = 4.5,
        base_lot: float = 1.0,
        liquidity_sessions: int = 20,
        coint_sessions: int = 2,
        min_coverage_quantile: float = 0.9,
        min_tick_volume_quantile: float = 0.9,
        max_spread_quantile: float = 0.1,
        opening_minutes: int = 90,
        global_fdr_level: float = 0.1,
        local_fdr_level: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    trading_dates = get_trading_dates(start_date, end_date)
    symbols_info = db.load_symbols()

    sessions = []
    sessions_history = []

    for session in tqdm(trading_dates, desc = 'Backtest sessions'):
        session_bt_history = backtest_session(
            db,
            session,
            timeframe,
            symbols_info,
            half_life_multiplier,
            entry_z_score,
            exit_z_score,
            acceptable_z_score,
            base_lot,
            liquidity_sessions,
            coint_sessions,
            min_coverage_quantile,
            min_tick_volume_quantile,
            max_spread_quantile,
            opening_minutes,
            global_fdr_level,
            local_fdr_level,
        )

        if not session_bt_history.empty:
            sessions_history.append(session_bt_history)

        market_open, last_bar_time = get_full_session_bar_range(session, timeframe)
        market_close = last_bar_time + pd.Timedelta(TIME_FREQUENCIES[timeframe])

        sessions.append(
            {
                "session_date": session,
                "market_open": market_open,
                "market_close": market_close,
                "timeframe": timeframe,
            }
        )

    if sessions_history:
        period_history = pd.concat(sessions_history, ignore_index=True)
        period_history = period_history.sort_values(['session_date', 'time']).reset_index(drop=True)
    else: period_history = pd.DataFrame()

    sessions = pd.DataFrame(sessions, columns=["session_date", "market_open", "market_close", "timeframe"])

    return period_history, sessions


def backtest_session(
        db : SQLiteDB,
        session_date : date,
        timeframe: str,
        symbols_info: pd.DataFrame,
        half_life_multiplier: float = 2.0,
        entry_z_score: float = 2.0,
        exit_z_score: float = 0.5,
        acceptable_z_score: float = 4.5,
        base_lot: float = 1.0,
        liquidity_sessions: int = 20,
        coint_sessions: int = 2,
        min_coverage_quantile: float = 0.9,
        min_tick_volume_quantile: float = 0.9,
        max_spread_quantile: float = 0.1,
        opening_minutes: int = 90,
        global_fdr_level: float = 0.1,
        local_fdr_level: float = 0.05,
) -> pd.DataFrame:

    pairs_parameters = prepare_trading_day(
        db,
        session_date,
        timeframe,
        liquidity_sessions,
        coint_sessions,
        min_coverage_quantile,
        min_tick_volume_quantile,
        max_spread_quantile,
        opening_minutes,
        global_fdr_level,
        local_fdr_level)

    if pairs_parameters.empty:
        return pd.DataFrame()

    tradable_data = get_tradable_data(db,pairs_parameters, session_date, timeframe, opening_minutes)

    if tradable_data.empty:
        raise ValueError(f"No tradable data for selected pairs on {session_date}")

    tradable_pairs_history = []

    for pair in pairs_parameters.itertuples():
        tradable_pairs_data = tradable_data[
            (tradable_data['symbol_1'] == pair.first_symbol) & (tradable_data['symbol_2'] == pair.second_symbol)
        ]

        tradable_pair_history = simulate_trades(
            tradable_pairs_data,
            timeframe,
            symbols_info,
            pair.hedge_ratio,
            pair.half_life_minutes,
            half_life_multiplier,
            entry_z_score,
            exit_z_score,
            acceptable_z_score,
            base_lot)

        if not tradable_pair_history.empty:
            tradable_pairs_history.append(tradable_pair_history)

    if not tradable_pairs_history:
        return pd.DataFrame()

    session_bt_history = pd.concat(tradable_pairs_history, ignore_index=True)
    session_bt_history['session_date'] = session_date
    session_bt_history = session_bt_history.sort_values('time').reset_index(drop = True)

    return session_bt_history


def simulate_trades(
        tradable_pairs_data : pd.DataFrame,
        timeframe : str,
        symbols_info : pd.DataFrame,
        hedge_ratio: float,
        half_life_minutes: float,
        half_life_multiplier: float = 2.0,
        entry_z_score : float = 2.0,
        exit_z_score : float = 0.5,
        acceptable_z_score : float = 4.5,
        base_lot : float = 1.0
) -> pd.DataFrame:

    if tradable_pairs_data.empty:
        return pd.DataFrame()
    if half_life_minutes <= 0:
        raise ValueError (f'Half_time should be positive')
    if not 0 <= exit_z_score < entry_z_score < acceptable_z_score:
        raise ValueError (f'Exit-Z-score should be between 0 and Entry-Z-score'\
                          'Acceptable-Z-score should be greater than Entry-Z-score')
    if half_life_multiplier <= 0:
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
    stop_loss_time = half_life_minutes * half_life_multiplier
    last_bar = len(prices) - 1

    direction = 0
    unrealized_pnl, realized_pnl = 0, 0
    entry_price_1, entry_price_2 = 0, 0
    quantity_1, quantity_2 = 0, 0
    entry_time = None
    trading_enabled = True
    tradable_pair_history = []

    for i in range(len(prices)):
        current_bar = prices.iloc[i]
        current_time = current_bar.time + pd.Timedelta(TIME_FREQUENCIES[timeframe])

        bid_1 = current_bar.symbol_1_close
        ask_1 = bid_1 + current_bar.symbol_1_spread * symbol_1_info.point
        bid_2 = current_bar.symbol_2_close
        ask_2 = bid_2  + current_bar.symbol_2_spread * symbol_2_info.point

        if direction != 0:
            closing_price_1 = bid_1 if quantity_1 < 0 else ask_1
            closing_price_2 = bid_2 if quantity_2 < 0 else ask_2


        if i > 0:
            signal_z_score = prices.iloc[i-1].z_score

            if direction != 0:
                time_passed = (current_time - entry_time).total_seconds()/60

                stop_by_acceptable_z_score = (
                        (direction == 1 and signal_z_score <= -acceptable_z_score)
                        or (direction == -1 and signal_z_score >= acceptable_z_score)
                )

                stop_by_mean_revertion = (
                        (direction == 1 and signal_z_score > -exit_z_score)
                        or (direction == -1 and signal_z_score < exit_z_score)
                )
                time_stop = time_passed >= stop_loss_time
                session_end = i == last_bar

                if stop_by_mean_revertion or stop_by_acceptable_z_score or time_stop or session_end:
                    direction = 0
                    realized_pnl = realized_pnl + ()
                    entry_time = None
                    if stop_by_acceptable_z_score: trading_enabled = False

            elif direction == 0 and trading_enabled and i<last_bar and abs(signal_z_score) < acceptable_z_score:
                if signal_z_score > entry_z_score:
                    direction = -1
                    entry_price_1 = bid_1
                    if hedge_ratio > 0:
                        entry_price_2 = ask_2
                    else: entry_price_2 = bid_2

                elif signal_z_score < -entry_z_score:
                    direction = 1
                    entry_price_1 = ask_1
                    if hedge_ratio > 0:
                        entry_price_2 = bid_2
                    else: entry_price_2 = ask_2

                entry_time = current_time

        quantity_1 = direction * lot_1 * symbol_1_info.contract_size
        if hedge_ratio > 0:
            quantity_2 = -direction * lot_2 * contract_size_2
        else:
            quantity_2 = direction * lot_2 * contract_size_2

        # if quantity_1 < 0 and quantity_2 < 0:
        #     unrealized_pnl = quantity_1 * (entry_price_1 - ask_1) + quantity_2 * (entry_price_2 - ask_2)
        # elif quantity_1 < 0 and quantity_2 > 0:
        #     unrealized_pnl = quantity_1 * (entry_price_1 - ask_1) + quantity_2 * (entry_price_2 - bid_2)
        # elif quantity_1 > 0 and quantity_2 < 0:
        #     unrealized_pnl = quantity_1 * (entry_price_1 - bid_1) + quantity_2 * (entry_price_2 - ask_2)
        # elif quantity_1 > 0 and quantity_2 > 0:
        #     unrealized_pnl = quantity_1 * (entry_price_1 - bid_1) + quantity_2 * (entry_price_2 - bid_2)
        # else: unrealized_pnl = 0

        tradable_pair_history.append(
            {
                "time": current_time,
                "symbol_1": symbol_1,
                "symbol_2": symbol_2,
                "timeframe": timeframe,
                "quantity_1": quantity_1,
                "quantity_2": quantity_2,
                "bid_1": bid_1,
                "ask_1": ask_1,
                "bid_2": bid_2,
                "ask_2": ask_2,
                "z_score": current_bar.z_score,
                "direction": direction,
                "unrealized_pnl" : unrealized_pnl,
                "realized_pnl" : realized_pnl,
            }
        )

    return pd.DataFrame(tradable_pair_history)


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

    session_data = get_session_data(db, symbols, timeframe, session_date)
    local_start, local_end = get_local_session_bar_range(session_date, timeframe, opening_minutes)
    tradable_session_data = session_data[session_data.index > local_end]

    if tradable_session_data.empty:
        return pd.DataFrame()

    results = []
    for pair in pairs_parameters.itertuples():
        pair_spread = calculate_pair_spread(
            tradable_session_data['close'],
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
            'time' : tradable_session_data.index,
            'symbol_1_close' : tradable_session_data['close'][pair.first_symbol],
            'symbol_2_close' : tradable_session_data['close'][pair.second_symbol],
            'symbol_1_spread' : tradable_session_data['spread'][pair.first_symbol],
            'symbol_2_spread': tradable_session_data['spread'][pair.second_symbol],
            'pair_spread' : pair_spread,
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