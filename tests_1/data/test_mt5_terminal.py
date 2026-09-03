from src.data.mt5_terminal import MT5Terminal
from datetime import datetime


def test_fetch_bars_from_mt5() -> None:
    terminal = MT5Terminal()
    terminal.connect()

    try:
        bars = terminal.fetch_bars(symbol = "JPM",
                            start_time = datetime(2026, 2, 9, 16,30),
                            end_time = datetime(2026, 2, 9, 17,30),
                            )
        print(bars)
    finally:
        terminal.close()
    assert not bars.empty