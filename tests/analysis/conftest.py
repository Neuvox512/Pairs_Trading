import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sim_close_prices() -> pd.DataFrame:
    random_gen = np.random.RandomState(0)

    time_index = pd.date_range(start="2026-08-02", periods=250, freq="1min", tz="UTC")

    first_i1 = pd.Series(100 + random_gen.normal(size=250).cumsum(), index=time_index)

    second_i1 = pd.Series(50 + 2 * first_i1 + random_gen.normal(size=250, scale=0.5), index=time_index)

    independent_i1 = pd.Series(200 + random_gen.normal(size=250).cumsum(), index=time_index)

    stationary = pd.Series(100 + random_gen.normal(size=250), index=time_index)

    return pd.DataFrame(
        {
            "first_i1": first_i1,
            "second_i1": second_i1,
            "indep_i1": independent_i1,
            "stationary": stationary,
        }
    )