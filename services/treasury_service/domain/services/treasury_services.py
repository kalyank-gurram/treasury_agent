"""Domain services for complex business logic."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from statistics import mean, stdev

from ..entities.treasury import Payment, Transaction, Counterparty
from ..value_objects.treasury import EntityId, Money, PaymentStatus
from ..repositories.interfaces import (
    PaymentRepository, TransactionRepository, CounterpartyRepository, AccountRepository
)


class PaymentApprovalService:
    """Domain service for payment approval logic."""
    
    def __init__(
        self,
        payment_repo: PaymentRepository,
        transaction_repo: TransactionRepository,
        counterparty_repo: CounterpartyRepository
    ):
        self._payment_repo = payment_repo
        self._transaction_repo = transaction_repo
        self._counterparty_repo = counterparty_repo
    
    async def can_approve_payment(self, payment: Payment) -> tuple[bool, str]:
        """Determine if a payment can be approved based on business rules."""
        
        # Rule 1: Payment must be pending
        if not payment.is_pending():
            return False, f"Payment is not pending (status: {payment.status})"
        
        # Rule 2: Large payments require dual approval (mock check)
        if payment.amount.amount > Decimal("250000"):
            # In real system, check if dual approval exists
            return True, "Large payment - dual approval required"
        
        # Rule 3: Check counterparty risk
        counterparty = await self._counterparty_repo.find_by_name(payment.counterparty)
        if counterparty and not counterparty.is_active:
            return False, "Counterparty is inactive"
        
        # Rule 4: Check if payment is significantly overdue
        if payment.is_overdue():
            days_overdue = (date.today() - payment.due_date).days
            if days_overdue > 30:
                return False, f"Payment is {days_overdue} days overdue"
        
        return True, "Payment approved"
    
    async def auto_approve_eligible_payments(self, entity_id: EntityId) -> List[Payment]:
        """Auto-approve payments that meet criteria."""
        pending_payments = await self._payment_repo.find_by_status(
            PaymentStatus.PENDING, entity_id
        )
        
        approved_payments = []
        for payment in pending_payments:
            can_approve, _ = await self.can_approve_payment(payment)
            
            # Auto-approve small intra-company payments
            if (can_approve and 
                payment.amount.amount < Decimal("1000000") and
                "intra" in payment.description.lower()):
                
                payment.approve()
                await self._payment_repo.save(payment)
                approved_payments.append(payment)
        
        return approved_payments


class RiskAnalysisService:
    """Domain service for risk analysis and anomaly detection."""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self._transaction_repo = transaction_repo
    
    async def calculate_counterparty_exposure(
        self,
        entity_id: EntityId
    ) -> List[Dict[str, Any]]:
        """Calculate counterparty exposure analysis."""
        
        end_date = date.today()
        start_date = date.today().replace(day=1)  # Start of current month
        
        transactions = await self._transaction_repo.find_by_entity(
            entity_id, start_date, end_date
        )
        
        exposure_map: Dict[str, Dict[str, Any]] = {}
        
        for tx in transactions:
            cp = tx.counterparty
            if cp not in exposure_map:
                exposure_map[cp] = {
                    "counterparty": cp,
                    "total_outflow": Decimal(0),
                    "total_inflow": Decimal(0),
                    "net_exposure": Decimal(0),
                    "transaction_count": 0
                }
            
            entry = exposure_map[cp]
            if tx.is_outflow():
                entry["total_outflow"] += abs(tx.amount.amount)
            else:
                entry["total_inflow"] += tx.amount.amount
            
            entry["transaction_count"] += 1
            entry["net_exposure"] = entry["total_outflow"] - entry["total_inflow"]
        
        return sorted(
            exposure_map.values(),
            key=lambda x: x["total_outflow"],
            reverse=True
        )
    
    async def detect_anomalous_transactions(
        self,
        entity_id: EntityId,
        z_threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalous transactions using statistical analysis."""
        
        # Get last 90 days of transactions
        end_date = date.today()
        start_date = date.today().replace(day=end_date.day - 90) if end_date.day > 90 else date(end_date.year - 1, 12, 31)
        
        transactions = await self._transaction_repo.find_by_entity(
            entity_id, start_date, end_date
        )
        
        if len(transactions) < 10:
            return []  # Not enough data for analysis
        
        # Calculate statistics for outflows
        outflows = [abs(tx.amount.amount) for tx in transactions if tx.is_outflow()]
        
        if len(outflows) < 5:
            return []
        
        mean_outflow = mean(outflows)
        std_outflow = stdev(outflows)
        
        anomalies = []
        for tx in transactions:
            if tx.is_outflow():
                z_score = (abs(tx.amount.amount) - mean_outflow) / (std_outflow + 1e-6)
                if abs(z_score) > z_threshold:
                    anomalies.append({
                        "transaction_id": str(tx.id),
                        "date": tx.transaction_date.isoformat(),
                        "amount": float(tx.amount.amount),
                        "counterparty": tx.counterparty,
                        "z_score": round(z_score, 2),
                        "category": tx.category.value
                    })
        
        return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)


class WorkingCapitalService:
    """Domain service for working capital calculations."""
    
    def __init__(self, transaction_repo: TransactionRepository):
        self._transaction_repo = transaction_repo
    
    async def calculate_dso_dpo(self, entity_id: EntityId) -> Dict[str, Optional[float]]:
        """Calculate Days Sales Outstanding and Days Payable Outstanding."""
        
        # Get transactions for DSO/DPO calculation
        end_date = date.today()
        start_date = date.today().replace(day=1)  # Current month
        
        transactions = await self._transaction_repo.find_by_entity(
            entity_id, start_date, end_date
        )
        
        ar_transactions = [tx for tx in transactions if tx.category.value == "AR"]
        ap_transactions = [tx for tx in transactions if tx.category.value == "AP"]
        
        # Calculate DSO (simplified)
        dso = None
        if ar_transactions:
            total_ar = sum(tx.amount.amount for tx in ar_transactions)
            avg_daily_sales = total_ar / 30  # Approximate
            if avg_daily_sales > 0:
                dso = float(total_ar / avg_daily_sales)
        
        # Calculate DPO (simplified)
        dpo = None
        if ap_transactions:
            total_ap = sum(abs(tx.amount.amount) for tx in ap_transactions)
            avg_daily_purchases = total_ap / 30  # Approximate
            if avg_daily_purchases > 0:
                dpo = float(total_ap / avg_daily_purchases)
        
        return {
            "dso": dso,
            "dpo": dpo,
            "calculation_date": end_date.isoformat()
        }


class TreasuryDomainService:
    """Central domain service coordinating treasury operations."""
    
    def __init__(
        self,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        payment_repo: PaymentRepository,
        counterparty_repo: CounterpartyRepository
    ):
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.payment_repo = payment_repo
        self.counterparty_repo = counterparty_repo
    
    def get_accounts_by_entity(self, entity_id: EntityId) -> list:
        """Get accounts for an entity."""
        try:
            return self.account_repo.find_by_entity(entity_id)
        except (AttributeError, NotImplementedError):
            return []  # Return empty list if not implemented
    
    def get_pending_payments(self) -> list:
        """Get pending payments.""" 
        try:
            return self.payment_repo.find_by_status(PaymentStatus.PENDING)
        except (AttributeError, NotImplementedError):
            return []  # Return empty list if not implemented


# Alias for backward compatibility
RiskAssessmentService = RiskAnalysisService