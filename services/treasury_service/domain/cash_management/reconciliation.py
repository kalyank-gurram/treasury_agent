"""Automated bank reconciliation engine."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from .infrastructure.observability import get_observability_manager


class ReconciliationStatus(Enum):
    """Status of reconciliation items."""
    MATCHED = "matched"
    UNMATCHED_BOOK = "unmatched_book"
    UNMATCHED_BANK = "unmatched_bank"
    TIMING_DIFFERENCE = "timing_difference" 
    AMOUNT_DIFFERENCE = "amount_difference"
    REQUIRES_INVESTIGATION = "requires_investigation"


@dataclass
class ReconciliationItem:
    """Individual reconciliation item."""
    item_id: str
    transaction_date: datetime
    book_amount: Optional[float]
    bank_amount: Optional[float]
    difference: float
    status: ReconciliationStatus
    description: str
    counterparty: Optional[str] = None
    reference: Optional[str] = None
    confidence_score: float = 0.0
    suggested_action: Optional[str] = None


@dataclass 
class ReconciliationReport:
    """Reconciliation report summary."""
    entity: str
    account_id: str
    reconciliation_date: datetime
    book_balance: float
    bank_balance: float
    net_difference: float
    total_items: int
    matched_items: int
    unmatched_items: int
    items_by_status: Dict[str, int]
    confidence_score: float
    items: List[ReconciliationItem]
    

class AutoReconciliationEngine:
    """Automated bank reconciliation with intelligent matching."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("cash_management.reconciliation")
        
        # Matching parameters
        self.matching_config = {
            "exact_match_tolerance": 0.01,  # $0.01 tolerance for exact matches
            "amount_tolerance_percent": 0.05,  # 5% tolerance for amount matching
            "date_tolerance_days": 3,  # 3 days tolerance for timing differences
            "fuzzy_match_threshold": 0.8,  # 80% similarity for fuzzy matching
            "auto_approve_threshold": 0.95  # 95% confidence for auto-approval
        }
        
    def reconcile_account(self, entity: str, account_id: str, 
                         reconciliation_date: Optional[datetime] = None) -> ReconciliationReport:
        """Perform automated reconciliation for a specific account."""
        if reconciliation_date is None:
            reconciliation_date = datetime.now()
            
        self.logger.info("Starting automated reconciliation",
                        entity=entity, account_id=account_id, 
                        reconciliation_date=reconciliation_date.isoformat())
        
        try:
            # Get book and bank data
            book_transactions = self._get_book_transactions(entity, account_id, reconciliation_date)
            bank_transactions = self._get_bank_transactions(entity, account_id, reconciliation_date)
            
            # Calculate balances
            book_balance = book_transactions["amount"].sum() if len(book_transactions) > 0 else 0
            bank_balance = bank_transactions["amount"].sum() if len(bank_transactions) > 0 else 0
            
            # Perform matching
            reconciliation_items = self._perform_matching(book_transactions, bank_transactions)
            
            # Calculate statistics
            matched_count = len([item for item in reconciliation_items if item.status == ReconciliationStatus.MATCHED])
            total_count = len(reconciliation_items)
            
            # Count by status
            status_counts = {}
            for status in ReconciliationStatus:
                status_counts[status.value] = len([item for item in reconciliation_items if item.status == status])
                
            # Calculate overall confidence
            if total_count > 0:
                avg_confidence = sum(item.confidence_score for item in reconciliation_items) / total_count
            else:
                avg_confidence = 1.0
                
            report = ReconciliationReport(
                entity=entity,
                account_id=account_id,
                reconciliation_date=reconciliation_date,
                book_balance=book_balance,
                bank_balance=bank_balance,
                net_difference=book_balance - bank_balance,
                total_items=total_count,
                matched_items=matched_count,
                unmatched_items=total_count - matched_count,
                items_by_status=status_counts,
                confidence_score=avg_confidence,
                items=reconciliation_items
            )
            
            self.logger.info("Reconciliation completed",
                           entity=entity, account_id=account_id,
                           total_items=total_count, matched_items=matched_count,
                           net_difference=book_balance - bank_balance,
                           confidence_score=avg_confidence)
            
            # Record metrics
            self.observability.record_metric(
                "counter", "reconciliations_completed_total", 1,
                {"entity": entity, "account": account_id}
            )
            
            self.observability.record_metric(
                "gauge", "reconciliation_match_rate", matched_count / total_count if total_count > 0 else 1,
                {"entity": entity, "account": account_id}
            )
            
            return report
            
        except Exception as e:
            self.logger.error("Reconciliation failed",
                            entity=entity, account_id=account_id,
                            error=str(e), error_type=type(e).__name__)
            
            self.observability.record_metric(
                "counter", "reconciliations_failed_total", 1,
                {"entity": entity, "account": account_id}
            )
            
            raise
            
    def _get_book_transactions(self, entity: str, account_id: str, 
                             reconciliation_date: datetime) -> pd.DataFrame:
        """Get book transactions for reconciliation."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        transactions = api.transactions.copy()
        
        # Filter by entity and account
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
            
        if account_id != "ALL":
            transactions = transactions[transactions["account_id"] == account_id]
            
        # Filter by date (e.g., current month)
        transactions["date"] = pd.to_datetime(transactions["date"])
        month_start = reconciliation_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = reconciliation_date
        
        transactions = transactions[
            (transactions["date"] >= month_start) & 
            (transactions["date"] <= month_end)
        ]
        
        # Add reconciliation fields
        transactions["transaction_id"] = transactions.index.astype(str)
        transactions["source"] = "book"
        
        return transactions
        
    def _get_bank_transactions(self, entity: str, account_id: str, 
                             reconciliation_date: datetime) -> pd.DataFrame:
        """Get bank transactions for reconciliation (simulated)."""
        # In a real system, this would fetch from bank APIs or files
        # For simulation, we'll create bank data based on book transactions with some variations
        
        book_transactions = self._get_book_transactions(entity, account_id, reconciliation_date)
        
        if len(book_transactions) == 0:
            return pd.DataFrame(columns=["date", "amount", "counterparty", "description", "transaction_id", "source"])
            
        # Simulate bank transactions with realistic variations
        bank_transactions = book_transactions.copy()
        
        # Add some timing differences (10% of transactions)
        timing_diff_mask = np.random.random(len(bank_transactions)) < 0.1
        bank_transactions.loc[timing_diff_mask, "date"] += pd.Timedelta(days=1)
        
        # Add some amount differences (5% of transactions) 
        amount_diff_mask = np.random.random(len(bank_transactions)) < 0.05
        bank_transactions.loc[amount_diff_mask, "amount"] *= np.random.uniform(0.95, 1.05, sum(amount_diff_mask))
        
        # Remove some transactions to simulate unmatched bank items (3%)
        remove_mask = np.random.random(len(bank_transactions)) < 0.03
        bank_transactions = bank_transactions[~remove_mask]
        
        # Add some extra bank transactions (2%)
        extra_count = max(1, int(len(book_transactions) * 0.02))
        extra_transactions = []
        
        for i in range(extra_count):
            base_amount = np.random.choice(bank_transactions["amount"].values) if len(bank_transactions) > 0 else 1000
            extra_transactions.append({
                "date": reconciliation_date - timedelta(days=np.random.randint(0, 30)),
                "amount": base_amount * np.random.uniform(0.5, 1.5),
                "counterparty": f"Bank-Only-{i+1}",
                "description": "Bank fee or interest",
                "transaction_id": f"bank_only_{i+1}",
                "source": "bank"
            })
            
        if extra_transactions:
            extra_df = pd.DataFrame(extra_transactions)
            bank_transactions = pd.concat([bank_transactions, extra_df], ignore_index=True)
            
        bank_transactions["source"] = "bank"
        bank_transactions["transaction_id"] = "bank_" + bank_transactions["transaction_id"].astype(str)
        
        return bank_transactions.reset_index(drop=True)
        
    def _perform_matching(self, book_transactions: pd.DataFrame, 
                         bank_transactions: pd.DataFrame) -> List[ReconciliationItem]:
        """Perform intelligent matching between book and bank transactions."""
        reconciliation_items = []
        matched_book_ids = set()
        matched_bank_ids = set()
        
        # Phase 1: Exact matches (amount and date)
        for book_idx, book_row in book_transactions.iterrows():
            if book_idx in matched_book_ids:
                continue
                
            for bank_idx, bank_row in bank_transactions.iterrows():
                if bank_idx in matched_bank_ids:
                    continue
                    
                if self._is_exact_match(book_row, bank_row):
                    item = ReconciliationItem(
                        item_id=f"match_{len(reconciliation_items)+1}",
                        transaction_date=book_row["date"],
                        book_amount=book_row["amount"],
                        bank_amount=bank_row["amount"],
                        difference=0.0,
                        status=ReconciliationStatus.MATCHED,
                        description="Exact match",
                        counterparty=book_row.get("counterparty"),
                        confidence_score=1.0,
                        suggested_action="No action required"
                    )
                    reconciliation_items.append(item)
                    matched_book_ids.add(book_idx)
                    matched_bank_ids.add(bank_idx)
                    break
                    
        # Phase 2: Amount matches with timing differences
        for book_idx, book_row in book_transactions.iterrows():
            if book_idx in matched_book_ids:
                continue
                
            for bank_idx, bank_row in bank_transactions.iterrows():
                if bank_idx in matched_bank_ids:
                    continue
                    
                if self._is_timing_difference_match(book_row, bank_row):
                    item = ReconciliationItem(
                        item_id=f"timing_{len(reconciliation_items)+1}",
                        transaction_date=book_row["date"],
                        book_amount=book_row["amount"],
                        bank_amount=bank_row["amount"],
                        difference=0.0,
                        status=ReconciliationStatus.TIMING_DIFFERENCE,
                        description=f"Timing difference: book {book_row['date'].date()} vs bank {bank_row['date'].date()}",
                        counterparty=book_row.get("counterparty"),
                        confidence_score=0.9,
                        suggested_action="Verify timing difference is acceptable"
                    )
                    reconciliation_items.append(item)
                    matched_book_ids.add(book_idx)
                    matched_bank_ids.add(bank_idx)
                    break
                    
        # Phase 3: Date matches with amount differences
        for book_idx, book_row in book_transactions.iterrows():
            if book_idx in matched_book_ids:
                continue
                
            for bank_idx, bank_row in bank_transactions.iterrows():
                if bank_idx in matched_bank_ids:
                    continue
                    
                if self._is_amount_difference_match(book_row, bank_row):
                    difference = book_row["amount"] - bank_row["amount"]
                    item = ReconciliationItem(
                        item_id=f"amount_diff_{len(reconciliation_items)+1}",
                        transaction_date=book_row["date"],
                        book_amount=book_row["amount"],
                        bank_amount=bank_row["amount"],
                        difference=difference,
                        status=ReconciliationStatus.AMOUNT_DIFFERENCE,
                        description=f"Amount difference: ${difference:.2f}",
                        counterparty=book_row.get("counterparty"),
                        confidence_score=0.8,
                        suggested_action="Investigate amount discrepancy"
                    )
                    reconciliation_items.append(item)
                    matched_book_ids.add(book_idx)
                    matched_bank_ids.add(bank_idx)
                    break
                    
        # Phase 4: Unmatched book transactions
        for book_idx, book_row in book_transactions.iterrows():
            if book_idx not in matched_book_ids:
                item = ReconciliationItem(
                    item_id=f"unmatched_book_{len(reconciliation_items)+1}",
                    transaction_date=book_row["date"],
                    book_amount=book_row["amount"],
                    bank_amount=None,
                    difference=book_row["amount"],
                    status=ReconciliationStatus.UNMATCHED_BOOK,
                    description="No matching bank transaction found",
                    counterparty=book_row.get("counterparty"),
                    confidence_score=0.6,
                    suggested_action="Verify transaction was processed by bank"
                )
                reconciliation_items.append(item)
                
        # Phase 5: Unmatched bank transactions
        for bank_idx, bank_row in bank_transactions.iterrows():
            if bank_idx not in matched_bank_ids:
                item = ReconciliationItem(
                    item_id=f"unmatched_bank_{len(reconciliation_items)+1}",
                    transaction_date=bank_row["date"],
                    book_amount=None,
                    bank_amount=bank_row["amount"],
                    difference=-bank_row["amount"],
                    status=ReconciliationStatus.UNMATCHED_BANK,
                    description="No matching book transaction found",
                    counterparty=bank_row.get("counterparty"),
                    confidence_score=0.6,
                    suggested_action="Book missing transaction or investigate bank error"
                )
                reconciliation_items.append(item)
                
        return reconciliation_items
        
    def _is_exact_match(self, book_row: pd.Series, bank_row: pd.Series) -> bool:
        """Check if two transactions are an exact match."""
        amount_match = abs(book_row["amount"] - bank_row["amount"]) <= self.matching_config["exact_match_tolerance"]
        date_match = abs((book_row["date"] - bank_row["date"]).days) <= 1
        return amount_match and date_match
        
    def _is_timing_difference_match(self, book_row: pd.Series, bank_row: pd.Series) -> bool:
        """Check if two transactions match with timing differences."""
        amount_match = abs(book_row["amount"] - bank_row["amount"]) <= self.matching_config["exact_match_tolerance"]
        date_diff = abs((book_row["date"] - bank_row["date"]).days)
        timing_acceptable = date_diff <= self.matching_config["date_tolerance_days"]
        return amount_match and timing_acceptable and date_diff > 1
        
    def _is_amount_difference_match(self, book_row: pd.Series, bank_row: pd.Series) -> bool:
        """Check if two transactions match with amount differences."""
        date_match = abs((book_row["date"] - bank_row["date"]).days) <= 1
        
        if book_row["amount"] != 0:
            amount_diff_percent = abs((book_row["amount"] - bank_row["amount"]) / book_row["amount"])
            amount_acceptable = amount_diff_percent <= self.matching_config["amount_tolerance_percent"]
        else:
            amount_acceptable = abs(bank_row["amount"]) <= self.matching_config["exact_match_tolerance"]
            
        return date_match and amount_acceptable
        
    def generate_reconciliation_summary(self, reports: List[ReconciliationReport]) -> Dict[str, Any]:
        """Generate summary across multiple reconciliation reports."""
        if not reports:
            return {"error": "No reconciliation reports provided"}
            
        summary = {
            "total_accounts": len(reports),
            "reconciliation_date": reports[0].reconciliation_date.isoformat(),
            "overall_statistics": {
                "total_items": sum(r.total_items for r in reports),
                "total_matched": sum(r.matched_items for r in reports),
                "total_unmatched": sum(r.unmatched_items for r in reports),
                "average_confidence": sum(r.confidence_score for r in reports) / len(reports),
                "total_difference": sum(r.net_difference for r in reports)
            },
            "by_account": {},
            "action_items": []
        }
        
        # Calculate match rate
        total_items = summary["overall_statistics"]["total_items"]
        if total_items > 0:
            summary["overall_statistics"]["match_rate"] = summary["overall_statistics"]["total_matched"] / total_items
        else:
            summary["overall_statistics"]["match_rate"] = 1.0
            
        # Account-level details
        for report in reports:
            summary["by_account"][report.account_id] = {
                "entity": report.entity,
                "book_balance": report.book_balance,
                "bank_balance": report.bank_balance,
                "difference": report.net_difference,
                "match_rate": report.matched_items / report.total_items if report.total_items > 0 else 1.0,
                "confidence": report.confidence_score,
                "status_breakdown": report.items_by_status
            }
            
        # Generate action items
        for report in reports:
            high_priority_items = [
                item for item in report.items 
                if item.status in [ReconciliationStatus.REQUIRES_INVESTIGATION, 
                                 ReconciliationStatus.UNMATCHED_BOOK,
                                 ReconciliationStatus.UNMATCHED_BANK] and
                abs(item.difference) > 1000  # Focus on items > $1K
            ]
            
            for item in high_priority_items:
                summary["action_items"].append({
                    "account_id": report.account_id,
                    "entity": report.entity,
                    "item_id": item.item_id,
                    "amount": item.difference,
                    "status": item.status.value,
                    "action": item.suggested_action,
                    "priority": "high" if abs(item.difference) > 10000 else "medium"
                })
                
        return summary
        
    def auto_approve_matches(self, report: ReconciliationReport) -> Dict[str, Any]:
        """Auto-approve high-confidence matches."""
        auto_approved = []
        requires_review = []
        
        for item in report.items:
            if (item.confidence_score >= self.matching_config["auto_approve_threshold"] and 
                item.status == ReconciliationStatus.MATCHED):
                auto_approved.append(item.item_id)
            elif item.status != ReconciliationStatus.MATCHED:
                requires_review.append({
                    "item_id": item.item_id,
                    "status": item.status.value,
                    "difference": item.difference,
                    "confidence": item.confidence_score,
                    "action": item.suggested_action
                })
                
        result = {
            "auto_approved_count": len(auto_approved),
            "requires_review_count": len(requires_review),
            "auto_approved_items": auto_approved,
            "requires_review": requires_review,
            "approval_rate": len(auto_approved) / len(report.items) if report.items else 0
        }
        
        self.logger.info("Auto-approval completed",
                        entity=report.entity, account=report.account_id,
                        auto_approved=len(auto_approved),
                        requires_review=len(requires_review))
        
        return result