"""Collections optimization engine for AR management."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from .infrastructure.observability import get_observability_manager


class CollectionPriority(Enum):
    """Collection priority levels."""
    CRITICAL = "critical"      # >90 days, high value
    HIGH = "high"             # >60 days or high value
    MEDIUM = "medium"         # 30-60 days
    LOW = "low"              # <30 days
    MAINTENANCE = "maintenance"  # Small amounts, low risk


class CollectionAction(Enum):
    """Recommended collection actions."""
    IMMEDIATE_CALL = "immediate_call"
    EMAIL_REMINDER = "email_reminder"
    FORMAL_NOTICE = "formal_notice"
    PAYMENT_PLAN = "payment_plan"
    LEGAL_ACTION = "legal_action"
    WRITE_OFF = "write_off"
    MONITOR = "monitor"


@dataclass
class CustomerRiskProfile:
    """Customer risk and payment behavior profile."""
    customer_id: str
    payment_history_score: float  # 0-100, higher is better
    average_days_to_pay: float
    payment_consistency: float   # 0-1, higher is more consistent
    credit_limit: float
    current_exposure: float
    dispute_frequency: float     # disputes per year
    payment_methods: List[str]
    last_payment_date: Optional[datetime] = None
    risk_category: str = "medium"
    

@dataclass
class CollectionRecommendation:
    """Individual collection recommendation."""
    invoice_id: str
    customer_id: str
    customer_name: str
    invoice_amount: float
    days_outstanding: int
    priority: CollectionPriority
    recommended_action: CollectionAction
    expected_collection_date: datetime
    collection_probability: float
    potential_recovery: float
    contact_sequence: List[Dict[str, Any]]
    risk_factors: List[str]
    suggested_message: str
    

@dataclass
class CollectionsReport:
    """Collections optimization report."""
    report_date: datetime
    total_ar: float
    aged_ar_buckets: Dict[str, float]
    recommendations: List[CollectionRecommendation]
    expected_collections: Dict[str, float]  # By week
    risk_metrics: Dict[str, float]
    action_summary: Dict[str, int]
    

class CollectionsOptimizer:
    """Intelligent collections optimization engine."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("cash_management.collections")
        
        # Configuration parameters
        self.config = {
            # Aging thresholds
            "current_days": 30,
            "early_days": 60,
            "late_days": 90,
            "critical_days": 120,
            
            # Priority thresholds
            "high_value_threshold": 10000,
            "critical_value_threshold": 50000,
            
            # Collection parameters
            "max_collection_attempts": 5,
            "legal_action_threshold": 120,
            "write_off_threshold": 180,
            "write_off_amount_limit": 1000,
            
            # Probability factors
            "base_collection_probability": 0.85,
            "aging_decay_factor": 0.02,  # 2% decline per day
            "customer_risk_weight": 0.3
        }
        
    def optimize_collections(self, entity: str, as_of_date: Optional[datetime] = None) -> CollectionsReport:
        """Generate optimized collections strategy."""
        if as_of_date is None:
            as_of_date = datetime.now()
            
        self.logger.info("Starting collections optimization",
                        entity=entity, as_of_date=as_of_date.isoformat())
        
        try:
            # Get AR data
            ar_data = self._get_ar_data(entity, as_of_date)
            
            if ar_data.empty:
                return self._empty_report(entity, as_of_date)
                
            # Get customer risk profiles
            customer_profiles = self._build_customer_profiles(ar_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(ar_data, customer_profiles, as_of_date)
            
            # Calculate metrics
            total_ar = ar_data["outstanding_amount"].sum()
            aged_buckets = self._calculate_aged_buckets(ar_data, as_of_date)
            expected_collections = self._forecast_collections(recommendations)
            risk_metrics = self._calculate_risk_metrics(ar_data, recommendations)
            action_summary = self._summarize_actions(recommendations)
            
            report = CollectionsReport(
                report_date=as_of_date,
                total_ar=total_ar,
                aged_ar_buckets=aged_buckets,
                recommendations=recommendations,
                expected_collections=expected_collections,
                risk_metrics=risk_metrics,
                action_summary=action_summary
            )
            
            self.logger.info("Collections optimization completed",
                           entity=entity, total_ar=total_ar,
                           recommendations_count=len(recommendations),
                           high_priority_count=len([r for r in recommendations if r.priority in [CollectionPriority.CRITICAL, CollectionPriority.HIGH]]))
            
            # Record metrics
            self.observability.record_metric(
                "gauge", "total_ar_amount", total_ar,
                {"entity": entity}
            )
            
            self.observability.record_metric(
                "counter", "collections_optimizations_total", 1,
                {"entity": entity}
            )
            
            return report
            
        except Exception as e:
            self.logger.error("Collections optimization failed",
                            entity=entity, error=str(e), error_type=type(e).__name__)
            raise
            
    def _get_ar_data(self, entity: str, as_of_date: datetime) -> pd.DataFrame:
        """Get accounts receivable data."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        
        # Generate realistic AR data based on transaction history
        transactions = api.transactions.copy()
        
        # Filter by entity
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
            
        # Create AR records from outbound transactions (positive amounts to customers)
        ar_transactions = transactions[
            (transactions["amount"] > 0) & 
            (transactions["counterparty"].str.contains("Customer|Client", na=False))
        ].copy()
        
        if ar_transactions.empty:
            # Generate sample AR data for demo
            customers = ["Acme Corp", "TechStart Inc", "Global Manufacturing", "Retail Chain LLC", "Service Co"]
            ar_data = []
            
            for i, customer in enumerate(customers):
                # Generate multiple invoices per customer
                for j in range(np.random.randint(1, 4)):
                    invoice_date = as_of_date - timedelta(days=np.random.randint(10, 150))
                    amount = np.random.uniform(5000, 75000)
                    
                    ar_data.append({
                        "invoice_id": f"INV-{i+1:03d}-{j+1:02d}",
                        "customer_id": f"CUST-{i+1:03d}",
                        "customer_name": customer,
                        "invoice_date": invoice_date,
                        "due_date": invoice_date + timedelta(days=30),
                        "original_amount": amount,
                        "outstanding_amount": amount * np.random.uniform(0.3, 1.0),  # Partial payments
                        "currency": "USD",
                        "payment_terms": "NET30"
                    })
                    
            ar_df = pd.DataFrame(ar_data)
        else:
            # Convert transactions to AR format
            ar_df = ar_transactions.rename(columns={
                "counterparty": "customer_name",
                "amount": "outstanding_amount"
            }).copy()
            
            ar_df["invoice_id"] = "INV-" + ar_df.index.astype(str).str.zfill(6)
            ar_df["customer_id"] = "CUST-" + (ar_df["customer_name"].astype("category").cat.codes + 1).astype(str).str.zfill(3)
            ar_df["invoice_date"] = pd.to_datetime(ar_df["date"])
            ar_df["due_date"] = ar_df["invoice_date"] + timedelta(days=30)
            ar_df["original_amount"] = ar_df["outstanding_amount"]
            ar_df["currency"] = "USD"
            ar_df["payment_terms"] = "NET30"
            
        return ar_df
        
    def _build_customer_profiles(self, ar_data: pd.DataFrame) -> Dict[str, CustomerRiskProfile]:
        """Build customer risk profiles based on historical data."""
        profiles = {}
        
        for customer_id in ar_data["customer_id"].unique():
            customer_invoices = ar_data[ar_data["customer_id"] == customer_id]
            
            # Calculate payment behavior metrics
            total_exposure = customer_invoices["outstanding_amount"].sum()
            avg_invoice_size = customer_invoices["original_amount"].mean()
            
            # Simulate payment history score (in real system, this would be calculated from payment data)
            base_score = 70 + np.random.normal(0, 15)  # Base score with variation
            payment_history_score = max(10, min(100, base_score))
            
            # Simulate other metrics
            avg_days_to_pay = 30 + np.random.exponential(10)  # Exponential distribution for payment delays
            payment_consistency = max(0.1, 1 - (avg_days_to_pay - 30) / 100)
            
            profile = CustomerRiskProfile(
                customer_id=customer_id,
                payment_history_score=payment_history_score,
                average_days_to_pay=avg_days_to_pay,
                payment_consistency=payment_consistency,
                credit_limit=total_exposure * 2,  # Assume credit limit is 2x current exposure
                current_exposure=total_exposure,
                dispute_frequency=np.random.poisson(0.5),  # Average 0.5 disputes per year
                payment_methods=["ACH", "Wire", "Check"],
                risk_category="low" if payment_history_score > 80 else "medium" if payment_history_score > 60 else "high"
            )
            
            profiles[customer_id] = profile
            
        return profiles
        
    def _generate_recommendations(self, ar_data: pd.DataFrame, customer_profiles: Dict[str, CustomerRiskProfile], 
                                as_of_date: datetime) -> List[CollectionRecommendation]:
        """Generate collection recommendations for each invoice."""
        recommendations = []
        
        for _, invoice in ar_data.iterrows():
            # Calculate days outstanding
            days_outstanding = (as_of_date - pd.to_datetime(invoice["due_date"])).days
            
            # Get customer profile
            profile = customer_profiles.get(invoice["customer_id"])
            if not profile:
                continue
                
            # Determine priority
            priority = self._calculate_priority(invoice, days_outstanding, profile)
            
            # Determine recommended action
            action = self._determine_action(invoice, days_outstanding, profile, priority)
            
            # Calculate collection probability
            probability = self._calculate_collection_probability(invoice, days_outstanding, profile)
            
            # Expected collection date
            expected_date = self._estimate_collection_date(as_of_date, days_outstanding, profile, action)
            
            # Generate contact sequence
            contact_sequence = self._generate_contact_sequence(action, profile)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(invoice, days_outstanding, profile)
            
            # Generate suggested message
            message = self._generate_collection_message(action, invoice, profile)
            
            recommendation = CollectionRecommendation(
                invoice_id=invoice["invoice_id"],
                customer_id=invoice["customer_id"],
                customer_name=invoice["customer_name"],
                invoice_amount=invoice["outstanding_amount"],
                days_outstanding=days_outstanding,
                priority=priority,
                recommended_action=action,
                expected_collection_date=expected_date,
                collection_probability=probability,
                potential_recovery=invoice["outstanding_amount"] * probability,
                contact_sequence=contact_sequence,
                risk_factors=risk_factors,
                suggested_message=message
            )
            
            recommendations.append(recommendation)
            
        # Sort by priority and amount
        priority_order = {CollectionPriority.CRITICAL: 0, CollectionPriority.HIGH: 1, 
                         CollectionPriority.MEDIUM: 2, CollectionPriority.LOW: 3, 
                         CollectionPriority.MAINTENANCE: 4}
        
        recommendations.sort(key=lambda x: (priority_order[x.priority], -x.invoice_amount))
        
        return recommendations
        
    def _calculate_priority(self, invoice: pd.Series, days_outstanding: int, 
                          profile: CustomerRiskProfile) -> CollectionPriority:
        """Calculate collection priority based on multiple factors."""
        amount = invoice["outstanding_amount"]
        
        # Critical: High risk or very old
        if (days_outstanding >= self.config["critical_days"] or
            amount >= self.config["critical_value_threshold"] or
            profile.risk_category == "high"):
            return CollectionPriority.CRITICAL
            
        # High: Moderately old or high value
        if (days_outstanding >= self.config["late_days"] or
            amount >= self.config["high_value_threshold"]):
            return CollectionPriority.HIGH
            
        # Medium: Early stage overdue
        if days_outstanding >= self.config["current_days"]:
            return CollectionPriority.MEDIUM
            
        # Low: Not yet due but needs monitoring
        if days_outstanding >= 0:
            return CollectionPriority.LOW
            
        # Maintenance: Future dated or very small amounts
        return CollectionPriority.MAINTENANCE
        
    def _determine_action(self, invoice: pd.Series, days_outstanding: int, 
                         profile: CustomerRiskProfile, priority: CollectionPriority) -> CollectionAction:
        """Determine recommended collection action."""
        amount = invoice["outstanding_amount"]
        
        # Write-off criteria
        if (days_outstanding >= self.config["write_off_threshold"] and
            amount <= self.config["write_off_amount_limit"]):
            return CollectionAction.WRITE_OFF
            
        # Legal action criteria  
        if (days_outstanding >= self.config["legal_action_threshold"] and
            amount >= self.config["high_value_threshold"] and
            profile.payment_history_score < 40):
            return CollectionAction.LEGAL_ACTION
            
        # Based on priority and customer profile
        if priority == CollectionPriority.CRITICAL:
            if profile.risk_category == "high":
                return CollectionAction.FORMAL_NOTICE
            else:
                return CollectionAction.IMMEDIATE_CALL
                
        elif priority == CollectionPriority.HIGH:
            if profile.payment_consistency < 0.5:
                return CollectionAction.PAYMENT_PLAN
            else:
                return CollectionAction.IMMEDIATE_CALL
                
        elif priority == CollectionPriority.MEDIUM:
            return CollectionAction.EMAIL_REMINDER
            
        else:
            return CollectionAction.MONITOR
            
    def _calculate_collection_probability(self, invoice: pd.Series, days_outstanding: int,
                                        profile: CustomerRiskProfile) -> float:
        """Calculate probability of successful collection."""
        base_prob = self.config["base_collection_probability"]
        
        # Aging factor - probability decreases with age
        aging_factor = max(0.1, 1 - (days_outstanding * self.config["aging_decay_factor"]))
        
        # Customer risk factor
        risk_score = profile.payment_history_score / 100
        risk_factor = (risk_score * self.config["customer_risk_weight"] + 
                      (1 - self.config["customer_risk_weight"]))
        
        # Amount factor - larger amounts have slightly lower collection rates
        amount_factor = max(0.8, 1 - (invoice["outstanding_amount"] / 1000000) * 0.1)
        
        probability = base_prob * aging_factor * risk_factor * amount_factor
        
        return max(0.05, min(0.99, probability))
        
    def _estimate_collection_date(self, as_of_date: datetime, days_outstanding: int,
                                profile: CustomerRiskProfile, action: CollectionAction) -> datetime:
        """Estimate when collection will occur."""
        # Base collection time based on action
        action_days = {
            CollectionAction.IMMEDIATE_CALL: 7,
            CollectionAction.EMAIL_REMINDER: 14,
            CollectionAction.FORMAL_NOTICE: 21,
            CollectionAction.PAYMENT_PLAN: 30,
            CollectionAction.LEGAL_ACTION: 60,
            CollectionAction.WRITE_OFF: 0,
            CollectionAction.MONITOR: 30
        }
        
        base_days = action_days.get(action, 30)
        
        # Adjust based on customer profile
        customer_adjustment = profile.average_days_to_pay - 30  # Baseline is 30 days
        
        total_days = base_days + max(0, customer_adjustment)
        
        return as_of_date + timedelta(days=int(total_days))
        
    def _generate_contact_sequence(self, action: CollectionAction, 
                                 profile: CustomerRiskProfile) -> List[Dict[str, Any]]:
        """Generate recommended contact sequence."""
        sequence = []
        
        if action in [CollectionAction.IMMEDIATE_CALL, CollectionAction.FORMAL_NOTICE]:
            sequence.append({
                "day": 0,
                "method": "phone",
                "message_type": "urgent_payment_request",
                "follow_up": True
            })
            sequence.append({
                "day": 3,
                "method": "email",
                "message_type": "payment_confirmation",
                "follow_up": True
            })
            
        elif action == CollectionAction.EMAIL_REMINDER:
            sequence.append({
                "day": 0,
                "method": "email", 
                "message_type": "friendly_reminder",
                "follow_up": True
            })
            sequence.append({
                "day": 7,
                "method": "email",
                "message_type": "second_notice",
                "follow_up": True
            })
            
        elif action == CollectionAction.PAYMENT_PLAN:
            sequence.append({
                "day": 0,
                "method": "phone",
                "message_type": "payment_plan_offer",
                "follow_up": True
            })
            
        return sequence
        
    def _identify_risk_factors(self, invoice: pd.Series, days_outstanding: int,
                             profile: CustomerRiskProfile) -> List[str]:
        """Identify collection risk factors."""
        factors = []
        
        if days_outstanding > 90:
            factors.append("Extended aging period")
            
        if profile.payment_history_score < 60:
            factors.append("Poor payment history")
            
        if profile.current_exposure > profile.credit_limit * 0.8:
            factors.append("High credit utilization")
            
        if profile.dispute_frequency > 2:
            factors.append("High dispute frequency")
            
        if invoice["outstanding_amount"] > profile.credit_limit * 0.2:
            factors.append("Large invoice relative to credit limit")
            
        return factors
        
    def _generate_collection_message(self, action: CollectionAction, invoice: pd.Series,
                                   profile: CustomerRiskProfile) -> str:
        """Generate personalized collection message."""
        customer_name = invoice["customer_name"]
        amount = invoice["outstanding_amount"]
        invoice_id = invoice["invoice_id"]
        
        if action == CollectionAction.EMAIL_REMINDER:
            return f"Dear {customer_name}, this is a friendly reminder that invoice {invoice_id} for ${amount:,.2f} is past due. Please arrange payment at your earliest convenience."
            
        elif action == CollectionAction.IMMEDIATE_CALL:
            return f"Urgent: Invoice {invoice_id} for ${amount:,.2f} requires immediate attention. Please call to arrange payment today."
            
        elif action == CollectionAction.FORMAL_NOTICE:
            return f"FORMAL NOTICE: Invoice {invoice_id} for ${amount:,.2f} is significantly overdue. Immediate payment is required to avoid further action."
            
        elif action == CollectionAction.PAYMENT_PLAN:
            return f"We understand payment challenges occur. Let's discuss a payment plan for invoice {invoice_id} (${amount:,.2f}) that works for both parties."
            
        else:
            return f"Please contact us regarding invoice {invoice_id} for ${amount:,.2f}."
            
    def _calculate_aged_buckets(self, ar_data: pd.DataFrame, as_of_date: datetime) -> Dict[str, float]:
        """Calculate aged AR buckets."""
        buckets = {
            "current": 0.0,
            "1-30_days": 0.0, 
            "31-60_days": 0.0,
            "61-90_days": 0.0,
            "over_90_days": 0.0
        }
        
        for _, invoice in ar_data.iterrows():
            days_outstanding = (as_of_date - pd.to_datetime(invoice["due_date"])).days
            amount = invoice["outstanding_amount"]
            
            if days_outstanding <= 0:
                buckets["current"] += amount
            elif days_outstanding <= 30:
                buckets["1-30_days"] += amount
            elif days_outstanding <= 60:
                buckets["31-60_days"] += amount
            elif days_outstanding <= 90:
                buckets["61-90_days"] += amount
            else:
                buckets["over_90_days"] += amount
                
        return buckets
        
    def _forecast_collections(self, recommendations: List[CollectionRecommendation]) -> Dict[str, float]:
        """Forecast expected collections by week."""
        collections = {}
        
        for rec in recommendations:
            if rec.recommended_action == CollectionAction.WRITE_OFF:
                continue
                
            # Get week key
            week_start = rec.expected_collection_date.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start -= timedelta(days=week_start.weekday())  # Monday of that week
            week_key = week_start.strftime("%Y-W%U")
            
            if week_key not in collections:
                collections[week_key] = 0.0
                
            collections[week_key] += rec.potential_recovery
            
        return collections
        
    def _calculate_risk_metrics(self, ar_data: pd.DataFrame, 
                              recommendations: List[CollectionRecommendation]) -> Dict[str, float]:
        """Calculate collection risk metrics."""
        total_ar = ar_data["outstanding_amount"].sum()
        
        if total_ar == 0:
            return {}
            
        # Calculate metrics
        high_risk_amount = sum(rec.invoice_amount for rec in recommendations 
                             if rec.priority == CollectionPriority.CRITICAL)
        
        low_probability_amount = sum(rec.invoice_amount for rec in recommendations
                                   if rec.collection_probability < 0.5)
        
        write_off_amount = sum(rec.invoice_amount for rec in recommendations
                             if rec.recommended_action == CollectionAction.WRITE_OFF)
        
        return {
            "total_ar": total_ar,
            "high_risk_percentage": (high_risk_amount / total_ar) * 100,
            "low_probability_percentage": (low_probability_amount / total_ar) * 100,
            "expected_write_off_percentage": (write_off_amount / total_ar) * 100,
            "average_collection_probability": sum(rec.collection_probability for rec in recommendations) / len(recommendations) if recommendations else 0
        }
        
    def _summarize_actions(self, recommendations: List[CollectionRecommendation]) -> Dict[str, int]:
        """Summarize recommended actions."""
        summary = {}
        
        for action in CollectionAction:
            summary[action.value] = len([rec for rec in recommendations if rec.recommended_action == action])
            
        return summary
        
    def _empty_report(self, entity: str, as_of_date: datetime) -> CollectionsReport:
        """Generate empty report when no AR data exists."""
        return CollectionsReport(
            report_date=as_of_date,
            total_ar=0.0,
            aged_ar_buckets={},
            recommendations=[],
            expected_collections={},
            risk_metrics={},
            action_summary={}
        )
        
    def generate_collection_workflow(self, recommendations: List[CollectionRecommendation]) -> Dict[str, Any]:
        """Generate prioritized collection workflow for the team."""
        # Group by priority and action
        workflow = {
            "daily_tasks": [],
            "weekly_tasks": [],
            "urgent_items": [],
            "summary": {
                "total_items": len(recommendations),
                "total_value": sum(rec.invoice_amount for rec in recommendations),
                "expected_recovery": sum(rec.potential_recovery for rec in recommendations)
            }
        }
        
        # Process urgent items (calls)
        urgent_items = [rec for rec in recommendations 
                       if rec.recommended_action == CollectionAction.IMMEDIATE_CALL]
        
        for rec in urgent_items[:10]:  # Limit to top 10 urgent items
            workflow["urgent_items"].append({
                "customer": rec.customer_name,
                "amount": rec.invoice_amount,
                "days_outstanding": rec.days_outstanding,
                "message": rec.suggested_message,
                "priority": rec.priority.value
            })
            
        # Daily tasks (emails, reminders)
        daily_actions = [CollectionAction.EMAIL_REMINDER, CollectionAction.FORMAL_NOTICE]
        daily_items = [rec for rec in recommendations if rec.recommended_action in daily_actions]
        
        for rec in daily_items:
            workflow["daily_tasks"].append({
                "action": rec.recommended_action.value,
                "customer": rec.customer_name,
                "amount": rec.invoice_amount,
                "message": rec.suggested_message
            })
            
        # Weekly tasks (payment plans, follow-ups)
        weekly_actions = [CollectionAction.PAYMENT_PLAN, CollectionAction.LEGAL_ACTION]
        weekly_items = [rec for rec in recommendations if rec.recommended_action in weekly_actions]
        
        for rec in weekly_items:
            workflow["weekly_tasks"].append({
                "action": rec.recommended_action.value,
                "customer": rec.customer_name,
                "amount": rec.invoice_amount,
                "expected_date": rec.expected_collection_date.isoformat()
            })
            
        return workflow