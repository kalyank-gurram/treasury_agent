"""Payment prioritization engine for AP optimization."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from .infrastructure.observability import get_observability_manager


class PaymentPriority(Enum):
    """Payment priority levels."""
    CRITICAL = "critical"      # Legal/regulatory, payroll, utilities
    HIGH = "high"             # Key suppliers, early pay discounts
    MEDIUM = "medium"         # Standard suppliers, normal terms
    LOW = "low"              # Non-critical, can be delayed
    STRATEGIC = "strategic"    # Strategic suppliers, relationship management


class PaymentMethod(Enum):
    """Available payment methods."""
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"
    CARD = "card"
    AUTOMATED_CLEARING = "automated_clearing"


@dataclass
class SupplierProfile:
    """Supplier profile for payment optimization."""
    supplier_id: str
    supplier_name: str
    category: str  # e.g., "utilities", "raw_materials", "services"
    payment_terms: str
    early_pay_discount: Optional[float] = None
    discount_days: Optional[int] = None
    preferred_payment_method: PaymentMethod = PaymentMethod.ACH
    strategic_importance: float = 0.5  # 0-1 scale
    credit_rating: str = "A"
    relationship_score: float = 0.5  # 0-1 scale
    average_monthly_spend: float = 0.0
    

@dataclass
class PaymentRecommendation:
    """Individual payment recommendation."""
    invoice_id: str
    supplier_id: str
    supplier_name: str
    invoice_amount: float
    original_due_date: datetime
    recommended_pay_date: datetime
    priority: PaymentPriority
    payment_method: PaymentMethod
    early_pay_discount: Optional[float] = None
    discount_savings: float = 0.0
    cash_impact: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    strategic_rationale: Optional[str] = None
    

@dataclass
class PaymentSchedule:
    """Optimized payment schedule."""
    schedule_date: datetime
    total_payments: float
    payments_by_day: Dict[str, List[PaymentRecommendation]]  # day -> payments
    cash_flow_impact: Dict[str, float]  # day -> net cash flow
    discount_opportunities: Dict[str, float]  # day -> total discounts
    liquidity_requirements: Dict[str, float]  # day -> required cash
    

class PaymentPrioritizer:
    """Intelligent payment prioritization and scheduling engine."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("cash_management.payments")
        
        # Configuration parameters
        self.config = {
            # Priority weights
            "strategic_weight": 0.3,
            "discount_weight": 0.25,
            "relationship_weight": 0.2,
            "cash_flow_weight": 0.15,
            "risk_weight": 0.1,
            
            # Thresholds
            "critical_supplier_categories": ["utilities", "payroll", "tax", "legal", "insurance"],
            "minimum_discount_rate": 0.01,  # 1% minimum discount to consider
            "maximum_delay_days": 30,
            "cash_buffer_percentage": 0.05,  # 5% cash buffer
            
            # Payment method costs
            "payment_costs": {
                PaymentMethod.ACH: 0.50,
                PaymentMethod.WIRE: 25.00,
                PaymentMethod.CHECK: 2.00,
                PaymentMethod.CARD: 0.02,  # 2% of amount
                PaymentMethod.AUTOMATED_CLEARING: 1.00
            }
        }
        
    def optimize_payments(self, entity: str, cash_position: float, 
                         forecast_horizon_days: int = 30,
                         as_of_date: Optional[datetime] = None) -> PaymentSchedule:
        """Generate optimized payment schedule."""
        if as_of_date is None:
            as_of_date = datetime.now()
            
        self.logger.info("Starting payment optimization",
                        entity=entity, cash_position=cash_position,
                        forecast_horizon_days=forecast_horizon_days)
        
        try:
            # Get AP data
            ap_data = self._get_ap_data(entity, as_of_date, forecast_horizon_days)
            
            if ap_data.empty:
                return self._empty_schedule(as_of_date)
                
            # Get supplier profiles
            supplier_profiles = self._build_supplier_profiles(ap_data)
            
            # Generate payment recommendations
            recommendations = self._generate_payment_recommendations(
                ap_data, supplier_profiles, cash_position, as_of_date
            )
            
            # Optimize payment schedule
            schedule = self._optimize_payment_schedule(
                recommendations, cash_position, forecast_horizon_days, as_of_date
            )
            
            self.logger.info("Payment optimization completed",
                           entity=entity, total_payments=schedule.total_payments,
                           recommendations_count=len(sum(schedule.payments_by_day.values(), [])))
            
            # Record metrics
            self.observability.record_metric(
                "gauge", "total_scheduled_payments", schedule.total_payments,
                {"entity": entity}
            )
            
            total_discounts = sum(schedule.discount_opportunities.values())
            self.observability.record_metric(
                "gauge", "payment_discount_opportunities", total_discounts,
                {"entity": entity}
            )
            
            return schedule
            
        except Exception as e:
            self.logger.error("Payment optimization failed",
                            entity=entity, error=str(e), error_type=type(e).__name__)
            raise
            
    def _get_ap_data(self, entity: str, as_of_date: datetime, horizon_days: int) -> pd.DataFrame:
        """Get accounts payable data."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        
        # Generate realistic AP data
        suppliers = [
            ("Acme Utilities", "utilities", "NET15", 0.02, 10),
            ("TechCorp Services", "services", "NET30", None, None), 
            ("Global Raw Materials", "raw_materials", "NET30", 0.015, 10),
            ("Office Supplies Inc", "office", "NET45", 0.01, 15),
            ("Legal Partners LLC", "legal", "NET15", None, None),
            ("Insurance Corp", "insurance", "NET30", None, None),
            ("Maintenance Co", "maintenance", "NET30", 0.02, 10),
            ("Marketing Agency", "marketing", "NET45", None, None)
        ]
        
        ap_data = []
        
        for i, (name, category, terms, discount_rate, discount_days) in enumerate(suppliers):
            # Generate multiple invoices per supplier
            for j in range(np.random.randint(2, 6)):
                invoice_date = as_of_date - timedelta(days=np.random.randint(1, 45))
                
                # Parse payment terms
                if terms == "NET15":
                    due_date = invoice_date + timedelta(days=15)
                elif terms == "NET30":
                    due_date = invoice_date + timedelta(days=30)
                elif terms == "NET45":
                    due_date = invoice_date + timedelta(days=45)
                else:
                    due_date = invoice_date + timedelta(days=30)
                    
                # Skip if outside forecast horizon
                if (due_date - as_of_date).days > horizon_days:
                    continue
                    
                # Generate realistic amounts based on category
                if category in ["utilities", "insurance"]:
                    amount = np.random.uniform(2000, 8000)
                elif category == "raw_materials":
                    amount = np.random.uniform(10000, 50000)
                elif category == "legal":
                    amount = np.random.uniform(5000, 25000)
                else:
                    amount = np.random.uniform(1000, 15000)
                    
                ap_data.append({
                    "invoice_id": f"AP-{i+1:03d}-{j+1:02d}",
                    "supplier_id": f"SUP-{i+1:03d}",
                    "supplier_name": name,
                    "category": category,
                    "invoice_date": invoice_date,
                    "due_date": due_date,
                    "amount": amount,
                    "payment_terms": terms,
                    "early_pay_discount_rate": discount_rate,
                    "discount_days": discount_days,
                    "currency": "USD",
                    "status": "approved"
                })
                
        return pd.DataFrame(ap_data)
        
    def _build_supplier_profiles(self, ap_data: pd.DataFrame) -> Dict[str, SupplierProfile]:
        """Build supplier profiles for optimization."""
        profiles = {}
        
        for supplier_id in ap_data["supplier_id"].unique():
            supplier_invoices = ap_data[ap_data["supplier_id"] == supplier_id]
            first_invoice = supplier_invoices.iloc[0]
            
            # Calculate average monthly spend
            total_amount = supplier_invoices["amount"].sum()
            date_range = (supplier_invoices["due_date"].max() - supplier_invoices["due_date"].min()).days
            monthly_spend = total_amount * (30 / max(1, date_range))
            
            # Determine strategic importance based on category and spend
            category = first_invoice["category"]
            if category in self.config["critical_supplier_categories"]:
                strategic_importance = 0.9
            elif monthly_spend > 20000:
                strategic_importance = 0.8
            elif monthly_spend > 10000:
                strategic_importance = 0.6
            else:
                strategic_importance = 0.4
                
            # Determine payment method based on amount and category
            avg_amount = supplier_invoices["amount"].mean()
            if category in ["utilities", "payroll", "tax"]:
                preferred_method = PaymentMethod.ACH
            elif avg_amount > 25000:
                preferred_method = PaymentMethod.WIRE
            elif category == "office":
                preferred_method = PaymentMethod.CARD
            else:
                preferred_method = PaymentMethod.ACH
                
            profile = SupplierProfile(
                supplier_id=supplier_id,
                supplier_name=first_invoice["supplier_name"],
                category=category,
                payment_terms=first_invoice["payment_terms"],
                early_pay_discount=first_invoice.get("early_pay_discount_rate"),
                discount_days=first_invoice.get("discount_days"),
                preferred_payment_method=preferred_method,
                strategic_importance=strategic_importance,
                relationship_score=strategic_importance * 0.8,  # Correlated with strategic importance
                average_monthly_spend=monthly_spend
            )
            
            profiles[supplier_id] = profile
            
        return profiles
        
    def _generate_payment_recommendations(self, ap_data: pd.DataFrame, 
                                        supplier_profiles: Dict[str, SupplierProfile],
                                        cash_position: float, as_of_date: datetime) -> List[PaymentRecommendation]:
        """Generate payment recommendations for each invoice."""
        recommendations = []
        
        for _, invoice in ap_data.iterrows():
            profile = supplier_profiles.get(invoice["supplier_id"])
            if not profile:
                continue
                
            # Calculate priority
            priority = self._calculate_payment_priority(invoice, profile)
            
            # Determine optimal payment date
            recommended_date = self._calculate_optimal_payment_date(invoice, profile, as_of_date)
            
            # Calculate early pay discount savings
            discount_savings = self._calculate_discount_savings(invoice, profile, recommended_date)
            
            # Assess risk factors
            risk_factors = self._assess_payment_risks(invoice, profile, recommended_date, as_of_date)
            
            # Generate strategic rationale
            rationale = self._generate_strategic_rationale(invoice, profile, priority, discount_savings)
            
            recommendation = PaymentRecommendation(
                invoice_id=invoice["invoice_id"],
                supplier_id=invoice["supplier_id"],
                supplier_name=invoice["supplier_name"],
                invoice_amount=invoice["amount"],
                original_due_date=pd.to_datetime(invoice["due_date"]),
                recommended_pay_date=recommended_date,
                priority=priority,
                payment_method=profile.preferred_payment_method,
                early_pay_discount=profile.early_pay_discount,
                discount_savings=discount_savings,
                cash_impact=invoice["amount"],
                risk_factors=risk_factors,
                strategic_rationale=rationale
            )
            
            recommendations.append(recommendation)
            
        # Sort by priority and strategic value
        priority_order = {PaymentPriority.CRITICAL: 0, PaymentPriority.STRATEGIC: 1,
                         PaymentPriority.HIGH: 2, PaymentPriority.MEDIUM: 3, PaymentPriority.LOW: 4}
        
        recommendations.sort(key=lambda x: (priority_order[x.priority], 
                                          -x.discount_savings, 
                                          x.recommended_pay_date))
        
        return recommendations
        
    def _calculate_payment_priority(self, invoice: pd.Series, profile: SupplierProfile) -> PaymentPriority:
        """Calculate payment priority based on multiple factors."""
        category = profile.category
        
        # Critical suppliers always get highest priority
        if category in self.config["critical_supplier_categories"]:
            return PaymentPriority.CRITICAL
            
        # Strategic suppliers
        if profile.strategic_importance > 0.8:
            return PaymentPriority.STRATEGIC
            
        # High priority for early pay discounts
        if (profile.early_pay_discount and 
            profile.early_pay_discount >= self.config["minimum_discount_rate"]):
            return PaymentPriority.HIGH
            
        # High priority for large suppliers
        if profile.average_monthly_spend > 20000:
            return PaymentPriority.HIGH
            
        # Medium priority for standard suppliers
        if profile.relationship_score > 0.6:
            return PaymentPriority.MEDIUM
            
        # Low priority for others
        return PaymentPriority.LOW
        
    def _calculate_optimal_payment_date(self, invoice: pd.Series, profile: SupplierProfile,
                                      as_of_date: datetime) -> datetime:
        """Calculate optimal payment date considering discounts and cash flow."""
        due_date = pd.to_datetime(invoice["due_date"])
        
        # Critical suppliers - pay immediately if overdue, otherwise on due date
        if profile.category in self.config["critical_supplier_categories"]:
            return max(as_of_date, due_date)
            
        # Early pay discount consideration
        if profile.early_pay_discount and profile.discount_days:
            invoice_date = pd.to_datetime(invoice["invoice_date"])
            discount_deadline = invoice_date + timedelta(days=profile.discount_days)
            
            if discount_deadline >= as_of_date:
                # Check if discount is worthwhile
                annual_rate = (profile.early_pay_discount * 365) / (due_date - discount_deadline).days
                if annual_rate > 0.15:  # 15% annual return threshold
                    return min(discount_deadline, as_of_date + timedelta(days=1))
                    
        # Strategic suppliers - pay on time
        if profile.strategic_importance > 0.7:
            return due_date
            
        # Standard optimization - pay close to due date to preserve cash
        optimal_date = due_date - timedelta(days=2)  # Small buffer before due date
        return max(optimal_date, as_of_date)
        
    def _calculate_discount_savings(self, invoice: pd.Series, profile: SupplierProfile,
                                  recommended_date: datetime) -> float:
        """Calculate potential early pay discount savings."""
        if not profile.early_pay_discount or not profile.discount_days:
            return 0.0
            
        invoice_date = pd.to_datetime(invoice["invoice_date"])
        discount_deadline = invoice_date + timedelta(days=profile.discount_days)
        
        if recommended_date <= discount_deadline:
            return invoice["amount"] * profile.early_pay_discount
            
        return 0.0
        
    def _assess_payment_risks(self, invoice: pd.Series, profile: SupplierProfile,
                            recommended_date: datetime, as_of_date: datetime) -> List[str]:
        """Assess risks associated with payment timing."""
        risks = []
        
        due_date = pd.to_datetime(invoice["due_date"])
        
        # Late payment risk
        if recommended_date > due_date:
            days_late = (recommended_date - due_date).days
            risks.append(f"Late payment by {days_late} days - may impact relationship")
            
        # Critical supplier risk
        if profile.category in self.config["critical_supplier_categories"]:
            if recommended_date > due_date:
                risks.append("Critical supplier - late payment may cause service disruption")
                
        # Large payment risk
        if invoice["amount"] > 50000:
            risks.append("Large payment amount - significant cash flow impact")
            
        # Relationship risk
        if profile.relationship_score > 0.8 and recommended_date > due_date:
            risks.append("High-value relationship - late payment may damage partnership")
            
        return risks
        
    def _generate_strategic_rationale(self, invoice: pd.Series, profile: SupplierProfile,
                                    priority: PaymentPriority, discount_savings: float) -> str:
        """Generate strategic rationale for payment timing."""
        if priority == PaymentPriority.CRITICAL:
            return f"Critical supplier ({profile.category}) - immediate payment required for business continuity"
            
        if discount_savings > 0:
            roi = (discount_savings * 365) / ((pd.to_datetime(invoice["due_date"]) - datetime.now()).days * invoice["amount"])
            return f"Early payment captures {discount_savings:.2f} discount (${discount_savings:.0f}) with {roi*100:.1f}% annualized return"
            
        if priority == PaymentPriority.STRATEGIC:
            return f"Strategic supplier - timely payment maintains {profile.relationship_score*100:.0f}% relationship score"
            
        return f"Standard payment optimization - balanced cash flow and supplier relationship management"
        
    def _optimize_payment_schedule(self, recommendations: List[PaymentRecommendation],
                                 initial_cash: float, horizon_days: int, 
                                 as_of_date: datetime) -> PaymentSchedule:
        """Optimize payment schedule considering cash flow constraints."""
        # Initialize schedule
        payments_by_day = {}
        cash_flow_impact = {}
        discount_opportunities = {}
        liquidity_requirements = {}
        
        # Track cash position
        cash_position = initial_cash
        required_buffer = initial_cash * self.config["cash_buffer_percentage"]
        
        # Process each day in the horizon
        for day_offset in range(horizon_days):
            current_date = as_of_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            payments_by_day[date_str] = []
            cash_flow_impact[date_str] = 0.0
            discount_opportunities[date_str] = 0.0
            
            # Get payments scheduled for this day
            daily_payments = [rec for rec in recommendations 
                            if rec.recommended_pay_date.date() == current_date.date()]
            
            # Sort by priority for cash allocation
            daily_payments.sort(key=lambda x: (
                0 if x.priority == PaymentPriority.CRITICAL else
                1 if x.priority == PaymentPriority.STRATEGIC else
                2 if x.priority == PaymentPriority.HIGH else
                3 if x.priority == PaymentPriority.MEDIUM else 4
            ))
            
            # Allocate cash to payments
            for payment in daily_payments:
                # Check if we have sufficient cash
                total_cost = payment.cash_impact + self._calculate_payment_cost(payment)
                
                if cash_position - total_cost >= required_buffer:
                    # Approve payment
                    payments_by_day[date_str].append(payment)
                    cash_position -= total_cost
                    cash_flow_impact[date_str] -= total_cost
                    
                    if payment.discount_savings > 0:
                        discount_opportunities[date_str] += payment.discount_savings
                        
                elif payment.priority == PaymentPriority.CRITICAL:
                    # Critical payments must be made even if it dips into buffer
                    payments_by_day[date_str].append(payment)
                    cash_position -= total_cost
                    cash_flow_impact[date_str] -= total_cost
                    
                    self.logger.warning("Critical payment approved despite cash constraints",
                                      payment_id=payment.invoice_id, 
                                      amount=payment.cash_impact,
                                      remaining_cash=cash_position)
                else:
                    # Defer non-critical payment
                    self.logger.info("Payment deferred due to cash constraints",
                                   payment_id=payment.invoice_id,
                                   amount=payment.cash_impact,
                                   available_cash=cash_position - required_buffer)
                    
            liquidity_requirements[date_str] = cash_position
            
        # Calculate total payments
        total_payments = sum(
            sum(payment.cash_impact for payment in daily_payments)
            for daily_payments in payments_by_day.values()
        )
        
        return PaymentSchedule(
            schedule_date=as_of_date,
            total_payments=total_payments,
            payments_by_day=payments_by_day,
            cash_flow_impact=cash_flow_impact,
            discount_opportunities=discount_opportunities,
            liquidity_requirements=liquidity_requirements
        )
        
    def _calculate_payment_cost(self, payment: PaymentRecommendation) -> float:
        """Calculate cost of payment method."""
        method_cost = self.config["payment_costs"].get(payment.payment_method, 0)
        
        if payment.payment_method == PaymentMethod.CARD:
            return payment.cash_impact * method_cost  # Percentage-based
        else:
            return method_cost  # Fixed cost
            
    def _empty_schedule(self, as_of_date: datetime) -> PaymentSchedule:
        """Generate empty payment schedule."""
        return PaymentSchedule(
            schedule_date=as_of_date,
            total_payments=0.0,
            payments_by_day={},
            cash_flow_impact={},
            discount_opportunities={},
            liquidity_requirements={}
        )
        
    def generate_payment_summary(self, schedule: PaymentSchedule) -> Dict[str, Any]:
        """Generate executive summary of payment optimization."""
        all_payments = []
        for daily_payments in schedule.payments_by_day.values():
            all_payments.extend(daily_payments)
            
        if not all_payments:
            return {"error": "No payments scheduled"}
            
        # Calculate summary metrics
        total_discounts = sum(schedule.discount_opportunities.values())
        critical_payments = len([p for p in all_payments if p.priority == PaymentPriority.CRITICAL])
        strategic_payments = len([p for p in all_payments if p.priority == PaymentPriority.STRATEGIC])
        
        # Payment method breakdown
        method_breakdown = {}
        for method in PaymentMethod:
            method_count = len([p for p in all_payments if p.payment_method == method])
            if method_count > 0:
                method_breakdown[method.value] = method_count
                
        # Risk assessment
        high_risk_payments = len([p for p in all_payments if len(p.risk_factors) > 0])
        
        summary = {
            "optimization_date": schedule.schedule_date.isoformat(),
            "total_payments": schedule.total_payments,
            "payment_count": len(all_payments),
            "total_discount_captured": total_discounts,
            "cash_flow_impact": {
                "daily_outflows": schedule.cash_flow_impact,
                "peak_outflow_day": min(schedule.cash_flow_impact, key=schedule.cash_flow_impact.get),
                "minimum_liquidity": min(schedule.liquidity_requirements.values()) if schedule.liquidity_requirements else 0
            },
            "priority_breakdown": {
                "critical": critical_payments,
                "strategic": strategic_payments,
                "high": len([p for p in all_payments if p.priority == PaymentPriority.HIGH]),
                "medium": len([p for p in all_payments if p.priority == PaymentPriority.MEDIUM]),
                "low": len([p for p in all_payments if p.priority == PaymentPriority.LOW])
            },
            "payment_methods": method_breakdown,
            "risk_assessment": {
                "high_risk_payments": high_risk_payments,
                "risk_percentage": (high_risk_payments / len(all_payments)) * 100 if all_payments else 0
            },
            "recommendations": [
                {
                    "type": "discount_optimization",
                    "message": f"Captured ${total_discounts:.0f} in early payment discounts",
                    "value": total_discounts
                } if total_discounts > 0 else None,
                {
                    "type": "cash_optimization", 
                    "message": f"Optimized payment timing to maintain minimum liquidity of ${min(schedule.liquidity_requirements.values()):,.0f}",
                    "value": min(schedule.liquidity_requirements.values()) if schedule.liquidity_requirements else 0
                }
            ]
        }
        
        # Remove None recommendations
        summary["recommendations"] = [r for r in summary["recommendations"] if r is not None]
        
        return summary