from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.config import SQLITE_DB_PATH
from src.data.sqlite_db import SQLiteDB
from src.data.timeframes import TIME_FREQUENCIES
from src.data.market_session import (
    get_previous_trading_dates,
    get_local_session_bar_range,
    get_session_data,
)
from src.strategies.intraday_strategy.general_tools import (
    get_global_pairs_parameters,
    get_local_prices,
)
from src.analysis.pairs_parameters_calculation import (
    calculate_pair_spread,
    calculate_pair_spread_z_score,
)


SESSION_DATE = date(2026, 8, 17)
TIMEFRAME = "M1"
COINT_SESSIONS = 1
OPENING_MINUTES = 90

# Пока только для диагностики, а не для отбора.
EXTREME_Z = 4.5

PAIRS = [
    ("ADBE.US", "SO.US"),
    ("ARKK.US", "CTSH.US"),
    ("ARKK.US", "IREN.US"),
    ("AVGO.US", "TSM.US"),
    ("CTSH.US", "USO.US"),
    ("NOW.US", "SOXX.US"),
]


if __name__ == "__main__":
    db = SQLiteDB(Path(SQLITE_DB_PATH))

    pairs = pd.DataFrame(
        PAIRS,
        columns=["first_symbol", "second_symbol"],
    )

    symbols = sorted({
        symbol
        for pair in PAIRS
        for symbol in pair
    })

    historical_dates = get_previous_trading_dates(
        SESSION_DATE,
        COINT_SESSIONS,
    )

    print("Исследуемая сессия:", SESSION_DATE)
    print("Исторические сессии:", historical_dates)
    print("Таймфрейм:", TIMEFRAME)
    print("Утреннее окно, минут:", OPENING_MINUTES)

    # Параметры оцениваются только на прошлых сессиях.
    parameters = get_global_pairs_parameters(db=db, confirmed_pairs=pairs, timeframe=TIMEFRAME,
                                             coint_dates=historical_dates)

    # Здесь загружаются только первые OPENING_MINUTES минут.
    morning_prices = get_local_prices(
        db=db,
        symbols=symbols,
        session_date=SESSION_DATE,
        timeframe=TIMEFRAME,
        opening_minutes=OPENING_MINUTES,
    )

    if morning_prices.empty:
        raise ValueError("Нет утренних данных для выбранных инструментов")

    market_open, last_morning_bar = get_local_session_bar_range(
        SESSION_DATE,
        TIMEFRAME,
        OPENING_MINUTES,
    )

    bar_duration = pd.Timedelta(TIME_FREQUENCIES[TIMEFRAME])
    decision_time = last_morning_bar + bar_duration
    expected_morning_bars = int(
        pd.Timedelta(minutes=OPENING_MINUTES) / bar_duration
    )

    results = []

    for pair in parameters.itertuples(index=False):
        if not np.isfinite(pair.spread_std) or pair.spread_std <= 0:
            raise ValueError(
                f"Некорректный spread_std: "
                f"{pair.first_symbol} — {pair.second_symbol}"
            )

        morning_spread = calculate_pair_spread(
            morning_prices,
            pair.first_symbol,
            pair.second_symbol,
            pair.intercept,
            pair.hedge_ratio,
        )

        morning_z = calculate_pair_spread_z_score(
            morning_spread,
            pair.spread_mean,
            pair.spread_std,
        )

        # Убираем точные нули, чтобы касание нуля без смены
        # стороны не считалось пересечением.
        nonzero_z = morning_z[morning_z != 0]
        zero_crossings = (
            nonzero_z * nonzero_z.shift(1) < 0
        ).sum()

        results.append({
            "first_symbol": pair.first_symbol,
            "second_symbol": pair.second_symbol,
            "historical_intercept": pair.intercept,
            "historical_hedge_ratio": pair.hedge_ratio,
            "historical_spread_mean": pair.spread_mean,
            "historical_spread_std": pair.spread_std,
            "historical_half_life_minutes": pair.half_life_minutes,
            "morning_bars": len(morning_z),
            "expected_morning_bars": expected_morning_bars,
            "first_morning_z": morning_z.iloc[0],
            "last_morning_z": morning_z.iloc[-1],
            "morning_z_mean": morning_z.mean(),
            "morning_z_std": morning_z.std(),
            "morning_z_min": morning_z.min(),
            "morning_z_max": morning_z.max(),
            "morning_z_change": morning_z.iloc[-1] - morning_z.iloc[0],
            "zero_crossings": int(zero_crossings),
            "extreme_bars_pct": 100 * (
                morning_z.abs() >= EXTREME_Z
            ).mean(),
        })

    diagnostics = pd.DataFrame(results)

    display_columns = [
        "first_symbol",
        "second_symbol",
        "historical_spread_std",
        "morning_z_mean",
        "morning_z_std",
        "first_morning_z",
        "last_morning_z",
        "morning_z_change",
        "zero_crossings",
        "extreme_bars_pct",
    ]

    print("\nУтренние показатели по исторической модели:")
    print(
        diagnostics[display_columns]
        .round(3)
        .to_string(index=False)
    )

    print(
        "\nУтренних баров после подготовки:",
        len(morning_prices),
        "/",
        expected_morning_bars,
    )
    print("Момент принятия решения, UTC:", decision_time)

    # Полная сессия загружается отдельно и используется
    # только для визуального сравнения с будущим движением.
    session_data = get_session_data(
        db,
        symbols,
        TIMEFRAME,
        SESSION_DATE,
    )

    if session_data.empty:
        raise ValueError("Нет данных полной сессии")

    session_prices = session_data["close"]

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(15, 11),
        sharex=True,
    )

    for ax, pair in zip(axes.flat, parameters.itertuples(index=False)):
        session_spread = calculate_pair_spread(
            session_prices,
            pair.first_symbol,
            pair.second_symbol,
            pair.intercept,
            pair.hedge_ratio,
        )

        session_z = calculate_pair_spread_z_score(
            session_spread,
            pair.spread_mean,
            pair.spread_std,
        )

        # На графике указываем момент, когда close уже известен.
        bar_close_times = session_z.index + bar_duration
        morning_mask = bar_close_times <= decision_time

        ax.plot(
            bar_close_times[morning_mask],
            session_z[morning_mask],
            color="tab:blue",
            label="Morning: available at decision",
        )

        ax.plot(
            bar_close_times[~morning_mask],
            session_z[~morning_mask],
            color="tab:orange",
            label="Later: diagnostic only",
        )

        ax.axvspan(
            market_open,
            decision_time,
            color="tab:blue",
            alpha=0.08,
        )
        ax.axvline(decision_time, color="black", linestyle="--")
        ax.axhline(0, color="gray", linewidth=1)

        ax.axhline(
            EXTREME_Z,
            color="red",
            linestyle=":",
            linewidth=1,
        )
        ax.axhline(
            -EXTREME_Z,
            color="red",
            linestyle=":",
            linewidth=1,
        )

        ax.set_title(f"{pair.first_symbol} — {pair.second_symbol}")
        ax.set_ylabel("Historical-model z-score")
        ax.set_xlabel("UTC, bar close time")
        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%H:%M", tz="UTC")
        )
        ax.grid(alpha=0.25)

    axes.flat[0].legend(fontsize=8)

    fig.suptitle(
        f"{SESSION_DATE} | {TIMEFRAME} | "
        f"Historical sessions: {COINT_SESSIONS}",
        fontsize=14,
    )

    plt.tight_layout()
    plt.show()