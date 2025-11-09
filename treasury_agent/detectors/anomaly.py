import pandas as pd
import numpy as np

def outflow_anomalies(daily_series: pd.Series, lookback: int = 90, z: float = 3.0):
    s = daily_series.tail(lookback)
    mu, sigma = s.mean(), s.std(ddof=1) + 1e-6
    zscores = (daily_series - mu) / sigma
    mask = (daily_series < 0) & (np.abs(zscores) > z)
    return pd.DataFrame({ "value": daily_series[mask], "z": zscores[mask] })