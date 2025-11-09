import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class TreasuryKPICalculator:
    """Enhanced treasury KPI calculator with comprehensive metrics."""
    
    def __init__(self):
        self.today = pd.Timestamp.today().normalize()
        
    def calculate_all_kpis(
        self, 
        ledger: pd.DataFrame, 
        transactions: pd.DataFrame, 
        balances: pd.DataFrame
    ) -> Dict:
        """Calculate comprehensive treasury KPIs."""
        
        kpis = {}
        
        # Working Capital KPIs
        dso, dpo = self.calculate_dso_dpo(ledger)
        working_capital_metrics = self.calculate_working_capital_metrics(ledger)
        
        kpis.update({
            "dso": dso,
            "dpo": dpo,
            "working_capital": working_capital_metrics
        })
        
        # Cash Flow KPIs
        cash_flow_metrics = self.calculate_cash_flow_kpis(transactions)
        kpis.update({"cash_flow": cash_flow_metrics})
        
        # Liquidity KPIs
        liquidity_metrics = self.calculate_liquidity_kpis(balances, transactions)
        kpis.update({"liquidity": liquidity_metrics})
        
        # Risk KPIs
        risk_metrics = self.calculate_risk_kpis(transactions, balances)
        kpis.update({"risk": risk_metrics})
        
        # Operational KPIs
        operational_metrics = self.calculate_operational_kpis(transactions, ledger)
        kpis.update({"operational": operational_metrics})
        
        return kpis
        
    def calculate_dso_dpo(self, ledger: pd.DataFrame) -> Tuple[float, float]:
        """Calculate Days Sales Outstanding and Days Payable Outstanding."""
        if len(ledger) == 0:
            return 0.0, 0.0
            
        df = ledger.copy()
        df["invoice_date"] = pd.to_datetime(df["invoice_date"])
        df["paid_date"] = pd.to_datetime(df["paid_date"], errors="coerce")

        # DSO Calculation
        ar = df[df["type"] == "AR"].copy()
        if len(ar) > 0:
            ar["settle_date"] = ar["paid_date"].fillna(self.today)
            ar["lag"] = (ar["settle_date"] - ar["invoice_date"]).dt.days
            dso = ar["lag"].mean()
        else:
            dso = 0.0

        # DPO Calculation
        ap = df[df["type"] == "AP"].copy()
        if len(ap) > 0:
            ap["settle_date"] = ap["paid_date"].fillna(self.today)
            ap["lag"] = (ap["settle_date"] - ap["invoice_date"]).dt.days
            dpo = ap["lag"].mean()
        else:
            dpo = 0.0

        return float(dso), float(dpo)
        
    def calculate_working_capital_metrics(self, ledger: pd.DataFrame) -> Dict:
        """Calculate comprehensive working capital metrics."""
        if len(ledger) == 0:
            return {"error": "No ledger data available"}
            
        df = ledger.copy()
        df["invoice_date"] = pd.to_datetime(df["invoice_date"])
        df["due_date"] = pd.to_datetime(df["due_date"])
        df["paid_date"] = pd.to_datetime(df["paid_date"], errors="coerce")
        
        # Current outstanding balances
        unpaid_ar = df[(df["type"] == "AR") & df["paid_date"].isna()]
        unpaid_ap = df[(df["type"] == "AP") & df["paid_date"].isna()]
        
        # Aging analysis
        ar_aging = self._calculate_aging(unpaid_ar)
        ap_aging = self._calculate_aging(unpaid_ap)
        
        # Collection efficiency
        collection_efficiency = self._calculate_collection_efficiency(df)
        
        return {
            "ar_balance": float(unpaid_ar["amount"].sum()) if len(unpaid_ar) > 0 else 0.0,
            "ap_balance": float(unpaid_ap["amount"].sum()) if len(unpaid_ap) > 0 else 0.0,
            "net_working_capital": float(unpaid_ar["amount"].sum() - unpaid_ap["amount"].sum()) if len(unpaid_ar) > 0 or len(unpaid_ap) > 0 else 0.0,
            "ar_aging": ar_aging,
            "ap_aging": ap_aging,
            "collection_efficiency": collection_efficiency
        }
        
    def _calculate_aging(self, df: pd.DataFrame) -> Dict:
        """Calculate aging buckets for AR/AP."""
        if len(df) == 0:
            return {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
            
        df = df.copy()
        df["days_outstanding"] = (self.today - df["due_date"]).dt.days
        
        aging = {
            "0-30": float(df[df["days_outstanding"] <= 30]["amount"].sum()),
            "31-60": float(df[(df["days_outstanding"] > 30) & (df["days_outstanding"] <= 60)]["amount"].sum()),
            "61-90": float(df[(df["days_outstanding"] > 60) & (df["days_outstanding"] <= 90)]["amount"].sum()),
            "90+": float(df[df["days_outstanding"] > 90]["amount"].sum())
        }
        
        return aging
        
    def _calculate_collection_efficiency(self, df: pd.DataFrame) -> Dict:
        """Calculate collection efficiency metrics."""
        ar_df = df[df["type"] == "AR"].copy()
        
        if len(ar_df) == 0:
            return {"rate": 0.0, "average_days": 0.0}
            
        # Collections in last 90 days
        recent_collections = ar_df[
            (ar_df["paid_date"].notna()) & 
            (ar_df["paid_date"] >= self.today - timedelta(days=90))
        ]
        
        if len(recent_collections) == 0:
            return {"rate": 0.0, "average_days": 0.0}
            
        # Calculate collection rate and average collection time
        total_invoiced = ar_df[ar_df["invoice_date"] >= self.today - timedelta(days=90)]["amount"].sum()
        total_collected = recent_collections["amount"].sum()
        
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
        
        recent_collections["collection_days"] = (
            recent_collections["paid_date"] - recent_collections["invoice_date"]
        ).dt.days
        
        avg_collection_days = recent_collections["collection_days"].mean()
        
        return {
            "rate": float(collection_rate),
            "average_days": float(avg_collection_days) if not np.isnan(avg_collection_days) else 0.0
        }
        
    def calculate_cash_flow_kpis(self, transactions: pd.DataFrame) -> Dict:
        """Calculate cash flow KPIs."""
        if len(transactions) == 0:
            return {"error": "No transaction data available"}
            
        df = transactions.copy()
        df["date"] = pd.to_datetime(df["date"])
        
        # Last 30, 60, 90 days analysis
        periods = {
            "30_days": self.today - timedelta(days=30),
            "60_days": self.today - timedelta(days=60),
            "90_days": self.today - timedelta(days=90)
        }
        
        cash_flow_metrics = {}
        
        for period_name, start_date in periods.items():
            period_data = df[df["date"] >= start_date]
            
            if len(period_data) > 0:
                inflows = period_data[period_data["amount"] > 0]["amount"].sum()
                outflows = abs(period_data[period_data["amount"] < 0]["amount"].sum())
                net_flow = period_data["amount"].sum()
                
                cash_flow_metrics[period_name] = {
                    "inflows": float(inflows),
                    "outflows": float(outflows),
                    "net_flow": float(net_flow),
                    "flow_ratio": float(inflows / outflows) if outflows > 0 else float('inf')
                }
            else:
                cash_flow_metrics[period_name] = {
                    "inflows": 0.0,
                    "outflows": 0.0,
                    "net_flow": 0.0,
                    "flow_ratio": 0.0
                }
                
        # Cash flow volatility
        daily_flows = df.groupby("date")["amount"].sum()
        if len(daily_flows) > 1:
            volatility = float(daily_flows.std())
        else:
            volatility = 0.0
            
        cash_flow_metrics["volatility"] = volatility
        
        return cash_flow_metrics
        
    def calculate_liquidity_kpis(self, balances: pd.DataFrame, transactions: pd.DataFrame) -> Dict:
        """Calculate liquidity KPIs."""
        if len(balances) == 0:
            return {"error": "No balance data available"}
            
        # Current liquidity position
        total_balance = balances["balance"].sum()
        
        # Average daily cash usage (last 30 days)
        if len(transactions) > 0:
            recent_tx = transactions[
                pd.to_datetime(transactions["date"]) >= self.today - timedelta(days=30)
            ]
            daily_outflows = recent_tx[recent_tx["amount"] < 0].groupby("date")["amount"].sum()
            avg_daily_usage = abs(daily_outflows.mean()) if len(daily_outflows) > 0 else 0
            
            # Days of liquidity remaining
            days_of_liquidity = total_balance / avg_daily_usage if avg_daily_usage > 0 else float('inf')
        else:
            avg_daily_usage = 0
            days_of_liquidity = float('inf')
            
        # Liquidity by currency
        currency_liquidity = balances.groupby("currency")["balance"].sum().to_dict()
        
        return {
            "total_liquidity": float(total_balance),
            "avg_daily_usage": float(avg_daily_usage),
            "days_of_liquidity": float(days_of_liquidity) if days_of_liquidity != float('inf') else 999,
            "currency_breakdown": {k: float(v) for k, v in currency_liquidity.items()}
        }
        
    def calculate_risk_kpis(self, transactions: pd.DataFrame, balances: pd.DataFrame) -> Dict:
        """Calculate risk-related KPIs."""
        risk_metrics = {}
        
        if len(transactions) > 0:
            # Cash flow at risk (VaR)
            daily_flows = transactions.groupby("date")["amount"].sum()
            if len(daily_flows) >= 30:  # Need sufficient data
                # 5th percentile (95% VaR)
                var_95 = float(daily_flows.quantile(0.05))
                # Standard deviation of daily flows
                flow_volatility = float(daily_flows.std())
            else:
                var_95 = 0.0
                flow_volatility = 0.0
                
            risk_metrics.update({
                "cash_flow_var_95": var_95,
                "flow_volatility": flow_volatility
            })
            
        # Currency concentration risk
        if len(balances) > 0:
            currency_distribution = balances.groupby("currency")["balance"].sum()
            total_balance = currency_distribution.sum()
            
            if total_balance > 0:
                # Herfindahl-Hirschman Index for currency concentration
                currency_shares = currency_distribution / total_balance
                hhi = float((currency_shares ** 2).sum())
                
                # Largest currency exposure
                max_currency_exposure = float(currency_shares.max())
                
                risk_metrics.update({
                    "currency_concentration_hhi": hhi,
                    "max_currency_exposure": max_currency_exposure,
                    "currency_count": len(currency_distribution)
                })
            
        return risk_metrics
        
    def calculate_operational_kpis(self, transactions: pd.DataFrame, ledger: pd.DataFrame) -> Dict:
        """Calculate operational efficiency KPIs."""
        operational_metrics = {}
        
        if len(transactions) > 0:
            # Transaction volume and frequency
            recent_tx = transactions[
                pd.to_datetime(transactions["date"]) >= self.today - timedelta(days=30)
            ]
            
            operational_metrics.update({
                "monthly_transaction_count": len(recent_tx),
                "monthly_transaction_volume": float(recent_tx["amount"].abs().sum()),
                "avg_transaction_size": float(recent_tx["amount"].abs().mean()) if len(recent_tx) > 0 else 0.0
            })
            
        if len(ledger) > 0:
            # Invoice processing efficiency
            recent_invoices = ledger[
                pd.to_datetime(ledger["invoice_date"]) >= self.today - timedelta(days=30)
            ]
            
            operational_metrics.update({
                "monthly_invoices_processed": len(recent_invoices),
                "avg_invoice_value": float(recent_invoices["amount"].mean()) if len(recent_invoices) > 0 else 0.0
            })
            
        return operational_metrics


# Legacy function for backward compatibility
def dso_dpo(ledger: pd.DataFrame):
    """Legacy function - use TreasuryKPICalculator for new implementations."""
    calculator = TreasuryKPICalculator()
    return calculator.calculate_dso_dpo(ledger)