import pandas as pd
from src.analysis.cointegration import *

def screen_pairs(close_prices : pd.DataFrame) -> pd.DataFrame:
    i1_symbols = select_i1_symbols(close_prices)

    coint_pairs = calculate_pair_p_values(close_prices, i1_symbols)

    corrected_coint_pairs = bh_correction(coint_pairs)

    return corrected_coint_pairs

