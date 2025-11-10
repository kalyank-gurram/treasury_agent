import pandas as pd
import numpy as np

def detect_cashflow_anomalies(
    series: pd.Series, lookback: int = 90, z_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Detect anomalies in daily cashflows using simple rolling z-score.
    
    Args:
        series (pd.Series): Daily cashflow time series (Date index)
        lookback (int): Rolling window for baseline calculation
        z_threshold (float): Threshold in standard deviations to flag anomalies

    Returns:
        pd.DataFrame: Table of detected anomalies with z-scores
    """
    if len(series) < 30:
        return pd.DataFrame(columns=["date", "value", "z_score", "description"])
    
    rolling_mean = series.rolling(window=lookback, min_periods=30).mean()
    rolling_std = series.rolling(window=lookback, min_periods=30).std()
    
    z_scores = (series - rolling_mean) / (rolling_std + 1e-6)
    anomalies = series[np.abs(z_scores) > z_threshold]
    
    result = pd.DataFrame({
        "date": anomalies.index,
        "value": anomalies.values,
        "z_score": z_scores.loc[anomalies.index],
        "description": [
            f"Cashflow deviation of {z:.2f} std deviations" for z in z_scores.loc[anomalies.index]
        ]
    })
    
    return result.reset_index(drop=True)
