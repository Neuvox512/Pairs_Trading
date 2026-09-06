import pandas as pd


def fill_price_gaps(close_prices: pd.DataFrame) -> pd.DataFrame:
    filled_prices = close_prices.ffill()

    return filled_prices