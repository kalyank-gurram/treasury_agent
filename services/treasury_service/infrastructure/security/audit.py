"""Security audit logging and event tracking system."""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from ..observability import get_observability_manager


class SecurityEventType(Enum):
    """Types of security events to audit."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    
    # Data events
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # System events
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_SUSPENDED = "user_suspended"
    CONFIG_CHANGE = "config_change"
    
    # Treasury-specific events
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_REJECTED = "payment_rejected"
    INVESTMENT_CREATED = "investment_created"
    INVESTMENT_EXECUTED = "investment_executed"
    RISK_ALERT_TRIGGERED = "risk_alert_triggered"
    COMPLIANCE_VIOLATION = "compliance_violation"
    
    # Security incidents
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_BREACH = "security_breach"
    MULTIPLE_LOGIN_FAILURES = "multiple_login_failures"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"


class SeverityLevel(Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Represents a security audit event."""
    event_id: str
    event_type: SecurityEventType
    severity: SeverityLevel
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: Optional[str]
    result: str  # success, failure, etc.
    details: Dict[str, Any]
    risk_score: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data
        
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
        
    def calculate_hash(self) -> str:
        """Calculate hash of event for integrity verification."""
        # Create deterministic string representation
        data = self.to_dict()
        # Remove mutable fields that shouldn't affect hash
        hash_data = {k: v for k, v in data.items() if k not in ['event_id']}
        
        json_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


