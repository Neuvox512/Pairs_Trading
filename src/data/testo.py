from datetime import date
from pathlib import Path
from time import perf_counter

from src.analysis.liquidity_filtration import (
    get_historical_symbols_quality,
    get_symbols_liquidity_quality,
    get_liquidity_params_quantiles,
    filter_symbols_by_liquidity,
)
from src.analysis.pairs_selection import (
    historical_screening,
    historical_screening_summary,
    select_stable_pairs,
)
from src.config import SQLITE_DB_PATH
from src.data.sqlite_db import SQLiteDB


def main() -> None:
    timeframe = "M1"
    database = SQLiteDB(Path(SQLITE_DB_PATH))

    liquidity_start_date = date(2026, 2, 27)
    liquidity_end_date = date(2026, 3, 27)

    cointegration_start_date = date(2026, 3, 30)
    cointegration_end_date = date(2026, 4, 3)

    start_time = perf_counter()

    # 1. Получаем дневную статистику качества за август.
    daily_quality = get_historical_symbols_quality(db=database, timeframe=timeframe, start_date=liquidity_start_date,
                                                   end_date=liquidity_end_date)

    # 2. Рассчитываем показатели за последние 5 сессий августа.
    liquidity_quality = get_symbols_liquidity_quality(
        daily_quality=daily_quality,
        window=5,
    )

    # 3. Смотрим распределение новых показателей.
    quantiles = get_liquidity_params_quantiles(
        liquidity_quality
    )

    print("Квантили показателей ликвидности:")
    print(quantiles)

    # После перехода на median_tick_volume используем его медиану.
    min_tick_volume = quantiles.loc[
        0.9,
        "avg_tick_volume",
    ]

    # 4. Фильтруем символы.
    selected_symbols = filter_symbols_by_liquidity(
        symbols_liquidity_quality=liquidity_quality,
        min_coverage_pct=99,
        min_tick_volume=min_tick_volume,
        max_spread_pct=0.05,
    )

    print("\nКоличество инструментов до фильтрации:",
          len(liquidity_quality))
    print("Количество инструментов после фильтрации:",
          len(selected_symbols))
    print("Минимальный median tick volume:",
          min_tick_volume)

    if len(selected_symbols) < 2:
        raise RuntimeError(
            "После фильтрации осталось меньше двух символов"
        )

    possible_pairs_count = (
        len(selected_symbols)
        * (len(selected_symbols) - 1)
        // 2
    )

    print("Максимальное количество пар:",
          possible_pairs_count)
    print("\nОтобранные символы:")
    print(selected_symbols)

    filtration_time = perf_counter() - start_time

    # 5. Проверяем отобранные символы на следующих сессиях.
    cointegration_start_time = perf_counter()

    historical_results = historical_screening(
        db=database,
        symbols=selected_symbols,
        timeframe=timeframe,
        start_date=cointegration_start_date,
        end_date=cointegration_end_date,
    )

    pairs_summary = historical_screening_summary(
        historical_results
    )

    stable_pairs = select_stable_pairs(
        pairs_summary=pairs_summary,
        min_test_sessions=2,
        min_persistence=0.8,
    )

    cointegration_time = (
        perf_counter() - cointegration_start_time
    )

    print("\nИсторических результатов:",
          len(historical_results))

    print("\nЛучшие пары:")
    print(
        pairs_summary
        .sort_values(
            "persistence",
            ascending=False,
        )
        .head(20)
    )

    print("\nСтабильные пары:")
    print(stable_pairs)

    print(
        "\nВремя фильтрации:",
        round(filtration_time, 2),
        "секунд",
    )

    print(
        "Время проверки коинтеграции:",
        round(cointegration_time, 2),
        "секунд",
    )


if __name__ == "__main__":
    main()