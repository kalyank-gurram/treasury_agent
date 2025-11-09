"""Mock Bank API for Treasury Agent demonstration and testing."""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random


class MockBankAPI:
    """Mock bank API that provides realistic treasury data for demonstration purposes."""
    
    def __init__(self):
        """Initialize the mock bank API with data loading."""
        self._load_data()
        
    def _load_data(self):
        """Load mock data from CSV files or generate if not available."""
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_path = os.path.join(base_path, "data")
        
        try:
            # Load transactions data
            transactions_file = os.path.join(data_path, "transactions.csv")
            if os.path.exists(transactions_file):
                self.transactions = pd.read_csv(transactions_file)
            else:
                self.transactions = self._generate_mock_transactions()
                
            # Load accounts data
            accounts_file = os.path.join(data_path, "accounts.csv")
            if os.path.exists(accounts_file):
                self.accounts = pd.read_csv(accounts_file)
            else:
                self.accounts = self._generate_mock_accounts()
                
            # Load payments data
            payments_file = os.path.join(data_path, "payments.csv")
            if os.path.exists(payments_file):
                self.payments = pd.read_csv(payments_file)
            else:
                self.payments = self._generate_mock_payments()
                
            # Load AR/AP ledger data
            ledger_file = os.path.join(data_path, "ar_ap.csv")
            if os.path.exists(ledger_file):
                self.ledger = pd.read_csv(ledger_file)
            else:
                self.ledger = self._generate_mock_ledger()
                
            # Load counterparties data
            counterparties_file = os.path.join(data_path, "counterparties.csv")
            if os.path.exists(counterparties_file):
                self.counterparties = pd.read_csv(counterparties_file)
            else:
                self.counterparties = self._generate_mock_counterparties()
                
        except Exception as e:
            print(f"Warning: Could not load data from {data_path}, generating mock data: {e}")
            self.transactions = self._generate_mock_transactions()
            self.accounts = self._generate_mock_accounts()
            self.payments = self._generate_mock_payments()
            self.ledger = self._generate_mock_ledger()
            self.counterparties = self._generate_mock_counterparties()
    
    def _generate_mock_transactions(self) -> pd.DataFrame:
        """Generate mock transaction data if CSV files are not available."""
        rng = np.random.default_rng(42)
        entities = [f"ENT-{i:02d}" for i in range(1, 11)]
        banks = ["Operating", "Payroll", "AP", "AR", "Investments"]
        cp_names = [f"Supplier-{i:03d}" for i in range(1, 101)] + [f"Customer-{i:03d}" for i in range(1, 101)]
        
        start = datetime.today() - timedelta(days=180)
        tx_rows = []
        
        for entity in entities:
            for bank in banks:
                account_id = f"{entity}-{bank}"
                day = start
                
                for d in range(180):
                    n = int(rng.integers(2, 6))  # 2-5 transactions per day
                    for i in range(n):
                        typ = rng.choice(["INFLOW", "OUTFLOW"], p=[0.53, 0.47])
                        amt = float(rng.lognormal(mean=10.3 if typ == "INFLOW" else 9.9, sigma=0.85))
                        if typ == "OUTFLOW":
                            amt = -amt
                        cp = rng.choice(cp_names)
                        
                        tx_rows.append({
                            "entity": entity,
                            "account_id": account_id,
                            "date": day.date().isoformat(),
                            "type": typ,
                            "amount": round(amt, 2),
                            "counterparty": cp,
                            "category": rng.choice(["AP", "AR", "Payroll", "FX", "Fees", "Misc"], 
                                                 p=[0.3, 0.3, 0.15, 0.1, 0.05, 0.1])
                        })
                    day += timedelta(days=1)
        
        return pd.DataFrame(tx_rows)
    
    def _generate_mock_accounts(self) -> pd.DataFrame:
        """Generate mock account data."""
        rng = np.random.default_rng(42)
        entities = [f"ENT-{i:02d}" for i in range(1, 11)]
        banks = ["Operating", "Payroll", "AP", "AR", "Investments"]
        currencies = ["USD", "EUR", "GBP", "INR"]
        
        rows = []
        for ent in entities:
            for b in banks:
                acct_id = f"{ent}-{b}"
                curr = rng.choice(currencies, p=[0.6, 0.15, 0.1, 0.15])
                rows.append({
                    "entity": ent,
                    "account_id": acct_id,
                    "account_type": b,
                    "currency": curr
                })
        
        return pd.DataFrame(rows)
    
    def _generate_mock_payments(self) -> pd.DataFrame:
        """Generate mock payment data."""
        rng = np.random.default_rng(42)
        entities = [f"ENT-{i:02d}" for i in range(1, 11)]
        
        p_rows = []
        for i in range(1000):
            ent = rng.choice(entities)
            acct = f"{ent}-AP"
            amt = float(rng.lognormal(mean=12.2, sigma=0.75))
            status = rng.choice(["PENDING", "APPROVED", "REJECTED"], p=[0.6, 0.35, 0.05])
            
            p_rows.append({
                "payment_id": f"PMT-{i:05d}",
                "entity": ent,
                "account_id": acct,
                "amount": round(amt, 2),
                "currency": rng.choice(["USD", "EUR", "GBP", "INR"], p=[0.65, 0.15, 0.1, 0.1]),
                "counterparty": f"Supplier-{rng.integers(1, 351):03d}",
                "status": status,
                "due_date": (datetime.today() + timedelta(days=int(rng.integers(-10, 30)))).date().isoformat()
            })
        
        return pd.DataFrame(p_rows)
    
    def _generate_mock_ledger(self) -> pd.DataFrame:
        """Generate mock AR/AP ledger data."""
        rng = np.random.default_rng(42)
        entities = [f"ENT-{i:02d}" for i in range(1, 11)]
        
        ledger = []
        today = datetime.today().date()
        
        for ent in entities:
            for i in range(500):  # 500 entries per entity
                typ = rng.choice(["AR", "AP"])
                inv_date = today - timedelta(days=int(rng.integers(1, 270)))
                terms = rng.choice([15, 30, 45, 60])
                due = inv_date + timedelta(days=int(terms))
                amt = float(rng.lognormal(mean=10.7, sigma=0.95))
                
                paid_delay = rng.choice([-1, 0, 5, 10, 20, 40], p=[0.1, 0.3, 0.25, 0.2, 0.1, 0.05])
                paid_date = None if paid_delay == -1 else (due + timedelta(days=int(paid_delay)))
                
                ledger.append({
                    "entity": ent,
                    "type": typ,
                    "invoice_date": inv_date.isoformat(),
                    "due_date": due.isoformat(),
                    "amount": round(amt, 2),
                    "paid_date": "" if paid_date is None else paid_date.isoformat()
                })
        
        return pd.DataFrame(ledger)
    
    def _generate_mock_counterparties(self) -> pd.DataFrame:
        """Generate mock counterparty data."""
        rng = np.random.default_rng(42)
        
        # Generate supplier and customer names
        suppliers = [f"Supplier-{i:03d}" for i in range(1, 351)]
        customers = [f"Customer-{i:03d}" for i in range(1, 351)]
        all_counterparties = suppliers + customers
        
        cp = []
        for name in all_counterparties:
            cp.append({
                "counterparty": name,
                "tier": rng.choice(["tier-1", "tier-2", "tier-3"], p=[0.2, 0.5, 0.3]),
                "rating": rng.choice(list("ABC"), p=[0.2, 0.6, 0.2]),
                "country": rng.choice(["US", "GB", "DE", "IN", "SG", "NL", "FR", "IE"]),
            })
        
        return pd.DataFrame(cp)
    
    def get_account_balances(self, entity: Optional[str] = None) -> Dict[str, float]:
        """Get current account balances for specified entity or all entities."""
        rng = np.random.default_rng(42)
        balances = {}
        
        accounts_subset = self.accounts
        if entity and entity != "ALL":
            accounts_subset = self.accounts[self.accounts["entity"] == entity]
        
        for _, account in accounts_subset.iterrows():
            # Generate realistic balance based on account type
            account_type = account["account_type"]
            if account_type == "Operating":
                balance = rng.uniform(5000000, 25000000)  # $5M - $25M
            elif account_type == "Payroll":
                balance = rng.uniform(500000, 3000000)    # $500K - $3M
            elif account_type == "AP":
                balance = rng.uniform(2000000, 10000000)  # $2M - $10M
            elif account_type == "AR":
                balance = rng.uniform(8000000, 15000000)  # $8M - $15M
            elif account_type == "Investments":
                balance = rng.uniform(10000000, 50000000) # $10M - $50M
            else:
                balance = rng.uniform(1000000, 5000000)   # Default: $1M - $5M
                
            balances[account["account_id"]] = round(balance, 2)
        
        return balances
    
    def get_recent_transactions(self, entity: Optional[str] = None, 
                              days: int = 30, limit: int = 100) -> pd.DataFrame:
        """Get recent transactions for the specified entity."""
        transactions = self.transactions.copy()
        
        # Filter by entity
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
        
        # Filter by date
        transactions["date"] = pd.to_datetime(transactions["date"])
        cutoff_date = datetime.now() - timedelta(days=days)
        transactions = transactions[transactions["date"] >= cutoff_date]
        
        # Sort by date (most recent first) and limit
        transactions = transactions.sort_values("date", ascending=False).head(limit)
        
        return transactions.reset_index(drop=True)
    
    def list_payments(self, entity: Optional[str] = None, 
                     status: Optional[str] = None) -> pd.DataFrame:
        """List payments with optional filtering by entity and status."""
        payments = self.payments.copy()
        
        # Filter by entity
        if entity and entity != "ALL":
            payments = payments[payments["entity"] == entity]
        
        # Filter by status
        if status:
            payments = payments[payments["status"] == status.upper()]
        
        return payments.reset_index(drop=True)
    
    def get_ledger(self, entity: Optional[str] = None, 
                   ledger_type: Optional[str] = None) -> pd.DataFrame:
        """Get AR/AP ledger entries with optional filtering."""
        ledger = self.ledger.copy()
        
        # Filter by entity
        if entity and entity != "ALL":
            ledger = ledger[ledger["entity"] == entity]
        
        # Filter by type (AR or AP)
        if ledger_type:
            ledger = ledger[ledger["type"] == ledger_type.upper()]
        
        return ledger.reset_index(drop=True)
    
    def get_counterparties(self, entity: Optional[str] = None) -> pd.DataFrame:
        """Get counterparty information."""
        return self.counterparties.copy()
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new payment (mock implementation)."""
        payment_id = f"PMT-{len(self.payments) + 1:05d}"
        
        new_payment = {
            "payment_id": payment_id,
            "entity": payment_data.get("entity"),
            "account_id": payment_data.get("account_id"),
            "amount": payment_data.get("amount"),
            "currency": payment_data.get("currency", "USD"),
            "counterparty": payment_data.get("counterparty"),
            "status": "PENDING",
            "due_date": payment_data.get("due_date", datetime.today().isoformat())
        }
        
        # Add to payments dataframe (in real system, this would be persisted)
        new_row = pd.DataFrame([new_payment])
        self.payments = pd.concat([self.payments, new_row], ignore_index=True)
        
        return {
            "payment_id": payment_id,
            "status": "created",
            "message": f"Payment {payment_id} created successfully"
        }
    
    def update_payment_status(self, payment_id: str, status: str) -> Dict[str, Any]:
        """Update payment status (mock implementation)."""
        mask = self.payments["payment_id"] == payment_id
        
        if not mask.any():
            return {
                "status": "error",
                "message": f"Payment {payment_id} not found"
            }
        
        self.payments.loc[mask, "status"] = status.upper()
        
        return {
            "payment_id": payment_id,
            "status": "updated",
            "new_status": status.upper(),
            "message": f"Payment {payment_id} status updated to {status.upper()}"
        }
    
    def get_cash_position(self, entity: Optional[str] = None, 
                         as_of_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get current cash position summary."""
        if as_of_date is None:
            as_of_date = datetime.now()
        
        balances = self.get_account_balances(entity)
        
        # Calculate totals by currency
        accounts_subset = self.accounts
        if entity and entity != "ALL":
            accounts_subset = self.accounts[self.accounts["entity"] == entity]
        
        position_summary = {}
        for currency in accounts_subset["currency"].unique():
            currency_accounts = accounts_subset[accounts_subset["currency"] == currency]
            total_balance = sum(balances.get(acc["account_id"], 0) 
                              for _, acc in currency_accounts.iterrows())
            position_summary[currency] = round(total_balance, 2)
        
        return {
            "as_of_date": as_of_date.isoformat(),
            "entity": entity or "ALL",
            "balances_by_account": balances,
            "total_by_currency": position_summary
        }