"""Intraday cash flow forecasting engine."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from .infrastructure.observability import get_observability_manager


class CashFlowType(Enum):
    """Types of cash flows."""
    COLLECTION = "collection"
    PAYMENT = "payment"
    BANK_FEE = "bank_fee"
    INTEREST = "interest"
    FX_SETTLEMENT = "fx_settlement"
    LOAN_DRAWDOWN = "loan_drawdown"
    INVESTMENT = "investment"
    OTHER = "other"


class ForecastConfidence(Enum):
    """Confidence levels for forecasted items."""
    CONFIRMED = "confirmed"      # >95% confidence
    HIGH = "high"               # 80-95% confidence
    MEDIUM = "medium"           # 60-80% confidence
    LOW = "low"                 # 40-60% confidence
    SPECULATIVE = "speculative"  # <40% confidence


@dataclass
class IntraDayFlow:
    """Individual intraday cash flow item."""
    flow_id: str
    timestamp: datetime
    amount: float  # Positive for inflows, negative for outflows
    flow_type: CashFlowType
    description: str
    counterparty: Optional[str] = None
    confidence: ForecastConfidence = ForecastConfidence.MEDIUM
    source_system: Optional[str] = None
    reference_id: Optional[str] = None
    

@dataclass
class IntraDayPosition:
    """Cash position at a specific point in time."""
    timestamp: datetime
    opening_balance: float
    gross_inflows: float
    gross_outflows: float
    net_flows: float
    closing_balance: float
    flows: List[IntraDayFlow]
    

@dataclass
class LiquidityAlert:
    """Liquidity management alert."""
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    recommended_action: str
    threshold_breached: Optional[float] = None
    

@dataclass
class IntraDayForecast:
    """Complete intraday cash flow forecast."""
    forecast_date: datetime
    entity: str
    account_id: str
    starting_balance: float
    ending_balance: float
    peak_balance: float
    trough_balance: float
    positions: List[IntraDayPosition]
    alerts: List[LiquidityAlert]
    confidence_score: float
    last_updated: datetime
    

class IntraDayForecaster:
    """Advanced intraday cash flow forecasting engine."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("cash_management.intraday_forecaster")
        
        # Configuration
        self.config = {
            # Forecasting parameters
            "forecast_intervals_minutes": 60,  # 1-hour intervals
            "working_hours_start": time(8, 0),   # 8:00 AM
            "working_hours_end": time(17, 0),    # 5:00 PM
            "wire_cutoff_time": time(15, 0),     # 3:00 PM for wires
            
            # Liquidity thresholds
            "minimum_balance": 1000000,          # $1M minimum
            "warning_threshold": 2000000,        # $2M warning level
            "optimal_balance": 5000000,          # $5M optimal level
            
            # Pattern detection
            "collection_patterns": {
                "morning_peak": (time(9, 0), time(11, 0)),  # 9-11 AM
                "afternoon_wave": (time(14, 0), time(16, 0))  # 2-4 PM
            },
            
            "payment_patterns": {
                "early_payments": (time(8, 0), time(10, 0)),   # 8-10 AM
                "wire_rush": (time(13, 0), time(15, 0)),       # 1-3 PM
                "ach_processing": (time(16, 0), time(17, 0))   # 4-5 PM
            },
            
            # Confidence factors
            "confidence_decay_hours": 6,  # Confidence decreases over time
            "historical_weight": 0.4,     # Weight of historical patterns
            "scheduled_weight": 0.6       # Weight of scheduled items
        }
        
    def generate_intraday_forecast(self, entity: str, account_id: str,
                                 forecast_date: Optional[datetime] = None) -> IntraDayForecast:
        """Generate comprehensive intraday cash flow forecast."""
        if forecast_date is None:
            forecast_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        self.logger.info("Generating intraday forecast",
                        entity=entity, account_id=account_id,
                        forecast_date=forecast_date.isoformat())
        
        try:
            # Get starting balance
            starting_balance = self._get_opening_balance(entity, account_id, forecast_date)
            
            # Generate scheduled flows
            scheduled_flows = self._get_scheduled_flows(entity, account_id, forecast_date)
            
            # Generate predicted flows based on patterns
            predicted_flows = self._generate_predicted_flows(entity, account_id, forecast_date)
            
            # Combine all flows
            all_flows = scheduled_flows + predicted_flows
            
            # Generate hourly positions
            positions = self._generate_hourly_positions(starting_balance, all_flows, forecast_date)
            
            # Calculate summary metrics
            ending_balance = positions[-1].closing_balance if positions else starting_balance
            peak_balance = max(pos.closing_balance for pos in positions) if positions else starting_balance
            trough_balance = min(pos.closing_balance for pos in positions) if positions else starting_balance
            
            # Generate liquidity alerts
            alerts = self._generate_liquidity_alerts(positions)
            
            # Calculate overall confidence
            confidence_score = self._calculate_forecast_confidence(all_flows, forecast_date)
            
            forecast = IntraDayForecast(
                forecast_date=forecast_date,
                entity=entity,
                account_id=account_id,
                starting_balance=starting_balance,
                ending_balance=ending_balance,
                peak_balance=peak_balance,
                trough_balance=trough_balance,
                positions=positions,
                alerts=alerts,
                confidence_score=confidence_score,
                last_updated=datetime.now()
            )
            
            self.logger.info("Intraday forecast completed",
                           entity=entity, account_id=account_id,
                           starting_balance=starting_balance,
                           ending_balance=ending_balance,
                           trough_balance=trough_balance,
                           alerts_count=len(alerts))
            
            # Record metrics
            self.observability.record_metric(
                "gauge", "intraday_starting_balance", starting_balance,
                {"entity": entity, "account": account_id}
            )
            
            self.observability.record_metric(
                "gauge", "intraday_trough_balance", trough_balance,
                {"entity": entity, "account": account_id}
            )
            
            self.observability.record_metric(
                "gauge", "intraday_forecast_confidence", confidence_score,
                {"entity": entity, "account": account_id}
            )
            
            return forecast
            
        except Exception as e:
            self.logger.error("Intraday forecast failed",
                            entity=entity, account_id=account_id,
                            error=str(e), error_type=type(e).__name__)
            raise
            
    def _get_opening_balance(self, entity: str, account_id: str, forecast_date: datetime) -> float:
        """Get opening balance for the forecast date."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        
        # Get account balance (in real system, this would be from bank API)
        balances = api.get_account_balances(entity)
        
        if account_id in balances:
            return balances[account_id]
        else:
            # Return a realistic starting balance for demo
            return np.random.uniform(8000000, 15000000)  # $8-15M
            
    def _get_scheduled_flows(self, entity: str, account_id: str, forecast_date: datetime) -> List[IntraDayFlow]:
        """Get confirmed scheduled cash flows for the day."""
        flows = []
        
        # In a real system, this would pull from:
        # - Payment systems (scheduled outgoing payments)
        # - Collections systems (expected incoming payments)
        # - Treasury management systems
        # - Bank reporting systems
        
        # Generate realistic scheduled flows for demo
        
        # Morning collections (high confidence)
        collections_amount = np.random.uniform(2000000, 5000000)
        flows.append(IntraDayFlow(
            flow_id="COLL-001",
            timestamp=forecast_date.replace(hour=9, minute=30),
            amount=collections_amount,
            flow_type=CashFlowType.COLLECTION,
            description="Wire collections from major customers",
            confidence=ForecastConfidence.CONFIRMED,
            source_system="Collections"
        ))
        
        # Scheduled payments (confirmed)
        payment_amount = np.random.uniform(1500000, 3000000)
        flows.append(IntraDayFlow(
            flow_id="PAY-001",
            timestamp=forecast_date.replace(hour=14, minute=0),
            amount=-payment_amount,
            flow_type=CashFlowType.PAYMENT,
            description="Scheduled supplier payments",
            confidence=ForecastConfidence.CONFIRMED,
            source_system="AP System"
        ))
        
        # ACH collections (high confidence)
        ach_collections = np.random.uniform(800000, 1500000)
        flows.append(IntraDayFlow(
            flow_id="ACH-001",
            timestamp=forecast_date.replace(hour=16, minute=0),
            amount=ach_collections,
            flow_type=CashFlowType.COLLECTION,
            description="ACH customer collections",
            confidence=ForecastConfidence.HIGH,
            source_system="ACH Processing"
        ))
        
        # Bank fees (confirmed)
        bank_fees = np.random.uniform(5000, 15000)
        flows.append(IntraDayFlow(
            flow_id="FEE-001",
            timestamp=forecast_date.replace(hour=17, minute=0),
            amount=-bank_fees,
            flow_type=CashFlowType.BANK_FEE,
            description="Daily banking fees",
            confidence=ForecastConfidence.CONFIRMED,
            source_system="Bank System"
        ))
        
        return flows
        
    def _generate_predicted_flows(self, entity: str, account_id: str, forecast_date: datetime) -> List[IntraDayFlow]:
        """Generate predicted flows based on historical patterns."""
        flows = []
        
        # Analyze day of week patterns
        day_of_week = forecast_date.weekday()  # 0 = Monday
        
        # Monday patterns - higher collections from weekend processing
        if day_of_week == 0:
            weekend_catch_up = np.random.uniform(500000, 1200000)
            flows.append(IntraDayFlow(
                flow_id="PRED-MON-001",
                timestamp=forecast_date.replace(hour=10, minute=0),
                amount=weekend_catch_up,
                flow_type=CashFlowType.COLLECTION,
                description="Monday catch-up collections",
                confidence=ForecastConfidence.MEDIUM,
                source_system="Pattern Analysis"
            ))
            
        # Friday patterns - higher outflows for weekly payments
        elif day_of_week == 4:
            weekly_payments = np.random.uniform(800000, 1800000)
            flows.append(IntraDayFlow(
                flow_id="PRED-FRI-001",
                timestamp=forecast_date.replace(hour=13, minute=30),
                amount=-weekly_payments,
                flow_type=CashFlowType.PAYMENT,
                description="Weekly payment batch",
                confidence=ForecastConfidence.MEDIUM,
                source_system="Pattern Analysis"
            ))
            
        # Mid-day surprise collections (lower confidence)
        if np.random.random() < 0.3:  # 30% chance
            surprise_collection = np.random.uniform(200000, 800000)
            flows.append(IntraDayFlow(
                flow_id="PRED-SURP-001",
                timestamp=forecast_date.replace(hour=12, minute=np.random.randint(0, 59)),
                amount=surprise_collection,
                flow_type=CashFlowType.COLLECTION,
                description="Unexpected customer payment",
                confidence=ForecastConfidence.LOW,
                source_system="Pattern Analysis"
            ))
            
        # FX settlements (if applicable)
        if np.random.random() < 0.2:  # 20% chance
            fx_amount = np.random.uniform(-500000, 500000)
            flows.append(IntraDayFlow(
                flow_id="PRED-FX-001",
                timestamp=forecast_date.replace(hour=11, minute=0),
                amount=fx_amount,
                flow_type=CashFlowType.FX_SETTLEMENT,
                description="FX settlement from overnight trading",
                confidence=ForecastConfidence.LOW,
                source_system="FX System"
            ))
            
        return flows
        
    def _generate_hourly_positions(self, starting_balance: float, flows: List[IntraDayFlow],
                                 forecast_date: datetime) -> List[IntraDayPosition]:
        """Generate hourly cash positions throughout the day."""
        positions = []
        
        # Sort flows by timestamp
        flows.sort(key=lambda x: x.timestamp)
        
        # Generate positions for each hour
        current_balance = starting_balance
        
        for hour in range(24):  # 24-hour coverage
            hour_start = forecast_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Find flows in this hour
            hour_flows = [f for f in flows if hour_start <= f.timestamp < hour_end]
            
            # Calculate flows for this hour
            gross_inflows = sum(f.amount for f in hour_flows if f.amount > 0)
            gross_outflows = sum(abs(f.amount) for f in hour_flows if f.amount < 0)
            net_flows = sum(f.amount for f in hour_flows)
            
            # Update balance
            opening_balance = current_balance
            closing_balance = current_balance + net_flows
            current_balance = closing_balance
            
            position = IntraDayPosition(
                timestamp=hour_start,
                opening_balance=opening_balance,
                gross_inflows=gross_inflows,
                gross_outflows=gross_outflows,
                net_flows=net_flows,
                closing_balance=closing_balance,
                flows=hour_flows.copy()
            )
            
            positions.append(position)
            
        return positions
        
    def _generate_liquidity_alerts(self, positions: List[IntraDayPosition]) -> List[LiquidityAlert]:
        """Generate liquidity management alerts based on positions."""
        alerts = []
        
        for position in positions:
            # Critical liquidity alert
            if position.closing_balance < self.config["minimum_balance"]:
                alerts.append(LiquidityAlert(
                    timestamp=position.timestamp,
                    alert_type="liquidity_critical",
                    severity="critical",
                    message=f"Balance projected to fall below minimum threshold: ${position.closing_balance:,.0f}",
                    recommended_action="Immediate funding required - activate credit lines or delay payments",
                    threshold_breached=self.config["minimum_balance"]
                ))
                
            # Warning threshold alert
            elif position.closing_balance < self.config["warning_threshold"]:
                alerts.append(LiquidityAlert(
                    timestamp=position.timestamp,
                    alert_type="liquidity_warning",
                    severity="warning", 
                    message=f"Balance approaching minimum threshold: ${position.closing_balance:,.0f}",
                    recommended_action="Monitor closely and prepare funding options",
                    threshold_breached=self.config["warning_threshold"]
                ))
                
            # Large outflow alert
            if position.gross_outflows > 5000000:  # $5M+ outflows
                alerts.append(LiquidityAlert(
                    timestamp=position.timestamp,
                    alert_type="large_outflow",
                    severity="info",
                    message=f"Large outflows scheduled: ${position.gross_outflows:,.0f}",
                    recommended_action="Verify sufficient funding and confirm payment authorizations"
                ))
                
        # Wire cutoff alerts
        wire_cutoff = datetime.combine(positions[0].timestamp.date(), self.config["wire_cutoff_time"])
        
        for position in positions:
            if (position.timestamp.time() >= self.config["wire_cutoff_time"] and
                position.closing_balance < self.config["warning_threshold"]):
                
                alerts.append(LiquidityAlert(
                    timestamp=position.timestamp,
                    alert_type="wire_cutoff",
                    severity="warning",
                    message="Low balance after wire cutoff - overnight funding options limited",
                    recommended_action="Consider international wires or next-day funding arrangements"
                ))
                break  # Only alert once per day
                
        return alerts
        
    def _calculate_forecast_confidence(self, flows: List[IntraDayFlow], forecast_date: datetime) -> float:
        """Calculate overall forecast confidence score."""
        if not flows:
            return 0.5  # Neutral confidence with no data
            
        # Weight by flow amount and confidence
        total_weighted_confidence = 0.0
        total_weights = 0.0
        
        confidence_values = {
            ForecastConfidence.CONFIRMED: 0.95,
            ForecastConfidence.HIGH: 0.85,
            ForecastConfidence.MEDIUM: 0.70,
            ForecastConfidence.LOW: 0.50,
            ForecastConfidence.SPECULATIVE: 0.30
        }
        
        for flow in flows:
            weight = abs(flow.amount)  # Use amount as weight
            confidence = confidence_values.get(flow.confidence, 0.50)
            
            # Apply time decay for future timestamps
            hours_ahead = (flow.timestamp - datetime.now()).total_seconds() / 3600
            if hours_ahead > 0:
                time_decay = max(0.5, 1 - (hours_ahead / self.config["confidence_decay_hours"]) * 0.2)
                confidence *= time_decay
                
            total_weighted_confidence += confidence * weight
            total_weights += weight
            
        if total_weights > 0:
            overall_confidence = total_weighted_confidence / total_weights
        else:
            overall_confidence = 0.7  # Default confidence
            
        return min(0.99, max(0.10, overall_confidence))
        
    def update_forecast_with_actuals(self, forecast: IntraDayForecast, 
                                   actual_flows: List[IntraDayFlow]) -> IntraDayForecast:
        """Update forecast with actual flows as they occur."""
        self.logger.info("Updating forecast with actuals",
                        entity=forecast.entity, 
                        actual_flows_count=len(actual_flows))
        
        # Create updated positions by replacing forecasted flows with actuals
        updated_positions = []
        
        for position in forecast.positions:
            # Check if we have actuals for this time period
            position_actuals = [
                flow for flow in actual_flows 
                if position.timestamp <= flow.timestamp < position.timestamp + timedelta(hours=1)
            ]
            
            if position_actuals:
                # Recalculate position with actuals
                gross_inflows = sum(f.amount for f in position_actuals if f.amount > 0)
                gross_outflows = sum(abs(f.amount) for f in position_actuals if f.amount < 0)
                net_flows = sum(f.amount for f in position_actuals)
                
                # Update position
                updated_position = IntraDayPosition(
                    timestamp=position.timestamp,
                    opening_balance=position.opening_balance,
                    gross_inflows=gross_inflows,
                    gross_outflows=gross_outflows,
                    net_flows=net_flows,
                    closing_balance=position.opening_balance + net_flows,
                    flows=position_actuals
                )
                
                updated_positions.append(updated_position)
            else:
                # Keep original forecast
                updated_positions.append(position)
                
        # Recalculate balances forward from actual positions
        current_balance = forecast.starting_balance
        
        for i, position in enumerate(updated_positions):
            position.opening_balance = current_balance
            position.closing_balance = current_balance + position.net_flows
            current_balance = position.closing_balance
            
        # Update forecast metrics
        ending_balance = updated_positions[-1].closing_balance if updated_positions else forecast.starting_balance
        peak_balance = max(pos.closing_balance for pos in updated_positions) if updated_positions else forecast.starting_balance
        trough_balance = min(pos.closing_balance for pos in updated_positions) if updated_positions else forecast.starting_balance
        
        # Regenerate alerts with updated data
        alerts = self._generate_liquidity_alerts(updated_positions)
        
        # Update confidence based on accuracy
        updated_confidence = self._calculate_updated_confidence(forecast, actual_flows)
        
        # Create updated forecast
        updated_forecast = IntraDayForecast(
            forecast_date=forecast.forecast_date,
            entity=forecast.entity,
            account_id=forecast.account_id,
            starting_balance=forecast.starting_balance,
            ending_balance=ending_balance,
            peak_balance=peak_balance,
            trough_balance=trough_balance,
            positions=updated_positions,
            alerts=alerts,
            confidence_score=updated_confidence,
            last_updated=datetime.now()
        )
        
        return updated_forecast
        
    def _calculate_updated_confidence(self, original_forecast: IntraDayForecast,
                                    actual_flows: List[IntraDayFlow]) -> float:
        """Calculate updated confidence based on forecast accuracy."""
        # Compare forecasted vs actual flows
        accuracy_scores = []
        
        for position in original_forecast.positions:
            # Get actuals for this time period
            position_actuals = [
                flow for flow in actual_flows
                if position.timestamp <= flow.timestamp < position.timestamp + timedelta(hours=1)
            ]
            
            if position_actuals and position.flows:
                # Calculate accuracy
                forecasted_net = sum(f.amount for f in position.flows)
                actual_net = sum(f.amount for f in position_actuals)
                
                if forecasted_net != 0:
                    accuracy = 1 - abs(forecasted_net - actual_net) / abs(forecasted_net)
                    accuracy_scores.append(max(0, accuracy))
                    
        if accuracy_scores:
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            # Blend with original confidence
            updated_confidence = (original_forecast.confidence_score * 0.5) + (avg_accuracy * 0.5)
        else:
            updated_confidence = original_forecast.confidence_score
            
        return min(0.99, max(0.10, updated_confidence))
        
    def generate_liquidity_report(self, forecast: IntraDayForecast) -> Dict[str, Any]:
        """Generate comprehensive liquidity management report."""
        report = {
            "forecast_summary": {
                "entity": forecast.entity,
                "account_id": forecast.account_id,
                "forecast_date": forecast.forecast_date.isoformat(),
                "starting_balance": forecast.starting_balance,
                "ending_balance": forecast.ending_balance,
                "peak_balance": forecast.peak_balance,
                "trough_balance": forecast.trough_balance,
                "confidence_score": forecast.confidence_score
            },
            "liquidity_analysis": {
                "minimum_threshold": self.config["minimum_balance"],
                "buffer_available": forecast.trough_balance - self.config["minimum_balance"],
                "threshold_breaches": len([alert for alert in forecast.alerts if alert.severity == "critical"]),
                "risk_level": "high" if forecast.trough_balance < self.config["minimum_balance"] else
                            "medium" if forecast.trough_balance < self.config["warning_threshold"] else "low"
            },
            "cash_flow_patterns": {},
            "alerts": [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "action": alert.recommended_action
                }
                for alert in forecast.alerts
            ],
            "recommendations": []
        }
        
        # Analyze cash flow patterns
        total_inflows = sum(pos.gross_inflows for pos in forecast.positions)
        total_outflows = sum(pos.gross_outflows for pos in forecast.positions)
        
        report["cash_flow_patterns"] = {
            "total_inflows": total_inflows,
            "total_outflows": total_outflows,
            "net_flow": total_inflows - total_outflows,
            "inflow_concentration": self._calculate_flow_concentration([pos.gross_inflows for pos in forecast.positions]),
            "outflow_concentration": self._calculate_flow_concentration([pos.gross_outflows for pos in forecast.positions])
        }
        
        # Generate recommendations
        if forecast.trough_balance < self.config["minimum_balance"]:
            funding_needed = self.config["minimum_balance"] - forecast.trough_balance
            report["recommendations"].append({
                "type": "funding_required",
                "priority": "critical",
                "message": f"Secure ${funding_needed:,.0f} in funding to maintain minimum balance",
                "amount": funding_needed
            })
            
        if len(forecast.alerts) > 5:
            report["recommendations"].append({
                "type": "risk_management",
                "priority": "high",
                "message": "Multiple liquidity alerts detected - review payment timing and cash management policies"
            })
            
        return report
        
    def _calculate_flow_concentration(self, flows: List[float]) -> float:
        """Calculate concentration of cash flows (Herfindahl index)."""
        if not flows or sum(flows) == 0:
            return 0.0
            
        total = sum(flows)
        proportions = [f / total for f in flows if f > 0]
        
        if not proportions:
            return 0.0
            
        # Herfindahl index (concentration measure)
        concentration = sum(p ** 2 for p in proportions)
        return concentration