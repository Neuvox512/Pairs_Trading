from datetime import date, datetime, time, timezone
from math import ceil
from pathlib import Path

import MetaTrader5 as mt5
import pandas as pd

from src.data.market_session import get_trading_dates


TERMINAL_PATH = (
    r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
)

TEST_PERIODS = {
    "august_2026": {
        "start_date": date(2026, 8, 1),
        "end_date": date(2026, 8, 31),
    },
    "august_2025": {
        "start_date": date(2025, 8, 1),
        "end_date": date(2025, 8, 31),
    },
}

NUMBER_OF_SESSIONS = 20

OUTPUT_DIRECTORY = Path.cwd()


def create_empty_result(
    period_name: str,
    session_day: date,
    symbol: str,
) -> dict:
    """Создаёт результат для сессии, в которой нет данных."""

    return {
        "period": period_name,
        "session_date": session_day,
        "symbol": symbol,
        "has_data": False,
        "bars": 0,
        "first_bar": pd.NaT,
        "last_bar": pd.NaT,
        "internal_gaps": 0,
        "duplicates": 0,
        "median_spread_bps": float("nan"),
        "p95_spread_bps": float("nan"),
        "median_tick_volume": float("nan"),
    }


# ==========================================================
# 1. Подключение к Pepperstone MT5
# ==========================================================

if not mt5.initialize(path=TERMINAL_PATH):
    raise RuntimeError(
        f"Не удалось подключиться к MT5: {mt5.last_error()}"
    )

account_info = mt5.account_info()
terminal_info = mt5.terminal_info()

if account_info is None:
    raise RuntimeError(
        f"Нет авторизации в MT5: {mt5.last_error()}"
    )

if terminal_info is None:
    raise RuntimeError(
        f"Не удалось получить информацию о терминале: "
        f"{mt5.last_error()}"
    )

print("Сервер:", account_info.server)
print("Максимальное количество баров:", terminal_info.maxbars)

if terminal_info.maxbars < 200_000:
    raise RuntimeError(
        "Лимит истории MT5 слишком маленький. "
        "Установи минимум 200000 баров и перезапусти терминал."
    )


# ==========================================================
# 2. Получаем по 20 торговых сессий для каждого периода
# ==========================================================

period_sessions = {}

for period_name, period_dates in TEST_PERIODS.items():
    trading_dates = get_trading_dates(
        start_date=period_dates["start_date"],
        end_date=period_dates["end_date"],
    )

    session_days = [
        pd.Timestamp(session_date).date()
        for session_date in trading_dates
    ]

    if len(session_days) < NUMBER_OF_SESSIONS:
        raise RuntimeError(
            f"В периоде {period_name} найдено только "
            f"{len(session_days)} торговых сессий"
        )

    # Если в месяце 21 торговая сессия,
    # берём последние 20.
    session_days = session_days[-NUMBER_OF_SESSIONS:]

    period_sessions[period_name] = session_days

    print(
        f"\nПериод: {period_name}"
        f"\nКоличество сессий: {len(session_days)}"
        f"\nПервая сессия: {session_days[0]}"
        f"\nПоследняя сессия: {session_days[-1]}"
    )


# ==========================================================
# 3. Получаем обычные американские акции
# ==========================================================

all_symbols = mt5.symbols_get()

if all_symbols is None:
    raise RuntimeError(
        f"Не удалось получить инструменты: {mt5.last_error()}"
    )

tested_symbols = sorted(
    symbol.name
    for symbol in all_symbols
    if (
        symbol.name.endswith(".US")
        and "\\Stocks\\USA\\" in symbol.path
        and "\\24 Hour\\" not in symbol.path
    )
)

print(
    "\nВсего обычных американских акций:",
    len(tested_symbols),
)


# ==========================================================
# 4. Скачиваем данные
# ==========================================================

daily_results = []
gap_results = []

