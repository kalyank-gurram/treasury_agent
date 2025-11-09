import pandas as pd

def dso_dpo(ledger: pd.DataFrame):
    df = ledger.copy()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["paid_date"] = pd.to_datetime(df["paid_date"], errors="coerce")
    today = pd.Timestamp.today().normalize()

    ar = df[df["type"]=="AR"].copy()
    ar["settle_date"] = ar["paid_date"].fillna(today)
    ar["lag"] = (ar["settle_date"] - ar["invoice_date"]).dt.days
    dso = ar["lag"].mean()

    ap = df[df["type"]=="AP"].copy()
    ap["settle_date"] = ap["paid_date"].fillna(today)
    ap["lag"] = (ap["settle_date"] - ap["invoice_date"]).dt.days
    dpo = ap["lag"].mean()

    return dso, dpo