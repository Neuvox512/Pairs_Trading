from datetime import datetime, timezone
from src.data.mt5_terminal import MT5Terminal
from src.data.sqlite_db import SQLiteDB
from tqdm import tqdm

DEFAULT_HISTORY_START = datetime(year=2025, month=1, day=1, tzinfo = timezone.utc)

def update_symbol(terminal : MT5Terminal,
                 database : SQLiteDB,
                 symbol : str,
                 timeframe : str,
                 start_time : datetime | None = None) -> int:

    latest_time_from_db = database.get_latest_bar_time(symbol, timeframe)
    latest_time_from_mt5 = terminal.get_latest_closed_bar_time(symbol, timeframe)

    if latest_time_from_mt5 is None:
        return 0

    if start_time is not None:
        download_start_time = start_time
    elif latest_time_from_db is not None:
        download_start_time = latest_time_from_db
    else:
        download_start_time = DEFAULT_HISTORY_START

    if download_start_time > latest_time_from_mt5:
        return 0

    if (
        start_time is None
        and latest_time_from_db is not None
        and latest_time_from_db >= latest_time_from_mt5
    ):
        return 0

    bars = terminal.fetch_bars(symbol, timeframe, download_start_time, latest_time_from_mt5)

    return database.save_bars(symbol = symbol, timeframe = timeframe, bars = bars)


def update_all_symbols(terminal : MT5Terminal,
                       database : SQLiteDB,
                       symbols: list[str],
                       timeframe: str,
                       start_time : datetime | None = None
                       ) -> dict[str, int | None]:

    updated_bars = {}

    for symbol in tqdm(symbols):
        try:
            updated_bars[symbol] = update_symbol(terminal, database, symbol, timeframe, start_time)
        except RuntimeError as error:
            updated_bars[symbol] = None
            print(f"Could not update {symbol}: {error}")

    return updated_bars