for period_number, (
    period_name,
    session_days,
) in enumerate(period_sessions.items(), start=1):

    print(
        f"\nПериод {period_number}/{len(period_sessions)}: "
        f"{period_name}"
    )

    # Это серверное время Pepperstone.
    #
    # Оба периода находятся в августе, когда сервер
    # Pepperstone использует GMT+3.
    #
    # В datetime оно помечено как UTC, потому что именно
    # в таком виде терминал принимает серверное время.
    request_start = datetime.combine(
        session_days[0],
        time(16, 30),
    ).replace(tzinfo=timezone.utc)

    request_end = datetime.combine(
        session_days[-1],
        time(23, 0),
    ).replace(tzinfo=timezone.utc)

    for symbol_number, symbol in enumerate(
        tested_symbols,
        start=1,
    ):
        print(
            f"{symbol_number:>3}/{len(tested_symbols)} "
            f"{symbol:<14}",
            end="",
        )

        symbol_selected = mt5.symbol_select(
            symbol,
            True,
        )

        if not symbol_selected:
            print(
                "не удалось выбрать символ:",
                mt5.last_error(),
            )

            for session_day in session_days:
                daily_results.append(
                    create_empty_result(
                        period_name,
                        session_day,
                        symbol,
                    )
                )

            continue

        # Один запрос получает весь период для одной акции.
        rates = mt5.copy_rates_range(
            symbol,
            mt5.TIMEFRAME_M1,
            request_start,
            request_end,
        )

        if rates is None or len(rates) == 0:
            print("данные отсутствуют")

            for session_day in session_days:
                daily_results.append(
                    create_empty_result(
                        period_name,
                        session_day,
                        symbol,
                    )
                )

            continue

        all_bars = pd.DataFrame(rates)

        # Это пока серверное время Pepperstone.
        all_bars["server_time"] = pd.to_datetime(
            all_bars["time"],
            unit="s",
            utc=True,
        )

        all_bars["session_date"] = (
            all_bars["server_time"].dt.date
        )

        # Разделяем общий период на торговые дни.
        bars_by_session = {
            session_date: session_bars
            for session_date, session_bars
            in all_bars.groupby("session_date")
        }

        available_sessions = 0
        symbol_info = mt5.symbol_info(symbol)

        for session_day in session_days:
            session_bars = bars_by_session.get(
                session_day
            )

            if session_bars is None or session_bars.empty:
                daily_results.append(
                    create_empty_result(
                        period_name,
                        session_day,
                        symbol,
                    )
                )

                continue

            available_sessions += 1

            session_bars = (
                session_bars
                .sort_values("server_time")
                .copy()
            )

            duplicate_count = int(
                session_bars["server_time"]
                .duplicated()
                .sum()
            )

            # Убираем дубликаты перед подсчётом свечей.
            session_bars = (
                session_bars
                .drop_duplicates(
                    subset="server_time"
                )
                .reset_index(drop=True)
            )

            bar_times = pd.DatetimeIndex(
                session_bars["server_time"]
            )

            first_bar = bar_times[0]
            last_bar = bar_times[-1]

            expected_inside_session = pd.date_range(
                start=first_bar,
                end=last_bar,
                freq="1min",
            )

            missing_times = (
                expected_inside_session
                .difference(bar_times)
            )

            internal_gaps = len(missing_times)

            # Сохраняем точное время каждого пропуска.
            for missing_time in missing_times:
                gap_results.append(
                    {
                        "period": period_name,
                        "session_date": session_day,
                        "symbol": symbol,
                        "missing_time": missing_time,
                    }
                )

            if symbol_info is None:
                spread_bps = pd.Series(
                    dtype="float64"
                )
            else:
                spread_in_price = (
                    session_bars["spread"]
                    * symbol_info.point
                )

                spread_bps = (
                    spread_in_price
                    / session_bars["close"].where(
                        session_bars["close"] > 0
                    )
                    * 10_000
                )

            daily_results.append(
                {
                    "period": period_name,
                    "session_date": session_day,
                    "symbol": symbol,
                    "has_data": True,
                    "bars": len(session_bars),
                    "first_bar": first_bar,
                    "last_bar": last_bar,
                    "internal_gaps": internal_gaps,
                    "duplicates": duplicate_count,
                    "median_spread_bps": (
                        spread_bps.median()
                    ),
                    "p95_spread_bps": (
                        spread_bps.quantile(0.95)
                    ),
                    "median_tick_volume": (
                        session_bars[
                            "tick_volume"
                        ].median()
                    ),
                }
            )

        print(
            f"сессий с данными: "
            f"{available_sessions}/{len(session_days)}"
        )


