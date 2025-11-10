# import pandas as pd
# from statsmodels.tsa.arima.model import ARIMA

# def arima_forecast(series: pd.Series, steps: int = 30):
#     try:
#         model = ARIMA(series, order=(2,1,2))
#         res = model.fit()
#         fc = res.forecast(steps=steps)
#         return fc
#     except Exception:
#         # fallback to mean
#         idx = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=steps, freq="D")
#         return pd.Series([series.mean()]*steps, index=idx)

import pandas as pd
import pmdarima as pm

def arima_forecast(series: pd.Series, steps: int = 30):
    try:
        model = pm.auto_arima(
            series,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            error_action='ignore'
        )
        forecast = model.predict(n_periods=steps)
        idx = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=steps, freq="D")
        return pd.Series(forecast, index=idx)
    except Exception:
        # fallback
        idx = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=steps, freq="D")
        return pd.Series([series.mean()]*steps, index=idx)
