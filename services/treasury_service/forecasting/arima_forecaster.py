import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def arima_forecast(series: pd.Series, steps: int = 30):
    try:
        model = ARIMA(series, order=(2,1,2))
        res = model.fit()
        fc = res.forecast(steps=steps)
        return fc
    except Exception:
        # fallback to mean
        idx = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=steps, freq="D")
        return pd.Series([series.mean()]*steps, index=idx)