# ==========================================================
# 5. Создаём таблицу дневных результатов
# ==========================================================

daily_quality = pd.DataFrame(daily_results)

if daily_quality.empty:
    raise RuntimeError(
        "Не удалось собрать результаты проверки"
    )


# ==========================================================
# 6. Рассчитываем покрытие
# ==========================================================

# Лучшее количество свечей определяется отдельно
# для каждого дня и каждого периода.
daily_quality["best_session_bars"] = (
    daily_quality
    .groupby(
        ["period", "session_date"]
    )["bars"]
    .transform("max")
)

daily_quality["coverage_percent"] = (
    daily_quality["bars"]
    .div(
        daily_quality["best_session_bars"].where(
            daily_quality["best_session_bars"] > 0
        )
    )
    .mul(100)
)


# ==========================================================
# 7. Анализируем общие пропуски
# ==========================================================

if gap_results:
    gap_details = pd.DataFrame(gap_results)

    # Сколько акций имело хотя бы какие-то данные
    # в каждой сессии.
    available_symbols = (
        daily_quality[
            daily_quality["has_data"]
        ]
        .groupby(
            ["period", "session_date"]
        )["symbol"]
        .nunique()
        .rename("symbols_with_data")
        .reset_index()
    )

    # У скольких акций отсутствовала конкретная минута.
    gap_summary = (
        gap_details
        .groupby(
            [
                "period",
                "session_date",
                "missing_time",
            ],
            as_index=False,
        )
        .agg(
            symbols_with_gap=(
                "symbol",
                "nunique",
            )
        )
    )

    gap_summary = gap_summary.merge(
        available_symbols,
        on=["period", "session_date"],
        how="left",
    )

    gap_summary["missing_share_percent"] = (
        gap_summary["symbols_with_gap"]
        / gap_summary["symbols_with_data"]
        * 100
    )

    gap_summary = gap_summary.sort_values(
        by=[
            "missing_share_percent",
            "period",
            "missing_time",
        ],
        ascending=[
            False,
            True,
            True,
        ],
    ).reset_index(drop=True)

    # Общим считаем пропуск, который возник
    # хотя бы у 80% акций.
    common_gaps = gap_summary[
        gap_summary[
            "missing_share_percent"
        ] >= 80
    ].copy()

    print("\nОбщие пропуски:")

    if common_gaps.empty:
        print("Общих пропусков не найдено")
    else:
        print(
            common_gaps.to_string(
                index=False
            )
        )

else:
    gap_details = pd.DataFrame(
        columns=[
            "period",
            "session_date",
            "symbol",
            "missing_time",
        ]
    )

    gap_summary = pd.DataFrame(
        columns=[
            "period",
            "session_date",
            "missing_time",
            "symbols_with_gap",
            "symbols_with_data",
            "missing_share_percent",
        ]
    )

    common_gaps = gap_summary.copy()

    print("\nВнутренних пропусков не найдено")


# ==========================================================
# 8. Собираем сводку по акциям
# ==========================================================

quality_summary = (
    daily_quality
    .groupby(
        ["period", "symbol"],
        as_index=False,
    )
    .agg(
        sessions_checked=(
            "session_date",
            "size",
        ),
        sessions_with_data=(
            "has_data",
            "sum",
        ),
        average_coverage_percent=(
            "coverage_percent",
            "mean",
        ),
        worst_coverage_percent=(
            "coverage_percent",
            "min",
        ),
        sessions_with_99_percent=(
            "coverage_percent",
            lambda values: int(
                (values >= 99).sum()
            ),
        ),
        total_internal_gaps=(
            "internal_gaps",
            "sum",
        ),
        total_duplicates=(
            "duplicates",
            "sum",
        ),
        median_p95_spread_bps=(
            "p95_spread_bps",
            "median",
        ),
        median_tick_volume=(
            "median_tick_volume",
            "median",
        ),
    )
)


