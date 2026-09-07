import pandas as pd


def prepare_prices(close_prices: pd.DataFrame) -> pd.DataFrame:
    clean_prices = close_prices.ffill().dropna()

    return clean_prices