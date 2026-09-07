import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller


def integration_p_values(symbol_prices : pd.Series) -> tuple[float, float]:
    clean_prices = symbol_prices.dropna()
    prices_stationarity = adfuller(clean_prices, regression='c', autolag='AIC')
    prices_stationarity_p_value = prices_stationarity[1]

    price_diff = clean_prices.diff().dropna()
    diff_stationarity = adfuller(price_diff, regression='c', autolag='AIC')
    diff_stationarity_p_value = diff_stationarity[1]

    return prices_stationarity_p_value, diff_stationarity_p_value


def cointegration_p_value(first_symbol_close : pd.Series, second_symbol_close : pd.Series) -> float:
    pair = pd.concat([first_symbol_close, second_symbol_close], axis="columns").dropna()

    test_statistic, p_value, critical_values = coint(pair.iloc[:,0], pair.iloc[:,1],
                                                     trend='c', autolag='AIC', return_results=False)

    return p_value

