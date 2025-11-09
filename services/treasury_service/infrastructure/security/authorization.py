"""Role-based access control (RBAC) and authorization service."""

from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from ..observability import get_observability_manager
from .authentication import User, Permission, UserRole


class ResourceType(Enum):
    """Types of resources in the treasury system."""
    CASH_ACCOUNT = "cash_account"
    PAYMENT = "payment"
    INVESTMENT = "investment"
    RISK_REPORT = "risk_report"
    COLLECTION = "collection"
    COMPLIANCE_REPORT = "compliance_report"
    USER = "user"
    WORKFLOW = "workflow"
    DASHBOARD = "dashboard"
    AUDIT_LOG = "audit_log"


class AccessLevel(Enum):
    """Access levels for resources."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass
class AccessRequest:
    """Represents an access request to a resource."""
    user_id: str
    resource_type: ResourceType
    resource_id: str
    action: str
    context: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class AccessResult:
    """Result of an access control decision."""
    granted: bool
    reason: str
    required_permissions: List[Permission]
    user_permissions: List[Permission]
    access_level: AccessLevel
    additional_context: Dict[str, Any] = None


@dataclass
class ResourcePolicy:
    """Defines access policy for a resource type."""
    resource_type: ResourceType
    read_permissions: List[Permission]
    write_permissions: List[Permission]
    admin_permissions: List[Permission]
    owner_permissions: List[Permission]
    additional_rules: Dict[str, Any] = None


class RBACManager:
    """Role-Based Access Control manager."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.rbac_manager")
        
        # Resource policies
        self.resource_policies = self._init_resource_policies()
        
        # Dynamic access rules
        self.access_rules: Dict[str, Any] = {}
        
    def _init_resource_policies(self) -> Dict[ResourceType, ResourcePolicy]:
        """Initialize resource access policies."""
        policies = {}
        
        # Cash Account policies
        policies[ResourceType.CASH_ACCOUNT] = ResourcePolicy(
            resource_type=ResourceType.CASH_ACCOUNT,
            read_permissions=[Permission.CASH_READ],
            write_permissions=[Permission.CASH_WRITE],
            admin_permissions=[Permission.CASH_ADMIN],
            owner_permissions=[Permission.CASH_ADMIN]
        )
        
        # Payment policies
        policies[ResourceType.PAYMENT] = ResourcePolicy(
            resource_type=ResourceType.PAYMENT,
            read_permissions=[Permission.PAYMENT_VIEW],
            write_permissions=[Permission.PAYMENT_INITIATE],
            admin_permissions=[Permission.PAYMENT_ADMIN],
            owner_permissions=[Permission.PAYMENT_APPROVE]
        )
        
        # Investment policies
        policies[ResourceType.INVESTMENT] = ResourcePolicy(
            resource_type=ResourceType.INVESTMENT,
            read_permissions=[Permission.INVESTMENT_VIEW],
            write_permissions=[Permission.INVESTMENT_ANALYZE],
            admin_permissions=[Permission.INVESTMENT_ADMIN],
            owner_permissions=[Permission.INVESTMENT_EXECUTE]
        )
        
        # Risk Report policies
        policies[ResourceType.RISK_REPORT] = ResourcePolicy(
            resource_type=ResourceType.RISK_REPORT,
            read_permissions=[Permission.RISK_VIEW],
            write_permissions=[Permission.RISK_ASSESS],
            admin_permissions=[Permission.RISK_ADMIN],
            owner_permissions=[Permission.RISK_MANAGE]
        )
        
        # Collection policies
        policies[ResourceType.COLLECTION] = ResourcePolicy(
            resource_type=ResourceType.COLLECTION,
            read_permissions=[Permission.COLLECTIONS_VIEW],
            write_permissions=[Permission.COLLECTIONS_MANAGE],
            admin_permissions=[Permission.COLLECTIONS_ADMIN],
            owner_permissions=[Permission.COLLECTIONS_ADMIN]
        )
        
        # Compliance Report policies
        policies[ResourceType.COMPLIANCE_REPORT] = ResourcePolicy(
            resource_type=ResourceType.COMPLIANCE_REPORT,
            read_permissions=[Permission.COMPLIANCE_VIEW],
            write_permissions=[Permission.COMPLIANCE_AUDIT],
            admin_permissions=[Permission.COMPLIANCE_ADMIN],
            owner_permissions=[Permission.COMPLIANCE_ADMIN]
        )
        
        # User management policies
        policies[ResourceType.USER] = ResourcePolicy(
            resource_type=ResourceType.USER,
            read_permissions=[Permission.USER_VIEW],
            write_permissions=[Permission.USER_MANAGE],
            admin_permissions=[Permission.SYSTEM_ADMIN],
            owner_permissions=[Permission.SYSTEM_ADMIN]
        )
        
        # Workflow policies
        policies[ResourceType.WORKFLOW] = ResourcePolicy(
            resource_type=ResourceType.WORKFLOW,
            read_permissions=[Permission.CASH_READ],  # Basic access to view workflows
            write_permissions=[Permission.CASH_WRITE],  # Ability to create/modify workflows
            admin_permissions=[Permission.SYSTEM_CONFIG],  # Workflow configuration
            owner_permissions=[Permission.SYSTEM_ADMIN]  # Full workflow control
        )
        
        return policies
        
    def check_access(self, user: User, resource_type: ResourceType, action: str,
                    resource_id: str = None, context: Dict[str, Any] = None) -> AccessResult:
        """Check if a user has access to perform an action on a resource."""
        
        access_request = AccessRequest(
            user_id=user.user_id,
            resource_type=resource_type,
            resource_id=resource_id or "unknown",
            action=action,
            context=context or {}
        )
        
        # Get resource policy
        policy = self.resource_policies.get(resource_type)
        if not policy:
            return AccessResult(
                granted=False,
                reason=f"No policy defined for resource type {resource_type.value}",
                required_permissions=[],
                user_permissions=user.permissions,
                access_level=AccessLevel.NONE
            )
            
        # Determine required permissions based on action
        required_permissions = self._get_required_permissions(policy, action)
        
        # Check if user has required permissions
        user_permission_values = {perm.value for perm in user.permissions}
        required_permission_values = {perm.value for perm in required_permissions}
        
        has_access = required_permission_values.issubset(user_permission_values)
        
        # Determine access level
        access_level = self._determine_access_level(user.permissions, policy)
        
        # Apply additional business rules
        if has_access:
            has_access = self._apply_business_rules(user, access_request, policy)
            
        result = AccessResult(
            granted=has_access,
            reason=self._get_access_reason(has_access, required_permissions, user.permissions),
            required_permissions=required_permissions,
            user_permissions=user.permissions,
            access_level=access_level,
            additional_context={
                "resource_type": resource_type.value,
                "action": action,
                "user_role": user.role.value
            }
        )
        
        # Log access attempt
        self.logger.info(
            f"Access check: {action} on {resource_type.value}",
            user_id=user.user_id,
            resource_type=resource_type.value,
            action=action,
            granted=has_access,
            reason=result.reason
        )
        
        return result
        
    def _get_required_permissions(self, policy: ResourcePolicy, action: str) -> List[Permission]:
        """Get required permissions for an action based on policy."""
        action_lower = action.lower()
        
        if action_lower in ['read', 'view', 'list', 'get']:
            return policy.read_permissions
        elif action_lower in ['create', 'update', 'write', 'modify']:
            return policy.write_permissions
        elif action_lower in ['delete', 'admin', 'configure']:
            return policy.admin_permissions
        elif action_lower in ['approve', 'execute', 'own']:
            return policy.owner_permissions
        else:
            # Default to read permissions for unknown actions
            return policy.read_permissions
            
    def _determine_access_level(self, user_permissions: List[Permission], 
                               policy: ResourcePolicy) -> AccessLevel:
        """Determine the highest access level a user has for a resource."""
        user_perm_set = set(user_permissions)
        
        if set(policy.owner_permissions).issubset(user_perm_set):
            return AccessLevel.OWNER
        elif set(policy.admin_permissions).issubset(user_perm_set):
            return AccessLevel.ADMIN
        elif set(policy.write_permissions).issubset(user_perm_set):
            return AccessLevel.WRITE
        elif set(policy.read_permissions).issubset(user_perm_set):
            return AccessLevel.READ
        else:
            return AccessLevel.NONE
            
    def _apply_business_rules(self, user: User, request: AccessRequest, 
                             policy: ResourcePolicy) -> bool:
        """Apply additional business rules for access control."""
        
        # Time-based access rules
        current_hour = datetime.now(timezone.utc).hour
        
        # Restrict certain high-risk operations to business hours (9 AM - 6 PM UTC)
        high_risk_actions = ['approve', 'execute', 'delete']
        if request.action.lower() in high_risk_actions:
            if not (9 <= current_hour <= 18):
                if user.role not in [UserRole.SUPER_ADMIN, UserRole.TREASURER]:
                    self.logger.warning(
                        f"High-risk action {request.action} blocked outside business hours",
                        user_id=user.user_id,
                        action=request.action,
                        hour=current_hour
                    )
                    return False
                    
        # Amount-based rules for payments
        if request.resource_type == ResourceType.PAYMENT and request.context:
            amount = request.context.get('amount', 0)
            
            # Large payments require higher authorization
            if amount > 1000000:  # $1M threshold
                if user.role not in [UserRole.SUPER_ADMIN, UserRole.TREASURER]:
                    return False
                    
            # Very large payments require super admin
            if amount > 10000000:  # $10M threshold
                if user.role != UserRole.SUPER_ADMIN:
                    return False
                    
        # Geographic restrictions
        if request.context and request.context.get('country_code'):
            restricted_countries = ['CU', 'IR', 'KP', 'SY']  # Example restricted countries
            if request.context['country_code'] in restricted_countries:
                if user.role != UserRole.SUPER_ADMIN:
                    self.logger.warning(
                        f"Access to restricted country blocked",
                        user_id=user.user_id,
                        country_code=request.context['country_code']
                    )
                    return False
                    
        return True
        
    def _get_access_reason(self, granted: bool, required_permissions: List[Permission],
                          user_permissions: List[Permission]) -> str:
        """Generate human-readable reason for access decision."""
        if granted:
            return "Access granted - user has required permissions"
        else:
            missing_perms = set(required_permissions) - set(user_permissions)
            if missing_perms:
                missing_names = [perm.value for perm in missing_perms]
                return f"Access denied - missing permissions: {', '.join(missing_names)}"
            else:
                return "Access denied - business rule violation"


