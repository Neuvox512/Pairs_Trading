import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.stats.multitest import fdrcorrection
from itertools import combinations


def screen_pairs(close_prices : pd.DataFrame) -> pd.DataFrame:
    #I(1) condition
    i1_symbols = select_i1_symbols(close_prices)
    #Cointegration
    coint_pairs = calculate_pair_p_values(close_prices, i1_symbols)
    #Benjamini-Hochberg correction
    corrected_coint_pairs = bh_correction(coint_pairs)

    return corrected_coint_pairs


def bh_correction(pair_p_values : pd.DataFrame) -> pd.DataFrame:
    bh_corr = fdrcorrection(pair_p_values['coint_p_value'], alpha=0.05)
    pair_p_values['adjusted_p_value'] = bh_corr[1]
    pair_p_values['reject_no_coint'] = bh_corr[0]

    return pair_p_values


def calculate_pair_p_values(close_prices : pd.DataFrame, symbols : list[str]) -> pd.DataFrame:
    result = []
    for symbol_1, symbol_2 in combinations(symbols, 2):
        test_statistic, p_value, critical_values = coint(
            close_prices[symbol_1],
            close_prices[symbol_2],
            trend='c',
            autolag='AIC',
            return_results=False
        )
        result.append(
            {
                "first_symbol": symbol_1,
                "second_symbol": symbol_2,
                "coint_p_value": p_value,
            }
        )

    return pd.DataFrame(result)

#Condition for cointegration is I(1)
def integration_p_values(close_prices : pd.Series) -> tuple[float, float]:
    prices_stationarity = adfuller(close_prices, regression='c', autolag='AIC')
    prices_stationarity_p_value = prices_stationarity[1]

    price_diff = close_prices.diff().dropna()
    diff_stationarity = adfuller(price_diff, regression='c', autolag='AIC')
    diff_stationarity_p_value = diff_stationarity[1]

    return prices_stationarity_p_value, diff_stationarity_p_value


def select_i1_symbols(close_prices : pd.DataFrame, significance_level : float = 0.05) -> list[str]:
    selected_symbols = []

    for symbol in close_prices.columns:
        #I(0)
        prices_stationarity = adfuller(close_prices[symbol], regression='c', autolag='AIC')
        price_stationarity_p_value = prices_stationarity[1]
        #I(1)
        price_diff = close_prices[symbol].diff().dropna()
        price_diff_stationarity = adfuller(price_diff, regression='c', autolag='AIC')
        price_diff_stationarity_p_value = price_diff_stationarity[1]

        if (price_stationarity_p_value > significance_level
            and price_diff_stationarity_p_value < significance_level):
            selected_symbols.append(symbol)

        return selected_symbols


