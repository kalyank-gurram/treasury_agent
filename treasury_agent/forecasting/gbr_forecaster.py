import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

def gbr_forecast(series: pd.Series, steps: int = 30):
    df = pd.DataFrame({"y": series})
    df["t"] = np.arange(len(df))
    X, y = df[["t"]].values, df["y"].values
    model = GradientBoostingRegressor()
    model.fit(X, y)
    last_t = df["t"].iloc[-1]
    Xf = np.arange(last_t+1, last_t+1+steps).reshape(-1,1)
    preds = model.predict(Xf)
    idx = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=steps, freq="D")
    return pd.Series(preds, index=idx)