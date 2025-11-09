"""JWT-based authentication system for treasury management."""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import bcrypt
from ..observability import get_observability_manager


class UserRole(Enum):
    """User roles in the treasury system."""
    SUPER_ADMIN = "super_admin"
    TREASURER = "treasurer"
    SENIOR_ANALYST = "senior_analyst"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class Permission(Enum):
    """System permissions for fine-grained access control."""
    # Cash Management
    CASH_READ = "cash:read"
    CASH_WRITE = "cash:write"
    CASH_ADMIN = "cash:admin"
    
    # Payments
    PAYMENT_VIEW = "payment:view"
    PAYMENT_INITIATE = "payment:initiate"
    PAYMENT_APPROVE = "payment:approve"
    PAYMENT_ADMIN = "payment:admin"
    
    # Investments
    INVESTMENT_VIEW = "investment:view"
    INVESTMENT_ANALYZE = "investment:analyze"
    INVESTMENT_EXECUTE = "investment:execute"
    INVESTMENT_ADMIN = "investment:admin"
    
    # Risk Management
    RISK_VIEW = "risk:view"
    RISK_ASSESS = "risk:assess"
    RISK_MANAGE = "risk:manage"
    RISK_ADMIN = "risk:admin"
    
    # Collections
    COLLECTIONS_VIEW = "collections:view"
    COLLECTIONS_MANAGE = "collections:manage"
    COLLECTIONS_ADMIN = "collections:admin"
    
    # Compliance
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_AUDIT = "compliance:audit"
    COMPLIANCE_ADMIN = "compliance:admin"
    
    # System Administration
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_ADMIN = "system:admin"


@dataclass
class User:
    """User representation in the system."""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: List[Permission]
    is_active: bool = True
    is_mfa_enabled: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None
    mfa_secret: Optional[str] = None


@dataclass
class AuthToken:
    """Authentication token representation."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1 hour
    scope: List[str] = field(default_factory=list)


@dataclass
class AuthSession:
    """User session information."""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True


class TokenManager:
    """Manages JWT tokens for authentication and authorization."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.token_manager")
        
        # Token configuration
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30    # 30 days
        
    def create_access_token(self, user: User, additional_claims: Dict[str, Any] = None) -> str:
        """Create a JWT access token for the user."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [perm.value for perm in user.permissions],
            "iat": now,
            "exp": expire,
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
            
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info(f"Access token created for user {user.username}",
                        user_id=user.user_id, expires_at=expire.isoformat())
        
        return token
        
    def create_refresh_token(self, user: User) -> str:
        """Create a JWT refresh token for the user."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user.user_id,
            "iat": now,
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token identifier
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info(f"Refresh token created for user {user.username}",
                        user_id=user.user_id, expires_at=expire.isoformat())
        
        return token
        
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token has expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise jwt.ExpiredSignatureError("Token has expired")
                
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token verification failed: expired token")
            raise
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Token verification failed: {e}")
            raise
            
    def refresh_access_token(self, refresh_token: str, user: User) -> str:
        """Create a new access token using a valid refresh token."""
        try:
            payload = self.verify_token(refresh_token)
            
            # Verify it's a refresh token and belongs to the user
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Invalid token type")
                
            if payload.get("sub") != user.user_id:
                raise jwt.InvalidTokenError("Token does not belong to user")
                
            # Create new access token
            return self.create_access_token(user)
            
        except jwt.InvalidTokenError:
            self.logger.warning(f"Refresh token validation failed for user {user.user_id}")
            raise


