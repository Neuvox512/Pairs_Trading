import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.stats.multitest import fdrcorrection
from itertools import combinations


def bh_correction(pair_p_values : pd.DataFrame) -> pd.DataFrame:
    bh_corr = fdrcorrection(pair_p_values['coint_p_value'], alpha=0.05)
    pair_p_values['adjusted_p_value'] = bh_corr[1]
    pair_p_values['reject_no_coint'] = bh_corr[0]

    return pair_p_values


def calculate_pair_p_values(close_prices : pd.DataFrame, symbols : list[str]) -> pd.DataFrame:
    result = []
    for symbol_1, symbol_2 in combinations(symbols, 2):
        coint_p_value = cointegration_p_value(close_prices[symbol_1], close_prices[symbol_2])
        result.append(
            {
                "first_symbol": symbol_1,
                "second_symbol": symbol_2,
                "coint_p_value": coint_p_value,
            }
        )

    return pd.DataFrame(result)

#Condition for cointegration is I(1)
def integration_p_values(close_prices : pd.Series) -> tuple[float, float]:
    clean_prices = close_prices.dropna()
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


