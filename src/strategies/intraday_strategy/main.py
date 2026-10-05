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
    period_start = date(2026, 6,1)
    period_end = date(2026, 6,30)
    timeframe = 'M1'

    backtest_history = backtest_period(
        db,
        period_start,
        period_end,
        timeframe,
        2,
        1.5,
        0.5,
        3,
        1,
        10,
        1,
        0.9,
        0.75,
        0.25,
        90,
        0.1,
        0.05,
        1,
        2.5
    )
    #backtest_1: half_lif 3 -> 4, z_acceptable 6-> 3
    #backtest_2: half_life 3 -> 4, z_acceptable 6-> 3, z_entry 2->1.5, z_exit 0.5-> 0
    backtest_history.to_parquet('backtest_6.parquet')

    # backtest = pd.read_parquet('backtest_5.parquet')
    #
    # pnl = calculate_pnl(backtest, period_start, period_end, timeframe, 100)
    # pnl_summary = pnl_summary(pnl, 4)
    # print(pnl_summary)




    # trading_dates = get_trading_dates(period_start, period_end)
    # symbols_info = db.load_symbols()
    #
    # for trading_date in trading_dates:
    #     print('Session: ', trading_date)
    #     pairs_parameters = prepare_trading_day(
    #         db,
    #         trading_date,
    #         timeframe,
    #             10,
    #             1,
    #             0.9,
    #             0.75,
    #             0.25,
    #             90,
    #             0.1,
    #             0.05,
    #             1,
    #             2.5,
    #     )
    #
    #     tradable_data = get_tradable_data(db, pairs_parameters, trading_date, timeframe, 90)
    #
    #     for pair in pairs_parameters.itertuples():
    #         tradable_pairs_data = tradable_data[
    #             (tradable_data['symbol_1'] == pair.first_symbol) & (tradable_data['symbol_2'] == pair.second_symbol)
    #             ]
    #
    #         tradable_pair_history = simulate_trades(
    #             tradable_pairs_data,
    #             timeframe,
    #             symbols_info,
    #             pair.hedge_ratio,
    #             pair.half_life_minutes,
    #             3,
    #             1.5,
    #             0.5,
    #             3,
    #             1)
    #
    #         if not tradable_pair_history.empty:
    #             plt.plot(tradable_pair_history.time, tradable_pair_history.z_score)
    #             plt.title(f'{pair.first_symbol} - {pair.second_symbol}')
    #             plt.show()
    #         print(tradable_pair_history)
    #         # pnl = calculate_pnl(tradable_pair_history, period_start, period_end, timeframe, 100)
    #         # print(pnl)
    #         # pnl = pnl_summary(pnl, 4)
    #         # print(pnl)