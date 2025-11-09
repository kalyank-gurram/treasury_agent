import os, random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)


# Use modern NumPy random generator
rng = np.random.default_rng(42)

entities = [f"ENT-{i:02d}" for i in range(1, 11)]
banks = ["Operating", "Payroll", "AP", "AR", "Investments"]
currencies = ["USD", "EUR", "GBP", "INR"]

# Accounts
rows = []
for ent in entities:
    for b in banks:
        acct_id = f"{ent}-{b}"
        curr = rng.choice(currencies, p=[0.6,0.15,0.1,0.15])
    rows.append({"entity": ent, "account_id": acct_id, "account_type": b, "currency": curr})
accounts = pd.DataFrame(rows)
accounts.to_csv(os.path.join(DATA, "accounts.csv"), index=False)

# Transactions over ~180 days per account, 4-10/day - ~150k+ rows total
start = datetime.today() - timedelta(days=180)
tx_rows = []
cp_names = [f"Supplier-{i:03d}" for i in range(1, 351)] + [f"Customer-{i:03d}" for i in range(1, 351)]
for _, acct in accounts.iterrows():
    day = start
    for d in range(180):
        n = int(rng.integers(4, 11))
        for i in range(n):
            typ = rng.choice(["INFLOW","OUTFLOW"], p=[0.53,0.47])
            amt = float(rng.lognormal(mean=10.3 if typ=="INFLOW" else 9.9, sigma=0.85))
            if typ == "OUTFLOW":
                amt = -amt
            cp = rng.choice(cp_names)
            tx_rows.append({
                "entity": acct["entity"],
                "account_id": acct["account_id"],
                "date": day.date().isoformat(),
                "type": typ,
                "amount": round(amt,2),
                "counterparty": cp,
                "category": rng.choice(["AP","AR","Payroll","FX","Fees","Misc"], p=[0.3,0.3,0.15,0.1,0.05,0.1])
            })
        day += timedelta(days=1)
transactions = pd.DataFrame(tx_rows)
transactions.to_csv(os.path.join(DATA, "transactions.csv"), index=False)

# Payments
p_rows = []
for i in range(2000):
    ent = rng.choice(entities)
    acct = f"{ent}-AP"
    amt = float(rng.lognormal(mean=12.2, sigma=0.75))
    status = rng.choice(["PENDING","APPROVED","REJECTED"], p=[0.6,0.35,0.05])
    p_rows.append({
        "payment_id": f"PMT-{i:05d}",
        "entity": ent,
        "account_id": acct,
        "amount": round(amt,2),
        "currency": rng.choice(["USD","EUR","GBP","INR"], p=[0.65,0.15,0.1,0.1]),
        "counterparty": rng.choice([c for c in cp_names if c.startswith("Supplier")]),
        "status": status,
    "due_date": (datetime.today() + timedelta(days=int(rng.integers(-10, 30)))).date().isoformat()
    })
payments = pd.DataFrame(p_rows)
payments.to_csv(os.path.join(DATA, "payments.csv"), index=False)

# Counterparties
cp = []
for name in set(transactions["counterparty"].unique()):
    cp.append({
        "counterparty": name,
        "tier": rng.choice(["tier-1","tier-2","tier-3"], p=[0.2,0.5,0.3]),
        "rating": rng.choice(list("ABC"), p=[0.2,0.6,0.2]),
        "country": rng.choice(["US","GB","DE","IN","SG","NL","FR","IE"]),
    })
counterparties = pd.DataFrame(cp)
counterparties.to_csv(os.path.join(DATA, "counterparties.csv"), index=False)

# AR/AP ledger for DSO/DPO
ledger = []
today = datetime.today().date()
for ent in entities:
    for i in range(1500):
        typ = rng.choice(["AR","AP"])
        inv_date = today - timedelta(days=int(rng.integers(1, 270)))
        terms = rng.choice([15,30,45,60])
        due = inv_date + timedelta(days=int(terms))
        amt = float(rng.lognormal(mean=10.7, sigma=0.95))
        paid_delay = rng.choice([-1, 0, 5, 10, 20, 40], p=[0.1,0.3,0.25,0.2,0.1,0.05])
        paid_date = None if paid_delay == -1 else (due + timedelta(days=int(paid_delay)))
        ledger.append({
            "entity": ent, "type": typ, "invoice_date": inv_date.isoformat(),
            "due_date": due.isoformat(), "amount": round(amt,2),
            "paid_date": "" if paid_date is None else paid_date.isoformat()
        })
ar_ap = pd.DataFrame(ledger)
ar_ap.to_csv(os.path.join(DATA, "ar_ap.csv"), index=False)

print("Generated datasets in", DATA)