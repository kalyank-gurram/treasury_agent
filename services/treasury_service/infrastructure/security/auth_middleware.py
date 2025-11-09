"""Authorization middleware for FastAPI with JWT and permission validation."""

from functools import wraps
from typing import Optional, Callable, List
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...domain.entities.user import User, Permission, Role
from .auth_service import AuthenticationService
from ..observability import get_observability_manager


class AuthMiddleware:
    """Middleware for handling authentication and authorization."""
    
    def __init__(self, auth_service: AuthenticationService):
        self.auth_service = auth_service
        self.security = HTTPBearer(auto_error=False)
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.middleware")
    
    async def get_current_user(self, request: Request) -> Optional[User]:
        """
        Extract current user from request.
        
        Supports both session-based and JWT authentication.
        """
        # Try session-based auth first (from cookies)
        session_id = request.cookies.get("session_id")
        if session_id:
            session = self.auth_service.validate_session(session_id)
            if session:
                user = self.auth_service.get_user_by_username(session.username)
                if user:
                    return user
        
        # Try JWT token auth (from Authorization header)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = self.auth_service.validate_jwt_token(token)
            if payload:
                username = payload.get('username')
                user = self.auth_service.get_user_by_username(username)
                return user
        
        return None
    
    def get_current_user_dependency(self) -> Callable:
        """FastAPI dependency to get current user."""
        async def _get_current_user(request: Request) -> Optional[User]:
            return await self.get_current_user(request)
        return _get_current_user
    
    def require_auth(self) -> Callable:
        """FastAPI dependency that requires authentication."""
        async def _require_auth(request: Request) -> User:
            user = await self.get_current_user(request)
            if not user:
                self.logger.warning(
                    "Unauthorized access attempt",
                    path=request.url.path,
                    method=request.method,
                    ip_address=request.client.host if request.client else "unknown"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            if user.is_locked():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="User account is locked"
                )
            
            # Log successful authentication
            self.logger.debug(
                "User authenticated",
                username=user.username,
                role=user.role.value,
                path=request.url.path
            )
            
            return user
        
        return _require_auth
    
    def require_permission(self, permission: Permission) -> Callable:
        """FastAPI dependency that requires specific permission."""
        async def _require_permission(
            request: Request,
            current_user: User = Depends(self.require_auth())
        ) -> User:
            if not current_user.has_permission(permission):
                self.logger.warning(
                    "Permission denied",
                    username=current_user.username,
                    required_permission=permission.value,
                    user_permissions=[p.value for p in current_user.permissions],
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission.value}"
                )
            
            return current_user
        
        return _require_permission
    
    def require_any_permission(self, permissions: List[Permission]) -> Callable:
        """FastAPI dependency that requires any of the specified permissions."""
        async def _require_any_permission(
            request: Request,
            current_user: User = Depends(self.require_auth())
        ) -> User:
            if not current_user.has_any_permission(permissions):
                permission_values = [p.value for p in permissions]
                self.logger.warning(
                    "Permission denied - none of required permissions",
                    username=current_user.username,
                    required_permissions=permission_values,
                    user_permissions=[p.value for p in current_user.permissions],
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permission_values)}"
                )
            
            return current_user
        
        return _require_any_permission
    
    def require_role(self, role: Role) -> Callable:
        """FastAPI dependency that requires specific role."""
        async def _require_role(
            request: Request,
            current_user: User = Depends(self.require_auth())
        ) -> User:
            if current_user.role != role:
                self.logger.warning(
                    "Role access denied",
                    username=current_user.username,
                    user_role=current_user.role.value,
                    required_role=role.value,
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role.value}"
                )
            
            return current_user
        
        return _require_role
    
    def require_any_role(self, roles: List[Role]) -> Callable:
        """FastAPI dependency that requires any of the specified roles."""
        async def _require_any_role(
            request: Request,
            current_user: User = Depends(self.require_auth())
        ) -> User:
            if current_user.role not in roles:
                role_values = [r.value for r in roles]
                self.logger.warning(
                    "Role access denied - none of required roles",
                    username=current_user.username,
                    user_role=current_user.role.value,
                    required_roles=role_values,
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: {', '.join(role_values)}"
                )
            
            return current_user
        
        return _require_any_role
    
    def require_entity_access(self, entity_param: str = "entity") -> Callable:
        """FastAPI dependency that requires access to specific entity."""
        async def _require_entity_access(
            request: Request,
            current_user: User = Depends(self.require_auth())
        ) -> User:
            # Get entity from path parameters or query parameters
            entity_id = None
            
            # Try path parameters first
            if hasattr(request, 'path_params') and entity_param in request.path_params:
                entity_id = request.path_params[entity_param]
            
            # Try query parameters
            elif entity_param in request.query_params:
                entity_id = request.query_params[entity_param]
            
            # Try request body (for POST/PUT requests)
            elif request.method in ["POST", "PUT"]:
                try:
                    body = await request.json()
                    entity_id = body.get(entity_param)
                except (ValueError, TypeError, KeyError):
                    pass  # No JSON body or entity param not in body
            
            # If entity_id is found, check access
            if entity_id and not current_user.can_access_entity(entity_id):
                self.logger.warning(
                    "Entity access denied",
                    username=current_user.username,
                    entity_id=entity_id,
                    user_entities=current_user.entity_access,
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to entity: {entity_id}"
                )
            
            return current_user
        
        return _require_entity_access
    
    def require_payment_approval_permission(self) -> Callable:
        """FastAPI dependency for payment approval based on amount."""
        async def _require_payment_approval(
            request: Request,
            current_user: User = Depends(self.require_auth())
        ) -> User:
            # Get amount from request
            amount = 0
            
            # Try query parameters
            if "amount" in request.query_params:
                try:
                    amount = float(request.query_params["amount"])
                except (ValueError, TypeError):
                    amount = 0
            
            # Try request body for POST/PUT
            elif request.method in ["POST", "PUT"]:
                try:
                    body = await request.json()
                    amount = float(body.get("amount", 0))
                except (ValueError, TypeError, KeyError):
                    amount = 0
            
            # Check approval permission based on amount
            if not current_user.can_approve_payment(amount):
                self.logger.warning(
                    "Payment approval permission denied",
                    username=current_user.username,
                    amount=amount,
                    user_permissions=[p.value for p in current_user.permissions],
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permission to approve payment of ${amount:,.2f}"
                )
            
            return current_user
        
        return _require_payment_approval


# Convenience functions for common permission checks
def require_view_permissions() -> Callable:
    """Require basic view permissions."""
    auth = AuthMiddleware(None)  # Will be injected properly
    return auth.require_any_permission([
        Permission.VIEW_BALANCES,
        Permission.VIEW_TRANSACTIONS,
        Permission.VIEW_KPI
    ])


def require_treasury_role() -> Callable:
    """Require treasury-related roles."""
    auth = AuthMiddleware(None)  # Will be injected properly
    return auth.require_any_role([
        Role.TREASURY_ANALYST,
        Role.TREASURY_MANAGER,
        Role.CFO
    ])


def require_admin_role() -> Callable:
    """Require administrative roles."""
    auth = AuthMiddleware(None)  # Will be injected properly
    return auth.require_any_role([
        Role.CFO,
        Role.TREASURY_MANAGER
    ])