class AuthorizationService:
    """Main authorization service for the treasury system."""
    
    def __init__(self):
        self.rbac_manager = RBACManager()
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.authorization")
        
        # Access decision cache (in production, use Redis or similar)
        self.decision_cache: Dict[str, AccessResult] = {}
        
    def authorize(self, user: User, resource_type: ResourceType, action: str,
                 resource_id: str = None, context: Dict[str, Any] = None) -> bool:
        """Authorize a user action - returns True/False."""
        result = self.check_authorization(user, resource_type, action, resource_id, context)
        return result.granted
        
    def check_authorization(self, user: User, resource_type: ResourceType, action: str,
                           resource_id: str = None, context: Dict[str, Any] = None) -> AccessResult:
        """Check authorization and return detailed result."""
        
        # Check cache first (optional optimization)
        cache_key = f"{user.user_id}:{resource_type.value}:{action}:{resource_id}"
        
        # For now, skip caching for real-time decisions
        result = self.rbac_manager.check_access(user, resource_type, action, resource_id, context)
        
        # Log authorization decision
        self.logger.info(
            f"Authorization decision",
            user_id=user.user_id,
            username=user.username,
            resource_type=resource_type.value,
            action=action,
            resource_id=resource_id,
            granted=result.granted,
            access_level=result.access_level.value
        )
        
        return result
        
    def get_user_resource_access(self, user: User, resource_type: ResourceType) -> Dict[str, Any]:
        """Get summary of user's access to a resource type."""
        policy = self.rbac_manager.resource_policies.get(resource_type)
        if not policy:
            return {"access_level": AccessLevel.NONE.value, "permissions": []}
            
        access_level = self.rbac_manager._determine_access_level(user.permissions, policy)
        
        return {
            "access_level": access_level.value,
            "permissions": [perm.value for perm in user.permissions],
            "can_read": self.authorize(user, resource_type, "read"),
            "can_write": self.authorize(user, resource_type, "write"), 
            "can_admin": self.authorize(user, resource_type, "admin"),
            "resource_type": resource_type.value
        }
        
    def get_user_all_access(self, user: User) -> Dict[ResourceType, Dict[str, Any]]:
        """Get user's access summary for all resource types."""
        access_summary = {}
        
        for resource_type in ResourceType:
            access_summary[resource_type] = self.get_user_resource_access(user, resource_type)
            
        return access_summary
        
    def require_permission(self, permission: Permission):
        """Decorator factory for requiring specific permissions."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # This would be implemented as a decorator in a web framework
                # For now, it's a placeholder for the concept
                pass
            return wrapper
        return decorator