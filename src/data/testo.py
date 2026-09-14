from datetime import date
from pathlib import Path
from time import perf_counter
from src.Data_Analysis import Coint_pairs
from src.Data_Analysis.Coint_pairs import coint_pairs_1
from src.analysis.pairs_selection import (
    historical_screening,
    historical_screening_summary,
    select_stable_pairs,
)
from src.data.sqlite_db import SQLiteDB


db = SQLiteDB(Path("RoboForex_market_data_(utc).db"))

symbols = ['GOOGL', 'MSFT', 'IBM', 'VZ', 'INTC', 'HPE', 'EA', 'ORCL', 'NVDA', 'CSCO', 'ADBE', 'TSLA',
               'CMCSA', 'DIS', 'FOXA', 'AMZN', 'UPS', 'NFLX', 'MCD', 'SBUX', 'EBAY', 'WMT', 'DAL', 'XOM',
               'CVX', 'NEM', 'JPM', 'BAC', 'C', 'WFC', 'V', 'GS', 'PYPL', 'PRU', 'BRK.B', 'AAPL', 'KO',
               'PEP', 'PG', 'PM', 'NKE', 'GM', 'GE', 'MMM', 'CAT', 'BA', 'JNJ', 'PFE', 'LLY', 'META']

start = perf_counter()

historical_results = historical_screening(
    db=db,
    symbols=symbols,
    timeframe="M1",
    start_date=date(2026, 9, 2),
    end_date=date(2026, 9, 4)
)

pairs_summary = historical_screening_summary(historical_results)

stable_pairs = select_stable_pairs(
    pairs_summary=pairs_summary,
    min_test_sessions=2,
    min_persistence=0.8,
)

elapsed_seconds = perf_counter() - start

print("Исторических результатов:", len(historical_results))
print("\nСводка:")
print(
    pairs_summary
    .sort_values("persistence", ascending=False)
    .head(10)
)

print("\nСтабильные пары:")
print(stable_pairs)

print("\nВремя выполнения:", round(elapsed_seconds, 2), "секунд")