from datetime import datetime, timezone

import MetaTrader5 as mt5
import pandas as pd


TERMINAL_PATH = (
    r"C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe"
)

SYMBOL = "AAPL.US"

TEST_DATES = [
    datetime(2026, 3, 13, tzinfo=timezone.utc),
    datetime(2026, 10, 30, tzinfo=timezone.utc),
]


if not mt5.initialize(path=TERMINAL_PATH):
    raise RuntimeError(
        f"Ошибка подключения: {mt5.last_error()}"
    )

if not mt5.symbol_select(SYMBOL, True):
    raise RuntimeError(
        f"Не удалось выбрать {SYMBOL}: "
        f"{mt5.last_error()}"
    )


for test_date in TEST_DATES:
    # Берём широкий диапазон, включающий оба
    # возможных времени открытия: 15:31 и 16:31.
    request_start = test_date.replace(
        hour=14,
        minute=0,
    )

    request_end = test_date.replace(
        hour=18,
        minute=0,
    )

    rates = mt5.copy_rates_range(
        SYMBOL,
        mt5.TIMEFRAME_M1,
        request_start,
        request_end,
    )

    print("\nДата:", test_date.date())

    if rates is None:
        print("Ошибка MT5:", mt5.last_error())
        continue

    if len(rates) == 0:
        print("Свечи отсутствуют")
        continue

    bars = pd.DataFrame(rates)

    bars["raw_server_time"] = pd.to_datetime(
        bars["time"],
        unit="s",
        utc=True,
    )

    print("Количество свечей:", len(bars))
    print(
        "Первая свеча:",
        bars["raw_server_time"].iloc[0],
    )
    print(
        "Последняя свеча:",
        bars["raw_server_time"].iloc[-1],
    )

    print(
        bars[
            [
                "raw_server_time",
                "open",
                "close",
            ]
        ].head()
    )


# Терминал не закрываем.
# mt5.shutdown()