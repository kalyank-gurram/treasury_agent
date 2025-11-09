"""Intelligent Alerting System for Treasury Operations.

This module provides comprehensive alerting capabilities with smart routing,
escalation policies, and integration with multiple notification channels.
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import threading
import uuid
import hashlib


class AlertSeverity(Enum):
    """Alert severity levels with escalation implications."""
    INFO = "info"                    # Informational, no action needed
    LOW = "low"                      # Low priority, can wait
    MEDIUM = "medium"                # Medium priority, investigate within hours
    HIGH = "high"                    # High priority, investigate within 30 minutes
    CRITICAL = "critical"            # Critical, immediate action required
    EMERGENCY = "emergency"          # Emergency, wake up on-call team


class AlertType(Enum):
    """Types of alerts in treasury operations."""
    CASH_FLOW = "cash_flow"                    # Cash flow related alerts
    PAYMENT_PROCESSING = "payment_processing"   # Payment system alerts
    INVESTMENT_RISK = "investment_risk"         # Investment risk alerts
    COMPLIANCE_VIOLATION = "compliance_violation" # Regulatory compliance
    SECURITY_BREACH = "security_breach"         # Security incidents
    SYSTEM_PERFORMANCE = "system_performance"   # System health alerts
    LIQUIDITY_RISK = "liquidity_risk"          # Liquidity management
    MARKET_RISK = "market_risk"                # Market condition alerts
    OPERATIONAL_RISK = "operational_risk"       # Operational issues
    AUDIT_ANOMALY = "audit_anomaly"            # Audit trail anomalies


class NotificationChannel(Enum):
    """Available notification channels for alerts."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    MOBILE_PUSH = "mobile_push"
    PAGERDUTY = "pagerduty"


@dataclass
class Alert:
    """Represents a treasury system alert."""
    alert_id: str
    title: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    source_system: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context and metadata
    affected_resources: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Alert lifecycle
    status: str = "active"  # active, acknowledged, resolved, suppressed
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Escalation tracking
    escalation_level: int = 0
    escalation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Auto-resolution
    auto_resolve_after: Optional[timedelta] = None
    fingerprint: Optional[str] = None  # For deduplication
    
    def __post_init__(self):
        """Generate fingerprint for deduplication."""
        if not self.fingerprint:
            content = f"{self.alert_type.value}:{self.title}:{self.source_system}"
            self.fingerprint = hashlib.md5(content.encode()).hexdigest()


@dataclass
class AlertRule:
    """Defines conditions and actions for alert generation."""
    rule_id: str
    name: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    
    # Trigger conditions
    metric_name: str
    condition_operator: str  # >, <, >=, <=, ==, !=
    threshold_value: float
    evaluation_window: timedelta
    
    # Advanced conditions
    additional_conditions: List[Dict[str, Any]] = field(default_factory=list)
    require_consecutive_breaches: int = 1
    
    # Actions and notifications
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    escalation_policy: Optional[str] = None
    auto_resolve_after: Optional[timedelta] = None
    
    # Rule management
    is_enabled: bool = True
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Suppression and throttling
    suppress_after: Optional[int] = None  # Suppress after N similar alerts
    throttle_window: Optional[timedelta] = None
    
    def evaluate_condition(self, metric_value: float, context: Dict[str, Any] = None) -> bool:
        """Evaluate if the rule condition is met."""
        context = context or {}
        
        # Primary condition evaluation
        if self.condition_operator == ">":
            primary_match = metric_value > self.threshold_value
        elif self.condition_operator == "<":
            primary_match = metric_value < self.threshold_value
        elif self.condition_operator == ">=":
            primary_match = metric_value >= self.threshold_value
        elif self.condition_operator == "<=":
            primary_match = metric_value <= self.threshold_value
        elif self.condition_operator == "==":
            primary_match = metric_value == self.threshold_value
        elif self.condition_operator == "!=":
            primary_match = metric_value != self.threshold_value
        else:
            return False
            
        if not primary_match:
            return False
            
        # Additional conditions evaluation
        for condition in self.additional_conditions:
            condition_type = condition.get("type")
            
            if condition_type == "time_of_day":
                current_hour = datetime.now().hour
                if not (condition["start_hour"] <= current_hour <= condition["end_hour"]):
                    return False
                    
            elif condition_type == "day_of_week":
                current_day = datetime.now().weekday()  # 0 = Monday
                if current_day not in condition["days"]:
                    return False
                    
            elif condition_type == "context_value":
                context_key = condition["key"]
                expected_value = condition["value"]
                if context.get(context_key) != expected_value:
                    return False
                    
        return True


