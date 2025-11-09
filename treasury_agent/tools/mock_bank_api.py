import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA = os.path.join(BASE, "data")

class MockBankAPI:
    def __init__(self):
        self.accounts = pd.read_csv(os.path.join(DATA, "accounts.csv"))
        self.transactions = pd.read_csv(os.path.join(DATA, "transactions.csv"))
        self.payments = pd.read_csv(os.path.join(DATA, "payments.csv"))
        self.counterparties = pd.read_csv(os.path.join(DATA, "counterparties.csv"))
        self.ar_ap = pd.read_csv(os.path.join(DATA, "ar_ap.csv"))

    def get_account_balances(self, entity: str | None = None):
        df = self.transactions
        if entity:
            df = df[df["entity"] == entity]
        latest_date = df["date"].max()
        sums = df.groupby(["entity","account_id"])["amount"].sum().reset_index(name="balance")
        out = sums.merge(self.accounts, on=["entity","account_id"])
        out["as_of"] = latest_date
        return out

    def get_daily_series(self, entity: str | None = None):
        df = self.transactions
        if entity:
            df = df[df["entity"] == entity]
        daily = df.groupby("date")["amount"].sum().sort_index()
        daily.index = pd.to_datetime(daily.index)
        return daily.asfreq("D").fillna(0)

    def list_payments(self, status: str | None = None):
        df = self.payments
        if status:
            df = df[df["status"] == status]
        return df

    def approve_payment(self, payment_id: str):
        idx = self.payments.index[self.payments["payment_id"] == payment_id]
        if len(idx) == 0:
            return False
        self.payments.loc[idx, "status"] = "APPROVED"
        self.payments.to_csv(os.path.join(DATA, "payments.csv"), index=False)
        return True

    def get_counterparty_exposure(self, entity: str | None = None, start_date: str | None = None, end_date: str | None = None):
        df = self.transactions
        if entity:
            df = df[df["entity"] == entity]
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]
        agg = df.groupby(["counterparty"])["amount"].sum().reset_index()
        cp = self.counterparties
        agg = agg.merge(cp, on="counterparty", how="left")
        agg["outflow_abs"] = agg["amount"].apply(lambda x: -x if x < 0 else 0.0)
        agg["inflow_abs"] = agg["amount"].apply(lambda x: x if x > 0 else 0.0)
        return agg.sort_values("outflow_abs", ascending=False)

    def get_ledger(self, entity: str | None = None):
        df = self.ar_ap.copy()
        if entity:
            df = df[df["entity"] == entity]
        return df