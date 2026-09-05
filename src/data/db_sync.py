from datetime import datetime, timezone
from pathlib import Path
from src.data.data_updater import update_all_symbols
from src.data.mt5_terminal import MT5Terminal
from src.data.sqlite_db import SQLiteDB

def main() -> None:
    terminal = MT5Terminal()
    terminal.connect()
    db = SQLiteDB(Path("market_data.db"))
    db.create_table()

    all_symbols = terminal.get_all_symbols()

    start_time = datetime(2026, 2, 9, 17, 30)
    end_time = datetime(2026, 2, 9, 17, 31)

    try:
        updated_bars = update_all_symbols(terminal, db, all_symbols, 'M1', start_time, end_time)
    finally:
        terminal.close()

    for symbol in updated_bars:
        print(f"{symbol}: {updated_bars[symbol]}")


if __name__ == "__main__":
    main()