@dataclass
class AuditTrail:
    """Represents an audit trail for a specific entity or process."""
    trail_id: str
    entity_type: str  # user, payment, investment, etc.
    entity_id: str
    events: List[SecurityEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_event(self, event: SecurityEvent):
        """Add an event to the audit trail."""
        self.events.append(event)
        self.last_updated = datetime.now(timezone.utc)
        
    def get_events_by_type(self, event_type: SecurityEventType) -> List[SecurityEvent]:
        """Get all events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]
        
    def get_events_by_severity(self, severity: SeverityLevel) -> List[SecurityEvent]:
        """Get all events of a specific severity."""
        return [event for event in self.events if event.severity == severity]


class AuditLogger:
    """Main security audit logging service."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.audit_logger")
        
        # Event storage (in production, use database or SIEM)
        self.events: Dict[str, SecurityEvent] = {}
        self.audit_trails: Dict[str, AuditTrail] = {}
        
        # Risk scoring configuration
        self.risk_scores = self._init_risk_scores()
        
        # Alert thresholds
        self.alert_thresholds = {
            'login_failures_per_hour': 5,
            'high_severity_events_per_hour': 3,
            'critical_events_per_day': 1
        }
        
    def _init_risk_scores(self) -> Dict[SecurityEventType, float]:
        """Initialize risk scores for different event types."""
        return {
            SecurityEventType.LOGIN_SUCCESS: 0.1,
            SecurityEventType.LOGIN_FAILURE: 0.3,
            SecurityEventType.LOGOUT: 0.0,
            SecurityEventType.TOKEN_REFRESH: 0.1,
            SecurityEventType.PASSWORD_CHANGE: 0.2,
            SecurityEventType.MFA_ENABLED: 0.0,
            SecurityEventType.MFA_DISABLED: 0.8,
            
            SecurityEventType.ACCESS_GRANTED: 0.1,
            SecurityEventType.ACCESS_DENIED: 0.5,
            SecurityEventType.PERMISSION_CHANGE: 0.6,
            SecurityEventType.ROLE_CHANGE: 0.7,
            
            SecurityEventType.DATA_READ: 0.1,
            SecurityEventType.DATA_WRITE: 0.3,
            SecurityEventType.DATA_DELETE: 0.8,
            SecurityEventType.DATA_EXPORT: 0.6,
            
            SecurityEventType.USER_CREATED: 0.3,
            SecurityEventType.USER_DELETED: 0.8,
            SecurityEventType.USER_SUSPENDED: 0.5,
            SecurityEventType.CONFIG_CHANGE: 0.7,
            
            SecurityEventType.PAYMENT_INITIATED: 0.4,
            SecurityEventType.PAYMENT_APPROVED: 0.3,
            SecurityEventType.PAYMENT_REJECTED: 0.2,
            SecurityEventType.INVESTMENT_CREATED: 0.4,
            SecurityEventType.INVESTMENT_EXECUTED: 0.5,
            SecurityEventType.RISK_ALERT_TRIGGERED: 0.7,
            SecurityEventType.COMPLIANCE_VIOLATION: 0.9,
            
            SecurityEventType.SUSPICIOUS_ACTIVITY: 0.9,
            SecurityEventType.SECURITY_BREACH: 1.0,
            SecurityEventType.MULTIPLE_LOGIN_FAILURES: 0.8,
            SecurityEventType.UNUSUAL_ACCESS_PATTERN: 0.6
        }
        
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import secrets
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(8)
        return f"evt_{timestamp}_{random_suffix}"
        
    def _calculate_severity(self, event_type: SecurityEventType, 
                           context: Dict[str, Any]) -> SeverityLevel:
        """Calculate severity level based on event type and context."""
        base_risk = self.risk_scores.get(event_type, 0.5)
        
        # Adjust based on context
        if context.get('amount', 0) > 1000000:  # Large financial amounts
            base_risk += 0.3
        if context.get('after_hours', False):  # After business hours
            base_risk += 0.2
        if context.get('unusual_location', False):  # Unusual geographic location
            base_risk += 0.3
        if context.get('privilege_escalation', False):  # Privilege changes
            base_risk += 0.4
            
        # Map risk score to severity
        if base_risk >= 0.8:
            return SeverityLevel.CRITICAL
        elif base_risk >= 0.6:
            return SeverityLevel.HIGH
        elif base_risk >= 0.3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
            
    def log_event(self, event_type: SecurityEventType, user_id: str = None,
                  session_id: str = None, ip_address: str = None,
                  user_agent: str = None, resource_type: str = None,
                  resource_id: str = None, action: str = None,
                  result: str = "success", details: Dict[str, Any] = None) -> SecurityEvent:
        """Log a security event."""
        
        details = details or {}
        event_id = self._generate_event_id()
        
        # Calculate severity and risk score
        severity = self._calculate_severity(event_type, details)
        risk_score = self.risk_scores.get(event_type, 0.5)
        
        # Create event
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details,
            risk_score=risk_score
        )
        
        # Store event
        self.events[event_id] = event
        
        # Add to audit trail if applicable
        if resource_type and resource_id:
            self._add_to_audit_trail(event, resource_type, resource_id)
            
        # Log to system logger
        self.logger.info(
            f"Security event: {event_type.value}",
            event_id=event_id,
            user_id=user_id,
            severity=severity.value,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            risk_score=risk_score
        )
        
        # Check for alerts
        self._check_alert_conditions(event)
        
        return event
        
    def _add_to_audit_trail(self, event: SecurityEvent, entity_type: str, entity_id: str):
        """Add event to relevant audit trail."""
        trail_key = f"{entity_type}:{entity_id}"
        
        if trail_key not in self.audit_trails:
            self.audit_trails[trail_key] = AuditTrail(
                trail_id=f"trail_{trail_key}",
                entity_type=entity_type,
                entity_id=entity_id
            )
            
        self.audit_trails[trail_key].add_event(event)
        
    def _check_alert_conditions(self, event: SecurityEvent):
        """Check if event triggers any security alerts."""
        now = datetime.now(timezone.utc)
        hour_ago = now.replace(minute=0, second=0, microsecond=0)
        day_ago = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check login failure rate
        if event.event_type == SecurityEventType.LOGIN_FAILURE and event.user_id:
            recent_failures = self._count_events_since(
                SecurityEventType.LOGIN_FAILURE, hour_ago, user_id=event.user_id
            )
            
            if recent_failures >= self.alert_thresholds['login_failures_per_hour']:
                self._trigger_alert(
                    "Multiple login failures detected",
                    SeverityLevel.HIGH,
                    {"user_id": event.user_id, "failure_count": recent_failures}
                )
                
        # Check high severity events
        if event.severity == SeverityLevel.HIGH:
            recent_high_severity = self._count_events_since(
                None, hour_ago, severity=SeverityLevel.HIGH
            )
            
            if recent_high_severity >= self.alert_thresholds['high_severity_events_per_hour']:
                self._trigger_alert(
                    "High number of high-severity security events",
                    SeverityLevel.CRITICAL,
                    {"high_severity_count": recent_high_severity}
                )
                
        # Check critical events
        if event.severity == SeverityLevel.CRITICAL:
            recent_critical = self._count_events_since(
                None, day_ago, severity=SeverityLevel.CRITICAL
            )
            
            if recent_critical >= self.alert_thresholds['critical_events_per_day']:
                self._trigger_alert(
                    "Critical security events detected",
                    SeverityLevel.CRITICAL,
                    {"critical_count": recent_critical}
                )
                
    def _count_events_since(self, event_type: SecurityEventType = None,
                           since: datetime = None, user_id: str = None,
                           severity: SeverityLevel = None) -> int:
        """Count events matching criteria since a specific time."""
        count = 0
        for event in self.events.values():
            if since and event.timestamp < since:
                continue
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if severity and event.severity != severity:
                continue
            count += 1
            
        return count
        
    def _trigger_alert(self, message: str, severity: SeverityLevel, 
                      context: Dict[str, Any]):
        """Trigger a security alert."""
        alert_event = self.log_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            result="alert_triggered",
            details={
                "alert_message": message,
                "alert_context": context,
                "auto_generated": True
            }
        )
        
        # In production, this would send alerts to security team
        self.logger.warning(
            f"SECURITY ALERT: {message}",
            severity=severity.value,
            context=context,
            event_id=alert_event.event_id
        )
        
    def get_audit_trail(self, entity_type: str, entity_id: str) -> Optional[AuditTrail]:
        """Get audit trail for a specific entity."""
        trail_key = f"{entity_type}:{entity_id}"
        return self.audit_trails.get(trail_key)
        
    def search_events(self, event_type: SecurityEventType = None,
                     user_id: str = None, severity: SeverityLevel = None,
                     start_time: datetime = None, end_time: datetime = None,
                     limit: int = 100) -> List[SecurityEvent]:
        """Search security events with filtering."""
        results = []
        
        for event in self.events.values():
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if severity and event.severity != severity:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
                
            results.append(event)
            
            if len(results) >= limit:
                break
                
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return results
        
    def get_security_summary(self, time_period_hours: int = 24) -> Dict[str, Any]:
        """Get security event summary for a time period."""
        since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if time_period_hours < 24:
            since = datetime.now(timezone.utc) - timedelta(hours=time_period_hours)
            
        recent_events = self.search_events(start_time=since)
        
        # Count by type
        type_counts = {}
        for event in recent_events:
            type_counts[event.event_type.value] = type_counts.get(event.event_type.value, 0) + 1
            
        # Count by severity
        severity_counts = {}
        for event in recent_events:
            severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
            
        # Calculate risk metrics
        total_risk_score = sum(event.risk_score or 0 for event in recent_events)
        avg_risk_score = total_risk_score / len(recent_events) if recent_events else 0
        
        return {
            "time_period_hours": time_period_hours,
            "total_events": len(recent_events),
            "events_by_type": type_counts,
            "events_by_severity": severity_counts,
            "average_risk_score": round(avg_risk_score, 3),
            "total_risk_score": round(total_risk_score, 3),
            "high_risk_events": len([e for e in recent_events if (e.risk_score or 0) >= 0.7]),
            "unique_users": len(set(e.user_id for e in recent_events if e.user_id))
        }