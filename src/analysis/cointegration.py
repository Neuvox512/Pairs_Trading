import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller

#Condition for cointegration is I(1)
def integration_p_values(symbol_prices : pd.Series) -> tuple[float, float]:
    clean_prices = symbol_prices.dropna()
    prices_stationarity = adfuller(clean_prices, regression='c', autolag='AIC')
    prices_stationarity_p_value = prices_stationarity[1]

    price_diff = clean_prices.diff().dropna()
    diff_stationarity = adfuller(price_diff, regression='c', autolag='AIC')
    diff_stationarity_p_value = diff_stationarity[1]

    return prices_stationarity_p_value, diff_stationarity_p_value


def select_i1_symbols(close_prices : pd.DataFrame, significance_level : float = 0.05) -> list[str]:
    selected_symbols = []

    for symbol in close_prices.columns:
        price_stationarity_p_value, diff_stationarity_p_value = integration_p_values(close_prices[symbol])
        if (price_stationarity_p_value > significance_level
            and diff_stationarity_p_value < significance_level):
            selected_symbols.append(symbol)

    return selected_symbols


def cointegration_p_value(first_symbol_close : pd.Series, second_symbol_close : pd.Series) -> float:
    pair = pd.concat([first_symbol_close, second_symbol_close], axis="columns").dropna()

    test_statistic, p_value, critical_values = coint(pair.iloc[:,0], pair.iloc[:,1],
                                                     trend='c', autolag='AIC', return_results=False)

    return p_value

