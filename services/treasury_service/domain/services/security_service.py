"""Service to manage role-based permissions and user creation."""

from typing import Dict, List, Set
from ..entities.user import Role, Permission, User
from ..value_objects.common import EntityId


class RolePermissionService:
    """Service to manage role-based permissions."""
    
    # Define role-based permission mapping
    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.VIEWER: {
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_KPI,
        },
        
        Role.TREASURY_ANALYST: {
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_FORECASTS,
            Permission.VIEW_KPI,
            Permission.VIEW_ANALYTICS,
            Permission.CREATE_FORECASTS,
            Permission.GENERATE_REPORTS,
        },
        
        Role.TREASURY_MANAGER: {
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_FORECASTS,
            Permission.VIEW_KPI,
            Permission.VIEW_ANALYTICS,
            Permission.CREATE_FORECASTS,
            Permission.APPROVE_PAYMENTS_LOW,
            Permission.APPROVE_PAYMENTS_MED,
            Permission.MODIFY_LIMITS,
            Permission.MANAGE_COUNTERPARTIES,
            Permission.EXPORT_DATA,
            Permission.GENERATE_REPORTS,
            Permission.VIEW_RISK_REPORTS,
        },
        
        Role.PAYMENT_APPROVER: {
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.APPROVE_PAYMENTS_LOW,
            Permission.APPROVE_PAYMENTS_MED,
            Permission.APPROVE_PAYMENTS_HIGH,
            Permission.VIEW_KPI,
            Permission.EXPORT_DATA,
        },
        
        Role.RISK_OFFICER: {
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_FORECASTS,
            Permission.VIEW_KPI,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_RISK_REPORTS,
            Permission.MANAGE_RISK_LIMITS,
            Permission.EXPORT_DATA,
            Permission.GENERATE_REPORTS,
        },
        
        Role.CFO: {
            # CFO has all operational permissions except system admin
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_FORECASTS,
            Permission.VIEW_KPI,
            Permission.VIEW_ANALYTICS,
            Permission.CREATE_FORECASTS,
            Permission.APPROVE_PAYMENTS_LOW,
            Permission.APPROVE_PAYMENTS_MED,
            Permission.APPROVE_PAYMENTS_HIGH,
            Permission.MODIFY_LIMITS,
            Permission.MANAGE_COUNTERPARTIES,
            Permission.EXPORT_DATA,
            Permission.GENERATE_REPORTS,
            Permission.VIEW_RISK_REPORTS,
            Permission.MANAGE_RISK_LIMITS,
            Permission.MANAGE_USERS,
            Permission.VIEW_SYSTEM_LOGS,
        },
        
        Role.AUDITOR: {
            Permission.VIEW_BALANCES,
            Permission.VIEW_TRANSACTIONS,
            Permission.VIEW_FORECASTS,
            Permission.VIEW_KPI,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_RISK_REPORTS,
            Permission.AUDIT_ACCESS,
            Permission.EXPORT_DATA,
            Permission.GENERATE_REPORTS,
            Permission.VIEW_SYSTEM_LOGS,
        },
    }
    
    # Define role hierarchy for inheritance
    ROLE_HIERARCHY: Dict[Role, List[Role]] = {
        Role.CFO: [Role.TREASURY_MANAGER, Role.PAYMENT_APPROVER, Role.RISK_OFFICER],
        Role.TREASURY_MANAGER: [Role.TREASURY_ANALYST],
        Role.PAYMENT_APPROVER: [Role.VIEWER],
        Role.RISK_OFFICER: [Role.TREASURY_ANALYST],
        Role.AUDITOR: [Role.VIEWER],
        Role.TREASURY_ANALYST: [Role.VIEWER],
    }
    
    @classmethod
    def get_permissions_for_role(cls, role: Role, include_inherited: bool = True) -> List[Permission]:
        """Get all permissions for a given role, optionally including inherited permissions."""
        permissions = set(cls.ROLE_PERMISSIONS.get(role, set()))
        
        if include_inherited:
            # Add permissions from inherited roles
            inherited_roles = cls.ROLE_HIERARCHY.get(role, [])
            for inherited_role in inherited_roles:
                inherited_permissions = cls.get_permissions_for_role(inherited_role, True)
                permissions.update(inherited_permissions)
        
        return list(permissions)
    
    @classmethod
    def role_has_permission(cls, role: Role, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        role_permissions = cls.get_permissions_for_role(role)
        return permission in role_permissions
    
    @classmethod
    def get_role_description(cls, role: Role) -> str:
        """Get human-readable description of role."""
        descriptions = {
            Role.VIEWER: "Read-only access to treasury data and reports",
            Role.TREASURY_ANALYST: "Analysis, forecasting, and reporting capabilities",
            Role.TREASURY_MANAGER: "Full treasury operations including low-medium payment approvals",
            Role.PAYMENT_APPROVER: "Specialized role for payment approvals at all levels",
            Role.RISK_OFFICER: "Risk management, monitoring, and compliance oversight",
            Role.CFO: "Executive level access with full treasury management capabilities",
            Role.AUDITOR: "Audit and compliance access with read-only permissions",
        }
        return descriptions.get(role, "Unknown role")
    
    @classmethod
    def get_default_entity_access(cls, role: Role) -> List[str]:
        """Get default entity access based on role."""
        # CFO and Auditor get access to all entities (handled in User.can_access_entity)
        if role in [Role.CFO, Role.AUDITOR]:
            return ["ALL"]
        
        # Other roles get limited entity access by default
        return ["ENT-01"]  # Default to first entity, should be customized per user
    
    @classmethod
    def create_user_with_role(
        cls,
        user_id: str,
        username: str,
        email: str,
        full_name: str,
        role: Role,
        entity_access: List[str] = None,
        password_hash: str = None
    ) -> User:
        """Create user with appropriate permissions for role."""
        permissions = cls.get_permissions_for_role(role)
        
        # Use default entity access if not specified
        if entity_access is None:
            entity_access = cls.get_default_entity_access(role)
        
        return User(
            user_id=EntityId(user_id),
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            entity_access=entity_access,
            permissions=permissions,
            password_hash=password_hash
        )
    
    @classmethod
    def can_role_perform_action(cls, role: Role, action: str, context: dict = None) -> bool:
        """
        Check if role can perform specific business action.
        
        Args:
            role: User role
            action: Business action (e.g., 'approve_payment', 'view_forecast')
            context: Additional context (e.g., payment amount, entity)
        """
        context = context or {}
        
        # Payment approval logic
        if action == "approve_payment":
            amount = context.get("amount", 0)
            if amount <= 50000:
                return cls.role_has_permission(role, Permission.APPROVE_PAYMENTS_LOW)
            elif amount <= 250000:
                return cls.role_has_permission(role, Permission.APPROVE_PAYMENTS_MED)
            else:
                return cls.role_has_permission(role, Permission.APPROVE_PAYMENTS_HIGH)
        
        # Map common actions to permissions
        action_permission_map = {
            "view_balances": Permission.VIEW_BALANCES,
            "view_transactions": Permission.VIEW_TRANSACTIONS,
            "view_forecasts": Permission.VIEW_FORECASTS,
            "view_analytics": Permission.VIEW_ANALYTICS,
            "create_forecasts": Permission.CREATE_FORECASTS,
            "export_data": Permission.EXPORT_DATA,
            "manage_users": Permission.MANAGE_USERS,
            "view_system_logs": Permission.VIEW_SYSTEM_LOGS,
        }
        
        required_permission = action_permission_map.get(action)
        if required_permission:
            return cls.role_has_permission(role, required_permission)
        
        return False
    
    @classmethod
    def get_available_actions(cls, role: Role) -> List[str]:
        """Get list of available actions for a role."""
        permissions = cls.get_permissions_for_role(role)
        actions = []
        
        # Map permissions to user-friendly actions
        permission_action_map = {
            Permission.VIEW_BALANCES: "View Account Balances",
            Permission.VIEW_TRANSACTIONS: "View Transaction History",
            Permission.VIEW_FORECASTS: "View Cash Flow Forecasts",
            Permission.VIEW_ANALYTICS: "View Analytics Dashboard",
            Permission.CREATE_FORECASTS: "Create New Forecasts",
            Permission.APPROVE_PAYMENTS_LOW: "Approve Payments (<$50K)",
            Permission.APPROVE_PAYMENTS_MED: "Approve Payments (<$250K)",
            Permission.APPROVE_PAYMENTS_HIGH: "Approve Payments (>$250K)",
            Permission.EXPORT_DATA: "Export Data and Reports",
            Permission.MANAGE_USERS: "Manage Users",
            Permission.VIEW_SYSTEM_LOGS: "View System Logs",
        }
        
        for permission in permissions:
            action = permission_action_map.get(permission)
            if action:
                actions.append(action)
        
        return sorted(actions)