class AuthenticationService:
    """Main authentication service for the treasury system."""
    
    def __init__(self, secret_key: str):
        self.token_manager = TokenManager(secret_key)
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.authentication")
        
        # User storage (in production, this would be a database)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, AuthSession] = {}
        
        # Role-based permissions mapping
        self.role_permissions = self._init_role_permissions()
        
        # Create default admin user
        self._create_default_admin()
        
    def _init_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-based permissions mapping."""
        return {
            UserRole.SUPER_ADMIN: list(Permission),  # All permissions
            
            UserRole.TREASURER: [
                Permission.CASH_READ, Permission.CASH_WRITE, Permission.CASH_ADMIN,
                Permission.PAYMENT_VIEW, Permission.PAYMENT_INITIATE, Permission.PAYMENT_APPROVE,
                Permission.INVESTMENT_VIEW, Permission.INVESTMENT_ANALYZE, Permission.INVESTMENT_EXECUTE,
                Permission.RISK_VIEW, Permission.RISK_ASSESS, Permission.RISK_MANAGE,
                Permission.COLLECTIONS_VIEW, Permission.COLLECTIONS_MANAGE,
                Permission.COMPLIANCE_VIEW, Permission.COMPLIANCE_AUDIT,
                Permission.USER_VIEW
            ],
            
            UserRole.SENIOR_ANALYST: [
                Permission.CASH_READ, Permission.CASH_WRITE,
                Permission.PAYMENT_VIEW, Permission.PAYMENT_INITIATE,
                Permission.INVESTMENT_VIEW, Permission.INVESTMENT_ANALYZE,
                Permission.RISK_VIEW, Permission.RISK_ASSESS,
                Permission.COLLECTIONS_VIEW, Permission.COLLECTIONS_MANAGE,
                Permission.COMPLIANCE_VIEW
            ],
            
            UserRole.ANALYST: [
                Permission.CASH_READ,
                Permission.PAYMENT_VIEW,
                Permission.INVESTMENT_VIEW,
                Permission.RISK_VIEW,
                Permission.COLLECTIONS_VIEW,
                Permission.COMPLIANCE_VIEW
            ],
            
            UserRole.AUDITOR: [
                Permission.CASH_READ,
                Permission.PAYMENT_VIEW,
                Permission.INVESTMENT_VIEW,
                Permission.RISK_VIEW,
                Permission.COLLECTIONS_VIEW,
                Permission.COMPLIANCE_VIEW, Permission.COMPLIANCE_AUDIT,
                Permission.USER_VIEW
            ],
            
            UserRole.VIEWER: [
                Permission.CASH_READ,
                Permission.PAYMENT_VIEW,
                Permission.INVESTMENT_VIEW,
                Permission.RISK_VIEW,
                Permission.COLLECTIONS_VIEW,
                Permission.COMPLIANCE_VIEW
            ]
        }
        
    def _create_default_admin(self):
        """Create a default admin user for initial system access."""
        admin_user = User(
            user_id="admin_001",
            username="admin",
            email="admin@treasury.local",
            role=UserRole.SUPER_ADMIN,
            permissions=self.role_permissions[UserRole.SUPER_ADMIN],
            password_hash=self.hash_password("TreasuryAdmin2025!")
        )
        
        self.users[admin_user.user_id] = admin_user
        self.logger.info("Default admin user created", user_id=admin_user.user_id)
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        
    def authenticate_user(self, username: str, password: str, ip_address: str = None,
                         user_agent: str = None) -> Optional[User]:
        """Authenticate a user with username and password."""
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username and u.is_active:
                user = u
                break
                
        if not user:
            self.logger.warning(f"Authentication failed: user not found", username=username)
            return None
            
        # Verify password
        if not self.verify_password(password, user.password_hash):
            self.logger.warning(f"Authentication failed: invalid password", 
                              username=username, user_id=user.user_id)
            return None
            
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        # Create session
        session = self._create_session(user, ip_address, user_agent)
        
        self.logger.info(f"User authenticated successfully", 
                        username=username, user_id=user.user_id, session_id=session.session_id)
        
        return user
        
    def _create_session(self, user: User, ip_address: str = None, 
                       user_agent: str = None) -> AuthSession:
        """Create a new user session."""
        now = datetime.now(timezone.utc)
        session = AuthSession(
            session_id=secrets.token_urlsafe(32),
            user_id=user.user_id,
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown",
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(hours=24)
        )
        
        self.sessions[session.session_id] = session
        return session
        
    def create_auth_token(self, user: User) -> AuthToken:
        """Create authentication tokens for a user."""
        access_token = self.token_manager.create_access_token(user)
        refresh_token = self.token_manager.create_refresh_token(user)
        
        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.token_manager.access_token_expire_minutes * 60,
            scope=[perm.value for perm in user.permissions]
        )
        
    def validate_token(self, token: str) -> Optional[User]:
        """Validate an access token and return the user."""
        try:
            payload = self.token_manager.verify_token(token)
            
            # Get user
            user_id = payload.get("sub")
            user = self.users.get(user_id)
            
            if not user or not user.is_active:
                self.logger.warning("Token validation failed: user not found or inactive",
                                  user_id=user_id)
                return None
                
            return user
            
        except jwt.InvalidTokenError:
            return None
            
    def logout_user(self, session_id: str):
        """Logout a user by deactivating their session."""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            self.logger.info("User logged out", session_id=session_id, user_id=session.user_id)
            
    def create_user(self, username: str, email: str, password: str, role: UserRole) -> User:
        """Create a new user in the system."""
        user_id = f"user_{secrets.token_urlsafe(8)}"
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=self.role_permissions.get(role, []),
            password_hash=self.hash_password(password)
        )
        
        self.users[user_id] = user
        
        self.logger.info("New user created", user_id=user_id, username=username, role=role.value)
        
        return user
        
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get permissions for a specific user."""
        user = self.users.get(user_id)
        return user.permissions if user else []
        
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
        
    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update a user's role and associated permissions."""
        user = self.users.get(user_id)
        if not user:
            return False
            
        old_role = user.role
        user.role = new_role
        user.permissions = self.role_permissions.get(new_role, [])
        
        self.logger.info("User role updated", user_id=user_id, old_role=old_role.value, 
                        new_role=new_role.value)
        
        return True
        
    def get_active_sessions(self, user_id: str = None) -> List[AuthSession]:
        """Get active sessions, optionally filtered by user."""
        sessions = []
        for session in self.sessions.values():
            if session.is_active and (not user_id or session.user_id == user_id):
                if session.expires_at > datetime.now(timezone.utc):
                    sessions.append(session)
                else:
                    # Auto-expire old sessions
                    session.is_active = False
                    
        return sessions