@dataclass 
class EscalationPolicy:
    """Defines escalation rules for alerts."""
    policy_id: str
    name: str
    description: str
    
    escalation_steps: List[Dict[str, Any]] = field(default_factory=list)
    # Each step: {"delay_minutes": int, "channels": [NotificationChannel], "recipients": [str]}
    
    max_escalations: int = 3
    repeat_interval: Optional[timedelta] = None  # Repeat notifications
    
    # Business hours consideration
    respect_business_hours: bool = True
    business_hours_start: int = 9   # 9 AM
    business_hours_end: int = 17    # 5 PM
    business_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri


class AlertManager:
    """Comprehensive alert management system for treasury operations."""
    
    def __init__(self, enable_auto_escalation: bool = True,
                 enable_smart_grouping: bool = True):
        self.enable_auto_escalation = enable_auto_escalation
        self.enable_smart_grouping = enable_smart_grouping
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.alert_rules: Dict[str, AlertRule] = {}
        self.escalation_policies: Dict[str, EscalationPolicy] = {}
        
        # Alert grouping and deduplication
        self.alert_groups: Dict[str, List[str]] = defaultdict(list)
        self.suppressed_fingerprints: Set[str] = set()
        
        # Notification tracking
        self.notification_callbacks: Dict[NotificationChannel, List[Callable]] = defaultdict(list)
        self.failed_notifications: deque = deque(maxlen=1000)
        
        # Performance tracking
        self.alert_stats = {
            'total_alerts_created': 0,
            'alerts_resolved': 0,
            'false_positives': 0,
            'avg_resolution_time': 0.0,
            'escalation_count': 0
        }
        
        # Threading for background tasks
        self.background_tasks = []
        self.shutdown_event = threading.Event()
        
        # Initialize default rules and policies
        self._initialize_treasury_alert_rules()
        self._initialize_default_escalation_policies()
        
        # Start background processing
        self._start_background_tasks()
        
        self.logger = logging.getLogger(__name__)
        
    def _initialize_treasury_alert_rules(self):
        """Initialize default alert rules for treasury operations."""
        default_rules = [
            # Cash Management Alerts
            AlertRule(
                rule_id="cash_balance_low",
                name="Low Cash Balance Alert",
                description="Alert when cash balance falls below minimum threshold",
                alert_type=AlertType.CASH_FLOW,
                severity=AlertSeverity.HIGH,
                metric_name="cash_balance_total",
                condition_operator="<",
                threshold_value=1000000,  # $1M minimum
                evaluation_window=timedelta(minutes=5),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_policy="treasury_standard",
                auto_resolve_after=timedelta(hours=1)
            ),
            
            AlertRule(
                rule_id="large_cash_outflow",
                name="Large Daily Cash Outflow",
                description="Alert on unusually large daily cash outflows",
                alert_type=AlertType.LIQUIDITY_RISK,
                severity=AlertSeverity.CRITICAL,
                metric_name="daily_cash_flow",
                condition_operator="<",
                threshold_value=-5000000,  # -$5M outflow
                evaluation_window=timedelta(minutes=15),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PAGERDUTY],
                escalation_policy="treasury_critical",
                require_consecutive_breaches=2
            ),
            
            # Payment Processing Alerts
            AlertRule(
                rule_id="payment_failure_rate_high",
                name="High Payment Failure Rate",
                description="Alert when payment failure rate exceeds threshold",
                alert_type=AlertType.PAYMENT_PROCESSING,
                severity=AlertSeverity.MEDIUM,
                metric_name="payment_failure_rate",
                condition_operator=">",
                threshold_value=0.05,  # 5% failure rate
                evaluation_window=timedelta(minutes=10),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                suppress_after=3,
                throttle_window=timedelta(hours=1)
            ),
            
            AlertRule(
                rule_id="payment_processing_slow",
                name="Slow Payment Processing",
                description="Alert when payment processing time is slow",
                alert_type=AlertType.SYSTEM_PERFORMANCE,
                severity=AlertSeverity.LOW,
                metric_name="payment_processing_time",
                condition_operator=">",
                threshold_value=5000,  # 5 seconds
                evaluation_window=timedelta(minutes=5),
                notification_channels=[NotificationChannel.EMAIL],
                require_consecutive_breaches=3
            ),
            
            # Investment Risk Alerts
            AlertRule(
                rule_id="investment_yield_low",
                name="Low Investment Yield",
                description="Alert when portfolio yield falls below minimum",
                alert_type=AlertType.INVESTMENT_RISK,
                severity=AlertSeverity.MEDIUM,
                metric_name="investment_yield",
                condition_operator="<",
                threshold_value=0.02,  # 2% minimum yield
                evaluation_window=timedelta(hours=1),
                notification_channels=[NotificationChannel.EMAIL],
                auto_resolve_after=timedelta(hours=24)
            ),
            
            AlertRule(
                rule_id="portfolio_risk_high",
                name="High Portfolio Risk",
                description="Alert when portfolio risk score is too high",
                alert_type=AlertType.INVESTMENT_RISK,
                severity=AlertSeverity.HIGH,
                metric_name="investment_risk_score",
                condition_operator=">",
                threshold_value=0.8,  # Risk score > 0.8
                evaluation_window=timedelta(minutes=15),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_policy="treasury_standard"
            ),
            
            # Security Alerts
            AlertRule(
                rule_id="failed_login_rate_high",
                name="High Failed Login Rate",
                description="Alert on suspicious login failure rates",
                alert_type=AlertType.SECURITY_BREACH,
                severity=AlertSeverity.CRITICAL,
                metric_name="failed_login_rate",
                condition_operator=">",
                threshold_value=0.20,  # 20% failure rate
                evaluation_window=timedelta(minutes=5),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PAGERDUTY],
                escalation_policy="security_breach",
                require_consecutive_breaches=1  # Immediate alert
            ),
            
            AlertRule(
                rule_id="security_violation_detected",
                name="Security Violation Detected",
                description="Alert on any security violation",
                alert_type=AlertType.SECURITY_BREACH,
                severity=AlertSeverity.EMERGENCY,
                metric_name="security_violations",
                condition_operator=">",
                threshold_value=0,  # Any violation
                evaluation_window=timedelta(minutes=1),
                notification_channels=[
                    NotificationChannel.EMAIL, NotificationChannel.SMS, 
                    NotificationChannel.PAGERDUTY, NotificationChannel.SLACK
                ],
                escalation_policy="security_breach"
            ),
            
            # Compliance Alerts
            AlertRule(
                rule_id="compliance_check_failed",
                name="Compliance Check Failed",
                description="Alert on failed compliance checks",
                alert_type=AlertType.COMPLIANCE_VIOLATION,
                severity=AlertSeverity.HIGH,
                metric_name="compliance_check_failures",
                condition_operator=">",
                threshold_value=0,  # Any failure
                evaluation_window=timedelta(minutes=1),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_policy="compliance_violation"
            ),
            
            # System Performance Alerts
            AlertRule(
                rule_id="api_response_slow",
                name="Slow API Response Times",
                description="Alert when API responses are consistently slow",
                alert_type=AlertType.SYSTEM_PERFORMANCE,
                severity=AlertSeverity.MEDIUM,
                metric_name="api_response_time",
                condition_operator=">",
                threshold_value=1000,  # 1 second
                evaluation_window=timedelta(minutes=5),
                notification_channels=[NotificationChannel.EMAIL],
                require_consecutive_breaches=5,
                suppress_after=2,
                throttle_window=timedelta(hours=2)
            ),
            
            AlertRule(
                rule_id="system_cpu_high",
                name="High System CPU Usage",
                description="Alert on high CPU utilization",
                alert_type=AlertType.SYSTEM_PERFORMANCE,
                severity=AlertSeverity.HIGH,
                metric_name="system_cpu_usage",
                condition_operator=">",
                threshold_value=0.85,  # 85% CPU
                evaluation_window=timedelta(minutes=5),
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                require_consecutive_breaches=3
            )
        ]
        
        # Register all rules
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
            
    def _initialize_default_escalation_policies(self):
        """Initialize default escalation policies."""
        policies = [
            EscalationPolicy(
                policy_id="treasury_standard",
                name="Treasury Standard Escalation",
                description="Standard escalation for treasury alerts",
                escalation_steps=[
                    {
                        "delay_minutes": 0,
                        "channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                        "recipients": ["treasury_team"]
                    },
                    {
                        "delay_minutes": 30,
                        "channels": [NotificationChannel.EMAIL, NotificationChannel.SMS],
                        "recipients": ["treasury_manager"]
                    },
                    {
                        "delay_minutes": 60,
                        "channels": [NotificationChannel.PAGERDUTY],
                        "recipients": ["treasury_director"]
                    }
                ]
            ),
            
            EscalationPolicy(
                policy_id="treasury_critical",
                name="Treasury Critical Escalation",
                description="Critical escalation for high-impact treasury alerts",
                escalation_steps=[
                    {
                        "delay_minutes": 0,
                        "channels": [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PAGERDUTY],
                        "recipients": ["treasury_team", "treasury_manager"]
                    },
                    {
                        "delay_minutes": 15,
                        "channels": [NotificationChannel.SMS, NotificationChannel.PAGERDUTY],
                        "recipients": ["treasury_director", "cfo"]
                    }
                ],
                max_escalations=2
            ),
            
            EscalationPolicy(
                policy_id="security_breach",
                name="Security Breach Escalation",
                description="Immediate escalation for security incidents",
                escalation_steps=[
                    {
                        "delay_minutes": 0,
                        "channels": [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PAGERDUTY],
                        "recipients": ["security_team", "treasury_manager", "ciso"]
                    }
                ],
                max_escalations=1,
                respect_business_hours=False  # 24/7 for security
            ),
            
            EscalationPolicy(
                policy_id="compliance_violation",
                name="Compliance Violation Escalation", 
                description="Escalation for regulatory compliance violations",
                escalation_steps=[
                    {
                        "delay_minutes": 0,
                        "channels": [NotificationChannel.EMAIL],
                        "recipients": ["compliance_team"]
                    },
                    {
                        "delay_minutes": 60,
                        "channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                        "recipients": ["compliance_manager", "treasury_manager"]
                    }
                ]
            )
        ]
        
        for policy in policies:
            self.escalation_policies[policy.policy_id] = policy
            
    def create_alert(self, title: str, description: str, alert_type: AlertType,
                    severity: AlertSeverity, source_system: str,
                    affected_resources: List[str] = None,
                    metrics: Dict[str, Any] = None,
                    tags: Dict[str, str] = None,
                    context: Dict[str, Any] = None,
                    auto_resolve_after: timedelta = None) -> str:
        """Create a new alert."""
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            title=title,
            description=description,
            alert_type=alert_type,
            severity=severity,
            source_system=source_system,
            affected_resources=affected_resources or [],
            metrics=metrics or {},
            tags=tags or {},
            context=context or {},
            auto_resolve_after=auto_resolve_after
        )
        
        # Check for deduplication
        if self._should_suppress_alert(alert):
            self.logger.info(f"Suppressing duplicate alert: {alert.fingerprint}")
            return alert.alert_id
            
        # Store alert
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        # Update statistics
        self.alert_stats['total_alerts_created'] += 1
        
        # Smart grouping
        if self.enable_smart_grouping:
            self._group_alert(alert)
            
        # Send initial notifications
        self._send_alert_notifications(alert)
        
        # Schedule escalation if enabled
        if self.enable_auto_escalation:
            self._schedule_escalation(alert)
            
        self.logger.info(f"Created alert {alert.alert_id}: {title}")
        
        return alert.alert_id
        
    def create_alert_from_metric(self, metric_name: str, metric_value: float,
                               context: Dict[str, Any] = None) -> List[str]:
        """Evaluate metric against rules and create alerts if conditions are met."""
        context = context or {}
        alerts_created = []
        
        # Find matching rules
        matching_rules = [
            rule for rule in self.alert_rules.values()
            if rule.is_enabled and rule.metric_name == metric_name
        ]
        
        for rule in matching_rules:
            if rule.evaluate_condition(metric_value, context):
                # Check consecutive breaches requirement
                if self._check_consecutive_breaches(rule, metric_value):
                    alert_id = self.create_alert(
                        title=f"{rule.name}: {metric_name} = {metric_value}",
                        description=f"{rule.description}. Current value: {metric_value}, Threshold: {rule.threshold_value}",
                        alert_type=rule.alert_type,
                        severity=rule.severity,
                        source_system="metrics_system",
                        metrics={metric_name: metric_value},
                        context=context,
                        auto_resolve_after=rule.auto_resolve_after
                    )
                    alerts_created.append(alert_id)
                    
        return alerts_created
        
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str,
                         notes: str = None) -> bool:
        """Acknowledge an active alert."""
        if alert_id not in self.active_alerts:
            return False
            
        alert = self.active_alerts[alert_id]
        alert.status = "acknowledged"
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now(timezone.utc)
        
        if notes:
            alert.context["acknowledgment_notes"] = notes
            
        self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True
        
    def resolve_alert(self, alert_id: str, resolved_by: str, 
                     resolution_notes: str = None) -> bool:
        """Resolve an active alert."""
        if alert_id not in self.active_alerts:
            return False
            
        alert = self.active_alerts[alert_id]
        alert.status = "resolved"
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.now(timezone.utc)
        
        if resolution_notes:
            alert.context["resolution_notes"] = resolution_notes
            
        # Calculate resolution time
        resolution_time = (alert.resolved_at - alert.created_at).total_seconds()
        self._update_avg_resolution_time(resolution_time)
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Update statistics
        self.alert_stats['alerts_resolved'] += 1
        
        self.logger.info(f"Alert {alert_id} resolved by {resolved_by}")
        return True
        
    def get_active_alerts(self, alert_type: AlertType = None,
                         severity: AlertSeverity = None) -> List[Alert]:
        """Get filtered list of active alerts."""
        alerts = list(self.active_alerts.values())
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
            
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
            
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
        
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get comprehensive alert statistics."""
        active_count = len(self.active_alerts)
        
        # Count by severity
        severity_counts = defaultdict(int)
        for alert in self.active_alerts.values():
            severity_counts[alert.severity.value] += 1
            
        # Count by type
        type_counts = defaultdict(int)
        for alert in self.active_alerts.values():
            type_counts[alert.alert_type.value] += 1
            
        return {
            **self.alert_stats,
            'active_alerts': active_count,
            'alerts_by_severity': dict(severity_counts),
            'alerts_by_type': dict(type_counts),
            'suppressed_fingerprints': len(self.suppressed_fingerprints),
            'failed_notifications': len(self.failed_notifications)
        }
        
    def register_notification_callback(self, channel: NotificationChannel,
                                     callback: Callable[[Alert], None]):
        """Register callback for alert notifications."""
        self.notification_callbacks[channel].append(callback)
        
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.rule_id}")
        
    def add_escalation_policy(self, policy: EscalationPolicy):
        """Add a new escalation policy."""
        self.escalation_policies[policy.policy_id] = policy
        self.logger.info(f"Added escalation policy: {policy.policy_id}")
        
    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed due to deduplication."""
        if alert.fingerprint in self.suppressed_fingerprints:
            return True
            
        # Check for similar recent alerts
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        similar_recent = [
            a for a in self.alert_history
            if (a.fingerprint == alert.fingerprint and 
                a.created_at > recent_cutoff and
                a.status == "active")
        ]
        
        if len(similar_recent) >= 3:  # Suppress after 3 similar alerts
            self.suppressed_fingerprints.add(alert.fingerprint)
            return True
            
        return False
        
    def _group_alert(self, alert: Alert):
        """Group alerts by type and severity for batch processing."""
        group_key = f"{alert.alert_type.value}_{alert.severity.value}"
        self.alert_groups[group_key].append(alert.alert_id)
        
    def _send_alert_notifications(self, alert: Alert):
        """Send notifications for alert through configured channels."""
        # Find applicable escalation policy
        escalation_policy = None
        for rule in self.alert_rules.values():
            if (rule.alert_type == alert.alert_type and 
                rule.escalation_policy in self.escalation_policies):
                escalation_policy = self.escalation_policies[rule.escalation_policy]
                break
                
        # Send immediate notifications (escalation step 0)
        if escalation_policy and escalation_policy.escalation_steps:
            first_step = escalation_policy.escalation_steps[0]
            for channel in first_step["channels"]:
                self._send_notification(alert, channel, first_step["recipients"])
                
    def _send_notification(self, alert: Alert, channel: NotificationChannel, recipients: List[str]):
        """Send notification through specific channel."""
        try:
            # Execute registered callbacks
            for callback in self.notification_callbacks[channel]:
                callback(alert)
                
            self.logger.info(f"Sent {channel.value} notification for alert {alert.alert_id}")
            
        except Exception as e:
            self.failed_notifications.append({
                'alert_id': alert.alert_id,
                'channel': channel.value,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            })
            self.logger.error(f"Failed to send {channel.value} notification: {e}")
            
    def _schedule_escalation(self, alert: Alert):
        """Schedule automatic escalation for alert."""
        # This would be implemented with a proper task scheduler in production
        # For now, we'll just log the scheduling
        self.logger.info(f"Scheduled escalation for alert {alert.alert_id}")
        
    def _check_consecutive_breaches(self, rule: AlertRule, metric_value: float) -> bool:
        """Check if consecutive breaches requirement is met."""
        if rule.require_consecutive_breaches <= 1:
            return True
            
        # In a full implementation, this would track metric history
        # For now, we'll assume the requirement is met
        return True
        
    def _update_avg_resolution_time(self, resolution_time: float):
        """Update average resolution time statistics."""
        current_avg = self.alert_stats['avg_resolution_time']
        resolved_count = self.alert_stats['alerts_resolved']
        
        if resolved_count <= 1:
            self.alert_stats['avg_resolution_time'] = resolution_time
        else:
            # Update rolling average
            self.alert_stats['avg_resolution_time'] = (
                (current_avg * (resolved_count - 1) + resolution_time) / resolved_count
            )
            
    def _start_background_tasks(self):
        """Start background tasks for alert processing."""
        # Auto-resolution task
        auto_resolve_thread = threading.Thread(
            target=self._auto_resolve_worker,
            daemon=True
        )
        auto_resolve_thread.start()
        self.background_tasks.append(auto_resolve_thread)
        
    def _auto_resolve_worker(self):
        """Background worker for auto-resolving expired alerts."""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now(timezone.utc)
                alerts_to_resolve = []
                
                for alert_id, alert in self.active_alerts.items():
                    if (alert.auto_resolve_after and 
                        current_time - alert.created_at > alert.auto_resolve_after):
                        alerts_to_resolve.append(alert_id)
                        
                # Auto-resolve expired alerts
                for alert_id in alerts_to_resolve:
                    self.resolve_alert(alert_id, "auto_resolver", "Auto-resolved due to timeout")
                    
            except Exception as e:
                self.logger.error(f"Auto-resolve worker error: {e}")
                
            # Sleep for 1 minute before next check
            self.shutdown_event.wait(60)
            
    def shutdown(self):
        """Gracefully shutdown alert manager."""
        self.shutdown_event.set()
        for task in self.background_tasks:
            if task.is_alive():
                task.join(timeout=5)