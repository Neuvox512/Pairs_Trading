from pathlib import Path
from src.data.acquisition.data_updater import update_all_symbols
from src.data.acquisition.mt5_terminal import MT5Terminal
from src.data.sqlite_db import SQLiteDB

def main() -> None:
    terminal = MT5Terminal()
    terminal.connect()
    db = SQLiteDB(Path("market_data_(utc).db"))
    db.create_table()

    all_symbols = terminal.get_all_symbols()

    try:
        #Add "start_date" if you would like to load more data from the past
        #Specify timeframe if you would like to load data from other timeframes then 'M1'
        updated_bars = update_all_symbols(terminal, db, all_symbols, 'M1')
    finally:
        terminal.close()

    for symbol in updated_bars:
        print(f"{symbol}: {updated_bars[symbol]}")


if __name__ == "__main__":
    main()