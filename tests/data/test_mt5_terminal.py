from src.data.mt5_terminal import MT5Terminal
from datetime import datetime, timezone


def test_fetch_bars_from_mt5() -> None:
    terminal = MT5Terminal()
    terminal.connect()

    bars = terminal.fetch_bars(
        symbol = "JPM.US",
        timeframe = "M1",
        start_time = datetime(2026, 2, 9, 14,30),
        end_time = datetime(2026, 2, 9, 14,35)
    )

    assert not bars.empty