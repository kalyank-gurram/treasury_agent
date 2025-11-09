"""Authentication and user management API endpoints."""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Request, HTTPException, Depends, Response, status
from fastapi.security import HTTPBearer

from ..schemas.auth import (
    LoginRequest, LoginResponse, UserInfo, SessionInfo, ChangePasswordRequest,
    CreateUserRequest, UserListResponse, LoginAttemptInfo, SecurityStatsResponse,
    LogoutResponse, ErrorResponse
)
from ..domain.entities.user import User, Permission, Role
from ..infrastructure.security.auth_service import AuthenticationService
from ..infrastructure.security.auth_middleware import AuthMiddleware
from ..infrastructure.observability import get_observability_manager


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_auth_service(request: Request) -> AuthenticationService:
    """Get authentication service from DI container."""
    container = request.app.state.container
    return container.get(AuthenticationService)


def get_auth_middleware(request: Request) -> AuthMiddleware:
    """Get auth middleware from DI container."""
    container = request.app.state.container
    return container.get(AuthMiddleware)


async def get_current_user(request: Request) -> User:
    """Dependency to get current authenticated user."""
    auth_middleware = get_auth_middleware(request)
    require_auth_dependency = auth_middleware.require_auth()
    return await require_auth_dependency(request)


async def require_admin(request: Request) -> User:
    """Dependency to require admin permissions."""
    auth_middleware = get_auth_middleware(request)
    require_permission_dependency = auth_middleware.require_permission(Permission.MANAGE_USERS)
    return await require_permission_dependency(request)


async def require_audit_access(request: Request) -> User:
    """Dependency to require audit access."""
    auth_middleware = get_auth_middleware(request)
    require_permission_dependency = auth_middleware.require_permission(Permission.VIEW_SYSTEM_LOGS)
    return await require_permission_dependency(request)


async def require_system_config(request: Request) -> User:
    """Dependency to require system configuration permissions."""
    auth_middleware = get_auth_middleware(request)
    require_permission_dependency = auth_middleware.require_permission(Permission.SYSTEM_CONFIG)
    return await require_permission_dependency(request)


