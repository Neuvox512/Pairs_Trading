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
    period_start = date(2026, 8,17)
    period_end = date(2026, 8,17)
    timeframe = 'M1'

    # backtest_history = backtest_period(
    #     db,
    #     period_start,
    #     period_end,
    #     timeframe,
    #     3,
    #     2,
    #     0.5,
    #     3,
    #     1,
    #     10,
    #     1,
    #     0.9,
    #     0.75,
    #     0.25,
    #     90,
    #     0.1,
    #     0.05,
    # )
    # backtest_history.to_parquet('backtest.parquet')


    trading_dates = get_trading_dates(period_start, period_end)
    symbols_info = db.load_symbols()
    print(trading_dates)
    for trading_date in trading_dates:

        pairs_parameters = prepare_trading_day(
            db,
            trading_date,
            timeframe,
                10,
                1,
                0.9,
                0.75,
                0.25,
                90,
                0.1,
                0.05,
                3,
                3
        )

        tradable_data = get_tradable_data(db, pairs_parameters, trading_date, timeframe, 90)

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
                3,
                1)

            if not tradable_pair_history.empty:
                plt.plot(tradable_pair_history.time, tradable_pair_history.z_score)
                plt.title(f'{pair.first_symbol} - {pair.second_symbol}')
                plt.show()

    # backtest = pd.read_parquet('backtest.parquet')
    #
    # pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    # pnl_summary = pnl_summary(pnl, 4)
    # print(pnl_summary)