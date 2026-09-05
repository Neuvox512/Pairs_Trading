import pytest
import pandas as pd
from src.data.sqlite_db import SQLiteDB

@pytest.fixture
def sim_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time_utc" : pd.to_datetime(["2026-02-09 16:30:00", "2026-02-09 16:31:00"], utc = True),
            "open" : [319.28, 321.24],
            "high" : [321.41, 321.79],
            "low" : [319.28, 320.12],
            "close" : [321.41, 320.12],
            "tick_volume" : [30, 38],
            "spread" : [22, 22],
            "real_volume" : [0, 0]
        }
    )