@router.post("/login", response_model=LoginResponse)
def login(
    login_req: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT token.
    
    Creates both a session (stored server-side) and JWT token for API access.
    """
    observability = get_observability_manager()
    logger = observability.get_logger("api.auth")
    
    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    logger.info(
        "Login attempt",
        username=login_req.username,
        ip_address=ip_address
    )
    
    # Authenticate user
    session = auth_service.authenticate(
        username=login_req.username,
        password=login_req.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not session:
        logger.warning(
            "Login failed",
            username=login_req.username,
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate JWT token
    jwt_token = auth_service.generate_jwt_token(session)
    
    # Set session cookie (for web interface)
    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 60  # 30 minutes
    )
    
    # Get user info
    user = auth_service.get_user_by_username(session.username)
    user_info = UserInfo(
        user_id=str(user.user_id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        entity_access=user.entity_access,
        permissions=[p.value for p in user.permissions],
        is_active=user.is_active,
        last_login=user.last_login
    )
    
    logger.info(
        "Login successful",
        username=user.username,
        role=user.role.value,
        session_id=session.session_id
    )
    
    return LoginResponse(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes
        user=user_info
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user and invalidate session.
    """
    observability = get_observability_manager()
    logger = observability.get_logger("api.auth")
    
    # Get session ID from cookie or JWT
    session_id = request.cookies.get("session_id")
    logout_count = 0
    
    if session_id:
        # Logout session-based auth
        if auth_service.logout(session_id):
            logout_count = 1
    else:
        # For JWT-only auth, logout all user sessions
        logout_count = auth_service.logout_all_sessions(current_user.username)
    
    # Clear session cookie
    response.delete_cookie("session_id")
    
    logger.info(
        "User logged out",
        username=current_user.username,
        session_count=logout_count
    )
    
    return LogoutResponse(
        message="Successfully logged out",
        logged_out_sessions=logout_count
    )


@router.get("/me", response_model=UserInfo)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserInfo(
        user_id=str(current_user.user_id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        entity_access=current_user.entity_access,
        permissions=[p.value for p in current_user.permissions],
        is_active=current_user.is_active,
        last_login=current_user.last_login
    )


@router.get("/sessions", response_model=List[SessionInfo])
def get_active_sessions(
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """Get all active sessions (admin only)."""
    sessions = auth_service.get_active_sessions()
    
    return [
        SessionInfo(
            session_id=session.session_id,
            username=session.username,
            role=session.role,
            login_time=session.login_time,
            expires_at=session.expires_at,
            ip_address=session.ip_address
        )
        for session in sessions
    ]


@router.post("/change-password", response_model=dict)
def change_password(
    password_req: ChangePasswordRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """Change current user's password."""
    success = auth_service.change_password(
        username=current_user.username,
        old_password=password_req.old_password,
        new_password=password_req.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/users", response_model=UserInfo)
def create_user(
    user_req: CreateUserRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """Create new user (admin only)."""
    try:
        user = auth_service.create_user(
            username=user_req.username,
            email=user_req.email,
            full_name=user_req.full_name,
            password=user_req.password,
            role=user_req.role,
            entity_access=user_req.entity_access or ["ENT-01"]
        )
        
        return UserInfo(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            entity_access=user.entity_access,
            permissions=[p.value for p in user.permissions],
            is_active=user.is_active,
            last_login=user.last_login
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users", response_model=UserListResponse)
def list_users(
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only)."""
    # This is a simplified implementation - in production, you'd want proper user repository
    users_data = []
    user_count = 0
    
    # Access internal users for demo - replace with proper repository in production
    for username, user in auth_service._users_db.items():
        user_count += 1
        users_data.append(UserInfo(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            entity_access=user.entity_access,
            permissions=[p.value for p in user.permissions],
            is_active=user.is_active,
            last_login=user.last_login
        ))
    
    return UserListResponse(
        users=users_data,
        total_count=user_count
    )


@router.get("/login-attempts", response_model=List[LoginAttemptInfo])
def get_login_attempts(
    username: str = None,
    hours: int = 24,
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(require_audit_access)
):
    """Get login attempts (admin/auditor only)."""
    attempts = auth_service.get_login_attempts(username, hours)
    
    return [
        LoginAttemptInfo(
            attempt_id=attempt.attempt_id,
            username=attempt.username,
            ip_address=attempt.ip_address,
            success=attempt.success,
            failure_reason=attempt.failure_reason,
            attempted_at=attempt.attempted_at
        )
        for attempt in attempts
    ]


@router.get("/security-stats", response_model=SecurityStatsResponse)
def get_security_stats(
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(require_audit_access)
):
    """Get security statistics (admin/auditor only)."""
    active_sessions = len(auth_service.get_active_sessions())
    total_users = len(auth_service._users_db)  # Replace with proper repository
    
    # Get recent login attempts
    recent_attempts = auth_service.get_login_attempts(hours=24)
    recent_count = len(recent_attempts)
    failed_count = len([a for a in recent_attempts if not a.success])
    
    # Count locked users
    locked_count = len([u for u in auth_service._users_db.values() if u.is_locked()])
    
    return SecurityStatsResponse(
        active_sessions=active_sessions,
        total_users=total_users,
        recent_login_attempts=recent_count,
        failed_login_attempts=failed_count,
        locked_users=locked_count
    )


@router.post("/cleanup-sessions", response_model=dict)
def cleanup_expired_sessions(
    auth_service: AuthenticationService = Depends(get_auth_service),
    current_user: User = Depends(require_system_config)
):
    """Clean up expired sessions (admin only)."""
    cleaned_count = auth_service.cleanup_expired_sessions()
    
    return {
        "message": f"Cleaned up {cleaned_count} expired sessions",
        "cleaned_sessions": cleaned_count
    }