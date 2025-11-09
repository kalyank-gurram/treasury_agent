"""Real-time cash position monitoring system."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from .infrastructure.observability import get_observability_manager


class AlertSeverity(Enum):
    """Alert severity levels for cash monitoring."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


@dataclass
class CashAlert:
    """Cash monitoring alert."""
    timestamp: datetime
    severity: AlertSeverity
    alert_type: str
    message: str
    entity: str
    current_balance: float
    threshold: Optional[float] = None
    recommended_action: Optional[str] = None
    

@dataclass
class IntraDayPosition:
    """Intra-day cash position snapshot."""
    timestamp: datetime
    entity: str
    opening_balance: float
    current_balance: float
    projected_end_balance: float
    pending_inflows: float
    pending_outflows: float
    net_position_change: float
    liquidity_ratio: float
    alerts: List[CashAlert]


class RealTimeCashMonitor:
    """Real-time cash position monitoring with intelligent alerting."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("cash_management.monitor")
        
        # Default thresholds (can be customized per entity)
        self.default_thresholds = {
            "minimum_balance": 1000000,  # $1M minimum
            "critical_balance": 500000,   # $500K critical 
            "liquidity_ratio_min": 0.15, # 15% liquidity ratio
            "daily_variance_threshold": 0.25,  # 25% daily variance alert
            "concentration_limit": 0.70   # 70% in single currency
        }
        
        self.entity_thresholds = {}  # Entity-specific overrides
        self.monitoring_active = False
        self.alert_history = []
        
    async def start_monitoring(self, entities: List[str], refresh_seconds: int = 300):
        """Start real-time monitoring for specified entities."""
        self.monitoring_active = True
        self.logger.info("Starting real-time cash monitoring", 
                        entities=entities, refresh_interval=refresh_seconds)
        
        while self.monitoring_active:
            try:
                for entity in entities:
                    position = await self.get_intraday_position(entity)
                    await self.process_alerts(position)
                    
                await asyncio.sleep(refresh_seconds)
                
            except Exception as e:
                self.logger.error("Error in cash monitoring loop", 
                                error=str(e), error_type=type(e).__name__)
                await asyncio.sleep(60)  # Wait 1 minute on error
                
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        self.logger.info("Cash monitoring stopped")
        
    async def get_intraday_position(self, entity: str) -> IntraDayPosition:
        """Get current intra-day cash position for an entity."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        current_time = datetime.now()
        
        # Get current balances
        balances = api.get_account_balances(entity)
        current_balance = balances["balance"].sum() if len(balances) > 0 else 0
        
        # Get today's transactions
        transactions = api.transactions.copy()
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
            
        transactions["date"] = pd.to_datetime(transactions["date"])
        today_transactions = transactions[transactions["date"].dt.date == current_time.date()]
        
        # Calculate opening balance (current - today's net)
        todays_net = today_transactions["amount"].sum() if len(today_transactions) > 0 else 0
        opening_balance = current_balance - todays_net
        
        # Estimate pending flows (simplified - in real system would come from pending payment systems)
        pending_inflows, pending_outflows = self._estimate_pending_flows(entity, current_time)
        
        # Project end-of-day balance
        projected_end_balance = current_balance + pending_inflows - pending_outflows
        
        # Calculate liquidity ratio (simplified)
        total_assets = current_balance + pending_inflows
        liquidity_ratio = current_balance / total_assets if total_assets > 0 else 0
        
        # Generate alerts
        alerts = self._generate_alerts(entity, current_balance, projected_end_balance, liquidity_ratio)
        
        position = IntraDayPosition(
            timestamp=current_time,
            entity=entity,
            opening_balance=opening_balance,
            current_balance=current_balance,
            projected_end_balance=projected_end_balance,
            pending_inflows=pending_inflows,
            pending_outflows=pending_outflows,
            net_position_change=current_balance - opening_balance,
            liquidity_ratio=liquidity_ratio,
            alerts=alerts
        )
        
        self.logger.info("Intraday position calculated",
                        entity=entity,
                        current_balance=current_balance,
                        projected_balance=projected_end_balance,
                        alert_count=len(alerts))
        
        return position
        
    def _estimate_pending_flows(self, entity: str, current_time: datetime) -> Tuple[float, float]:
        """Estimate pending inflows and outflows for remainder of day."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        
        # Get historical patterns for this time of day
        transactions = api.transactions.copy()
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
            
        transactions["date"] = pd.to_datetime(transactions["date"])
        transactions["hour"] = transactions["date"].dt.hour
        
        current_hour = current_time.hour
        
        # Estimate remaining flows based on historical hourly patterns
        remaining_hours = 24 - current_hour
        
        if remaining_hours <= 0:
            return 0.0, 0.0
            
        # Get average hourly flows for remaining hours
        late_day_mask = transactions["hour"] >= current_hour
        late_day_transactions = transactions[late_day_mask]
        
        if len(late_day_transactions) == 0:
            return 0.0, 0.0
            
        # Separate inflows and outflows
        inflows = late_day_transactions[late_day_transactions["amount"] > 0]["amount"].sum()
        outflows = abs(late_day_transactions[late_day_transactions["amount"] < 0]["amount"].sum())
        
        # Scale by remaining time (simplified estimation)
        days_of_data = len(transactions["date"].dt.date.unique())
        if days_of_data > 0:
            avg_daily_inflows = inflows / days_of_data
            avg_daily_outflows = outflows / days_of_data
            
            # Scale by remaining hours
            time_factor = remaining_hours / 24
            estimated_inflows = avg_daily_inflows * time_factor
            estimated_outflows = avg_daily_outflows * time_factor
        else:
            estimated_inflows = 0.0
            estimated_outflows = 0.0
            
        return estimated_inflows, estimated_outflows
        
    def _generate_alerts(self, entity: str, current_balance: float, 
                        projected_balance: float, liquidity_ratio: float) -> List[CashAlert]:
        """Generate alerts based on current cash position."""
        alerts = []
        thresholds = self.entity_thresholds.get(entity, self.default_thresholds)
        current_time = datetime.now()
        
        # Critical balance alert
        if current_balance < thresholds["critical_balance"]:
            alerts.append(CashAlert(
                timestamp=current_time,
                severity=AlertSeverity.CRITICAL,
                alert_type="critical_balance",
                message=f"Critical cash balance: ${current_balance:,.0f}",
                entity=entity,
                current_balance=current_balance,
                threshold=thresholds["critical_balance"],
                recommended_action="Immediate funding required or delay non-essential payments"
            ))
            
        # Minimum balance alert
        elif current_balance < thresholds["minimum_balance"]:
            alerts.append(CashAlert(
                timestamp=current_time,
                severity=AlertSeverity.WARNING,
                alert_type="low_balance",
                message=f"Low cash balance: ${current_balance:,.0f}",
                entity=entity,
                current_balance=current_balance,
                threshold=thresholds["minimum_balance"],
                recommended_action="Consider optimizing cash position or arranging additional funding"
            ))
            
        # Projected balance alert
        if projected_balance < thresholds["minimum_balance"]:
            alerts.append(CashAlert(
                timestamp=current_time,
                severity=AlertSeverity.WARNING,
                alert_type="projected_low_balance",
                message=f"Projected end-of-day balance below minimum: ${projected_balance:,.0f}",
                entity=entity,
                current_balance=current_balance,
                threshold=thresholds["minimum_balance"],
                recommended_action="Review pending payments and consider deferring non-critical items"
            ))
            
        # Liquidity ratio alert
        if liquidity_ratio < thresholds["liquidity_ratio_min"]:
            alerts.append(CashAlert(
                timestamp=current_time,
                severity=AlertSeverity.WARNING,
                alert_type="low_liquidity_ratio",
                message=f"Low liquidity ratio: {liquidity_ratio:.1%}",
                entity=entity,
                current_balance=current_balance,
                threshold=thresholds["liquidity_ratio_min"],
                recommended_action="Improve liquidity position by accelerating receivables or arranging credit lines"
            ))
            
        # Large intraday movement alert
        opening_balance = current_balance - (projected_balance - current_balance)  # Simplified
        if opening_balance > 0:
            variance = abs((current_balance - opening_balance) / opening_balance)
            if variance > thresholds["daily_variance_threshold"]:
                alerts.append(CashAlert(
                    timestamp=current_time,
                    severity=AlertSeverity.INFO,
                    alert_type="high_variance",
                    message=f"High intraday variance: {variance:.1%}",
                    entity=entity,
                    current_balance=current_balance,
                    threshold=thresholds["daily_variance_threshold"],
                    recommended_action="Review unusual transactions for accuracy"
                ))
                
        return alerts
        
    async def process_alerts(self, position: IntraDayPosition):
        """Process and log alerts for a cash position."""
        if not position.alerts:
            return
            
        for alert in position.alerts:
            # Log alert
            self.logger.warning("Cash position alert",
                              entity=alert.entity,
                              alert_type=alert.alert_type,
                              severity=alert.severity.value,
                              message=alert.message,
                              current_balance=alert.current_balance)
            
            # Add to history
            self.alert_history.append(alert)
            
            # Record metric
            self.observability.record_metric(
                "counter", "cash_alerts_total", 1,
                {
                    "entity": alert.entity,
                    "severity": alert.severity.value,
                    "alert_type": alert.alert_type
                }
            )
            
            # In a real system, you might send notifications here
            # await self.send_notification(alert)
            
    def get_cash_summary(self, entities: List[str]) -> Dict[str, Any]:
        """Get summary of cash positions across entities."""
        from ...tools.mock_bank_api import MockBankAPI
        
        api = MockBankAPI()
        summary = {
            "timestamp": datetime.now(),
            "entities": {},
            "consolidated": {
                "total_cash": 0.0,
                "total_entities": len(entities),
                "alert_counts": {"critical": 0, "warning": 0, "info": 0}
            }
        }
        
        for entity in entities:
            balances = api.get_account_balances(entity)
            entity_balance = balances["balance"].sum() if len(balances) > 0 else 0
            
            # Get recent alerts for entity
            recent_alerts = [a for a in self.alert_history 
                           if a.entity == entity and 
                           (datetime.now() - a.timestamp).total_seconds() < 3600]  # Last hour
            
            summary["entities"][entity] = {
                "balance": entity_balance,
                "currency_breakdown": balances.groupby("currency")["balance"].sum().to_dict() if len(balances) > 0 else {},
                "recent_alerts": len(recent_alerts),
                "alert_breakdown": {
                    severity.value: len([a for a in recent_alerts if a.severity == severity])
                    for severity in AlertSeverity
                }
            }
            
            summary["consolidated"]["total_cash"] += entity_balance
            
            # Aggregate alert counts
            for severity in AlertSeverity:
                count = len([a for a in recent_alerts if a.severity == severity])
                summary["consolidated"]["alert_counts"][severity.value] += count
        
        return summary
        
    def set_entity_thresholds(self, entity: str, thresholds: Dict[str, float]):
        """Set custom thresholds for a specific entity."""
        self.entity_thresholds[entity] = {**self.default_thresholds, **thresholds}
        self.logger.info("Updated thresholds for entity", 
                        entity=entity, thresholds=thresholds)
        
    def get_alert_history(self, 
                         entity: Optional[str] = None, 
                         hours_back: int = 24,
                         severity: Optional[AlertSeverity] = None) -> List[CashAlert]:
        """Get alert history with optional filtering."""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        filtered_alerts = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        if entity:
            filtered_alerts = [a for a in filtered_alerts if a.entity == entity]
            
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
            
        return sorted(filtered_alerts, key=lambda x: x.timestamp, reverse=True)
        
    def clear_alert_history(self, older_than_hours: int = 168):  # Default 1 week
        """Clear old alerts from history."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        initial_count = len(self.alert_history)
        
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        cleared_count = initial_count - len(self.alert_history)
        self.logger.info("Cleared alert history", 
                        cleared_alerts=cleared_count, 
                        remaining_alerts=len(self.alert_history))