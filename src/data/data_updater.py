from datetime import datetime
from src.data.mt5_terminal import MT5Terminal
from src.data.sqlite_db import SQLiteDB


def update_symbol(terminal : MT5Terminal,
                 database : SQLiteDB,
                 symbol : str,
                 timeframe : str,
                 start_time : datetime,
                 end_time : datetime) -> int:

    latest_bar = database.get_latest_bar(symbol, timeframe)

    if latest_bar is None:
        init_time = start_time
    else:
        init_time = latest_bar

    bars = terminal.fetch_bars(symbol, timeframe, init_time, end_time)

    return database.save_bars(symbol = symbol, timeframe = timeframe, bars = bars)


def update_all_symbols(terminal : MT5Terminal,
                       database : SQLiteDB,
                       symbols: list[str],
                       timeframe: str,
                       start_time : datetime,
                       end_time : datetime
                       ) -> dict[str, int]:

    updated_bars = {}

    for symbol in symbols:
        try:
            updated_bars[symbol] = update_symbol(terminal, database, symbol, timeframe, start_time, end_time)
        except Exception as error:
            updated_bars[symbol] = None
            print(f"Could not update {symbol}: {error}")

    return updated_bars