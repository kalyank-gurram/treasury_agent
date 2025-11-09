"""User domain entities for authentication and authorization."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from ..value_objects.common import EntityId


class Role(Enum):
    """Treasury user roles with hierarchical permissions."""
    VIEWER = "viewer"
    TREASURY_ANALYST = "treasury_analyst"
    TREASURY_MANAGER = "treasury_manager"
    PAYMENT_APPROVER = "payment_approver"
    RISK_OFFICER = "risk_officer"
    CFO = "cfo"
    AUDITOR = "auditor"


class Permission(Enum):
    """Granular permissions for treasury operations."""
    
    # Data Access Permissions
    VIEW_BALANCES = "view_balances"
    VIEW_TRANSACTIONS = "view_transactions"
    VIEW_FORECASTS = "view_forecasts"
    VIEW_KPI = "view_kpi"
    VIEW_ANALYTICS = "view_analytics"
    
    # Operational Permissions
    CREATE_FORECASTS = "create_forecasts"
    APPROVE_PAYMENTS_LOW = "approve_payments_low"    # < $50K
    APPROVE_PAYMENTS_MED = "approve_payments_med"    # < $250K
    APPROVE_PAYMENTS_HIGH = "approve_payments_high"  # > $250K
    MODIFY_LIMITS = "modify_limits"
    MANAGE_COUNTERPARTIES = "manage_counterparties"
    
    # Risk & Compliance
    VIEW_RISK_REPORTS = "view_risk_reports"
    MANAGE_RISK_LIMITS = "manage_risk_limits"
    AUDIT_ACCESS = "audit_access"
    
    # Data Export & Reporting
    EXPORT_DATA = "export_data"
    GENERATE_REPORTS = "generate_reports"
    
    # Administration
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"
    VIEW_SYSTEM_LOGS = "view_system_logs"


@dataclass
class User:
    """Treasury system user with role-based permissions."""
    
    user_id: EntityId
    username: str
    email: str
    full_name: str
    role: Role
    entity_access: List[str]  # Entity IDs this user can access
    permissions: List[Permission] = field(default_factory=list)
    is_active: bool = True
    password_hash: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)
    
    def can_access_entity(self, entity_id: str) -> bool:
        """Check if user can access specific entity."""
        # CFO and Auditor have access to all entities
        if self.role in [Role.CFO, Role.AUDITOR]:
            return True
        return entity_id in self.entity_access
    
    def can_approve_payment(self, amount: float) -> bool:
        """Check if user can approve payment based on amount thresholds."""
        if amount <= 50000:
            return self.has_permission(Permission.APPROVE_PAYMENTS_LOW)
        elif amount <= 250000:
            return self.has_permission(Permission.APPROVE_PAYMENTS_MED)
        else:
            return self.has_permission(Permission.APPROVE_PAYMENTS_HIGH)
    
    def update_last_login(self) -> None:
        """Update last login timestamp and reset failed attempts."""
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.now(timezone.utc)
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts and lock if necessary."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        self.updated_at = datetime.now(timezone.utc)
    
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class UserSession:
    """Active user session with security context."""
    
    session_id: str
    user_id: EntityId
    username: str
    role: Role
    permissions: List[Permission]
    entity_access: List[str]
    login_time: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def extend_session(self, minutes: int = 30) -> None:
        """Extend session expiration."""
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    def to_jwt_payload(self) -> dict:
        """Convert session to JWT payload."""
        return {
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "username": self.username,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "entity_access": self.entity_access,
            "exp": int(self.expires_at.timestamp()),
            "iat": int(self.login_time.timestamp())
        }


@dataclass
class LoginAttempt:
    """Track login attempts for security monitoring."""
    
    attempt_id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    ip_address: str = ""
    user_agent: str = ""
    success: bool = False
    failure_reason: Optional[str] = None
    attempted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if self.attempt_id is None:
            self.attempt_id = str(uuid4())