# ==========================================================
# 9. Применяем фильтр качества
# ==========================================================

minimum_sessions_with_data = ceil(
    NUMBER_OF_SESSIONS * 0.95
)

minimum_good_sessions = ceil(
    NUMBER_OF_SESSIONS * 0.90
)

quality_summary["passes_filter"] = (
    (
        quality_summary["sessions_with_data"]
        >= minimum_sessions_with_data
    )
    & (
        quality_summary["average_coverage_percent"]
        >= 99
    )
    & (
        quality_summary["sessions_with_99_percent"]
        >= minimum_good_sessions
    )
    & (
        quality_summary["median_p95_spread_bps"]
        <= 10
    )
    & (
        quality_summary["median_tick_volume"]
        >= 10
    )
)

quality_summary = quality_summary.sort_values(
    by=[
        "period",
        "passes_filter",
        "average_coverage_percent",
        "median_p95_spread_bps",
    ],
    ascending=[
        True,
        False,
        False,
        True,
    ],
).reset_index(drop=True)


# ==========================================================
# 10. Показываем результаты каждого периода
# ==========================================================

for period_name in TEST_PERIODS:
    passed_in_period = quality_summary[
        (quality_summary["period"] == period_name)
        & quality_summary["passes_filter"]
    ].copy()

    passed_symbols = (
        passed_in_period["symbol"]
        .sort_values()
        .tolist()
    )

    print(
        f"\nПодходящие акции за {period_name}:",
        len(passed_symbols),
    )

    print(passed_symbols)


# ==========================================================
# 11. Находим акции, прошедшие оба периода
# ==========================================================

passing_period_counts = (
    quality_summary[
        quality_summary["passes_filter"]
    ]
    .groupby("symbol")["period"]
    .nunique()
)

stable_symbols = (
    passing_period_counts[
        passing_period_counts
        == len(TEST_PERIODS)
    ]
    .index
    .sort_values()
    .tolist()
)

stable_quality = quality_summary[
    quality_summary["symbol"].isin(
        stable_symbols
    )
].copy()

stable_quality = stable_quality.sort_values(
    by=["symbol", "period"]
).reset_index(drop=True)

print(
    "\nКоличество акций, прошедших оба периода:",
    len(stable_symbols),
)

print("\nСтабильные акции:")
print(stable_symbols)

print("\nПоказатели стабильных акций:")

if stable_quality.empty:
    print("Нет акций, прошедших оба периода")
else:
    print(
        stable_quality.to_string(
            index=False
        )
    )


# ==========================================================
# 12. Сохраняем результаты
# ==========================================================

daily_quality_path = (
    OUTPUT_DIRECTORY
    / "pepperstone_daily_quality.csv"
)

quality_summary_path = (
    OUTPUT_DIRECTORY
    / "pepperstone_quality_summary.csv"
)

gap_summary_path = (
    OUTPUT_DIRECTORY
    / "pepperstone_gap_summary.csv"
)

stable_symbols_path = (
    OUTPUT_DIRECTORY
    / "pepperstone_stable_symbols.csv"
)

daily_quality.to_csv(
    daily_quality_path,
    index=False,
)

quality_summary.to_csv(
    quality_summary_path,
    index=False,
)

gap_summary.to_csv(
    gap_summary_path,
    index=False,
)

pd.DataFrame(
    {
        "symbol": stable_symbols,
    }
).to_csv(
    stable_symbols_path,
    index=False,
)


print("\nРезультаты сохранены:")

print(daily_quality_path)
print(quality_summary_path)
print(gap_summary_path)
print(stable_symbols_path)


# Терминал намеренно не закрываем.
# mt5.shutdown()