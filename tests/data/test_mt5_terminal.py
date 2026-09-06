from src.data.acquisition.mt5_terminal import MT5Terminal
from datetime import datetime, timezone


def test_fetch_bars_from_mt5() -> None:
    terminal = MT5Terminal()
    terminal.connect()

    bars = terminal.fetch_bars(symbol = "JPM",
                        timeframe = "M1",
                        start_time = datetime(2026, 2, 9, 16,30, tzinfo = timezone.utc),
                        end_time = datetime(2026, 2, 9, 16,31, tzinfo = timezone.utc),
                        )

    assert not bars.empty