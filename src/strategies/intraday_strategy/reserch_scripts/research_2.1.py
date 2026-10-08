from datetime import date
from src.data.sqlite_db import SQLiteDB
from src.config import SQLITE_DB_PATH
from pathlib import Path
import pandas as pd
from src.strategies.intraday_strategy.backtest_tools import pnl_summary, backtest_period, calculate_pnl
from src.strategies.intraday_strategy.backtest_tools import *

if __name__ == '__main__':
    path = SQLITE_DB_PATH
    db = SQLiteDB(Path(path))
    period_start = date(2025, 11,18)
    period_end = date(2025, 11,18)
    timeframe = 'M1'

    trading_dates = get_trading_dates(period_start, period_end)
    symbols_info = db.load_symbols()

    for trading_date in trading_dates:
        print('Session: ', trading_date)
        pairs_parameters = prepare_trading_day(
            db,
            trading_date,
            timeframe,
                10,
                1,
                0.9,
                0.5,
                0.5,
                90,
                0.1,
                0.05,
                0.75,
                2.5,
        )
        pd.set_option('display.max_columns', None)
        print(pairs_parameters)
        tradable_data = get_tradable_data(db, pairs_parameters, trading_date, timeframe, 90)

        pnl = []

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
                3,
                2,
                0.5,
                6,
                1)

            if not tradable_pair_history.empty:
                plt.plot(tradable_pair_history.time, tradable_pair_history.z_score)
                plt.title(f'{pair.first_symbol} - {pair.second_symbol}')
                plt.show()
            print(tradable_pair_history)
            pnl.append(tradable_pair_history['realized_pnl'].iloc[-1])
        print(sum(pnl))

