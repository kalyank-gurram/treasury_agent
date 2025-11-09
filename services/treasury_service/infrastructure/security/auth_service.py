"""Authentication service with JWT and session management."""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
import jwt
import bcrypt

from ...domain.entities.user import User, UserSession, LoginAttempt, Role
from ...domain.services.security_service import RolePermissionService
from ..observability import get_observability_manager


class AuthenticationService:
    """Handle user authentication, session management, and JWT tokens."""
    
    def __init__(self, jwt_secret: str, session_duration_minutes: int = 30):
        self.jwt_secret = jwt_secret
        self.session_duration = session_duration_minutes
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("security.auth")
        
        # In-memory storage for demo - replace with proper database
        self._users_db: Dict[str, User] = {}
        self._sessions: Dict[str, UserSession] = {}
        self._login_attempts: List[LoginAttempt] = []
        
        # Initialize demo users
        self._init_demo_users()
    
    def _init_demo_users(self) -> None:
        """Initialize demo users for testing."""
        demo_users = [
            {
                "user_id": "ENT-01",
                "username": "analyst",
                "email": "analyst@treasury.com",
                "full_name": "Treasury Analyst",
                "role": Role.TREASURY_ANALYST,
                "entity_access": ["ENT-01"],
                "password": "demo123"
            },
            {
                "user_id": "ENT-02",
                "username": "manager", 
                "email": "manager@treasury.com",
                "full_name": "Treasury Manager",
                "role": Role.TREASURY_MANAGER,
                "entity_access": ["ENT-01", "ENT-02", "ENT-03"],
                "password": "demo123"
            },
            {
                "user_id": "ENT-03",
                "username": "cfo",
                "email": "cfo@treasury.com", 
                "full_name": "Chief Financial Officer",
                "role": Role.CFO,
                "entity_access": ["ALL"],  # CFO has access to all entities
                "password": "demo123"
            },
            {
                "user_id": "ENT-04",
                "username": "approver",
                "email": "approver@treasury.com",
                "full_name": "Payment Approver",
                "role": Role.PAYMENT_APPROVER,
                "entity_access": ["ENT-01", "ENT-02"],
                "password": "demo123"
            },
            {
                "user_id": "ENT-05",
                "username": "auditor",
                "email": "auditor@treasury.com",
                "full_name": "Treasury Auditor", 
                "role": Role.AUDITOR,
                "entity_access": ["ALL"],  # Auditor has read access to all entities
                "password": "demo123"
            },
            {
                "user_id": "ENT-06",
                "username": "viewer",
                "email": "viewer@treasury.com",
                "full_name": "Treasury Viewer",
                "role": Role.VIEWER,
                "entity_access": ["ENT-01"],
                "password": "demo123"
            }
        ]
        
        for user_data in demo_users:
            password = user_data.pop("password")
            password_hash = self._hash_password(password)
            
            user = RolePermissionService.create_user_with_role(
                password_hash=password_hash,
                **user_data
            )
            
            self._users_db[user.username] = user
        
        self.logger.info("Demo users initialized", user_count=len(self._users_db))
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_session_id(self, user: User, ip_address: str) -> str:
        """Generate unique session ID."""
        data = f"{user.user_id}:{user.username}:{ip_address}:{datetime.now(timezone.utc)}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _log_login_attempt(self, username: str, ip_address: str, user_agent: str, 
                          success: bool, failure_reason: str = None) -> None:
        """Log login attempt for security monitoring."""
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        self._login_attempts.append(attempt)
        
        # Log to observability system
        if success:
            self.logger.info(
                "Successful login",
                username=username,
                ip_address=ip_address,
                attempt_id=attempt.attempt_id
            )
        else:
            self.logger.warning(
                "Failed login attempt",
                username=username,
                ip_address=ip_address,
                failure_reason=failure_reason,
                attempt_id=attempt.attempt_id
            )
    
    def authenticate(self, username: str, password: str, ip_address: str, 
                    user_agent: str) -> Optional[UserSession]:
        """
        Authenticate user and create session.
        
        Returns UserSession if successful, None if failed.
        """
        # Check if user exists
        user = self._users_db.get(username)
        if not user:
            self._log_login_attempt(username, ip_address, user_agent, False, "User not found")
            return None
        
        # Check if user is active
        if not user.is_active:
            self._log_login_attempt(username, ip_address, user_agent, False, "User inactive")
            return None
        
        # Check if user is locked
        if user.is_locked():
            self._log_login_attempt(username, ip_address, user_agent, False, "User locked")
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.increment_failed_login()
            self._log_login_attempt(username, ip_address, user_agent, False, "Invalid password")
            return None
        
        # Authentication successful
        user.update_last_login()
        
        # Create session
        session_id = self._generate_session_id(user, ip_address)
        session = UserSession(
            session_id=session_id,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            permissions=user.permissions,
            entity_access=user.entity_access,
            login_time=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.session_duration),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store session
        self._sessions[session_id] = session
        
        # Log successful authentication
        self._log_login_attempt(username, ip_address, user_agent, True)
        
        # Record metrics
        self.observability.record_metric(
            "counter", "auth_success_total", 1,
            {"username": username, "role": user.role.value}
        )
        
        return session
    
    def validate_session(self, session_id: str) -> Optional[UserSession]:
        """Validate and return active session."""
        session = self._sessions.get(session_id)
        
        if not session:
            return None
        
        if session.is_expired() or not session.is_active:
            # Clean up expired session
            self._sessions.pop(session_id, None)
            return None
        
        # Extend session on activity
        session.extend_session(self.session_duration)
        
        return session
    
    def logout(self, session_id: str) -> bool:
        """Logout user and invalidate session."""
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            self._sessions.pop(session_id, None)
            
            self.logger.info(
                "User logged out",
                username=session.username,
                session_id=session_id
            )
            
            return True
        return False
    
    def logout_all_sessions(self, username: str) -> int:
        """Logout all sessions for a user."""
        logout_count = 0
        sessions_to_remove = []
        
        for session_id, session in self._sessions.items():
            if session.username == username:
                session.is_active = False
                sessions_to_remove.append(session_id)
                logout_count += 1
        
        for session_id in sessions_to_remove:
            self._sessions.pop(session_id, None)
        
        if logout_count > 0:
            self.logger.info(
                "All sessions logged out",
                username=username,
                session_count=logout_count
            )
        
        return logout_count
    
    def generate_jwt_token(self, session: UserSession) -> str:
        """Generate JWT token for API access."""
        payload = session.to_jwt_payload()
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Check if session is still valid
            session_id = payload.get('session_id')
            if session_id and self.validate_session(session_id):
                return payload
            
            return None
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid JWT token")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self._users_db.get(username)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        for user in self._users_db.values():
            if str(user.user_id) == user_id:
                return user
        return None
    
    def create_user(self, username: str, email: str, full_name: str, 
                   password: str, role: Role, entity_access: List[str]) -> User:
        """Create new user with hashed password."""
        if username in self._users_db:
            raise ValueError(f"User {username} already exists")
        
        password_hash = self._hash_password(password)
        user_id = f"user_{len(self._users_db) + 1:03d}"
        
        user = RolePermissionService.create_user_with_role(
            user_id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            entity_access=entity_access,
            password_hash=password_hash
        )
        
        self._users_db[username] = user
        
        self.logger.info(
            "User created",
            username=username,
            role=role.value,
            user_id=user_id
        )
        
        return user
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = self._users_db.get(username)
        if not user:
            return False
        
        # Verify old password
        if not self._verify_password(old_password, user.password_hash):
            return False
        
        # Update password
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        
        # Logout all existing sessions
        self.logout_all_sessions(username)
        
        self.logger.info("Password changed", username=username)
        return True
    
    def get_active_sessions(self) -> List[UserSession]:
        """Get all active sessions."""
        active_sessions = []
        for session in self._sessions.values():
            if session.is_active and not session.is_expired():
                active_sessions.append(session)
        return active_sessions
    
    def get_login_attempts(self, username: str = None, 
                          hours: int = 24) -> List[LoginAttempt]:
        """Get login attempts within specified hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        attempts = [
            attempt for attempt in self._login_attempts
            if attempt.attempted_at > cutoff_time
        ]
        
        if username:
            attempts = [
                attempt for attempt in attempts
                if attempt.username == username
            ]
        
        return sorted(attempts, key=lambda x: x.attempted_at, reverse=True)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count removed."""
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._sessions.pop(session_id, None)
        
        if expired_sessions:
            self.logger.info("Cleaned up expired sessions", count=len(expired_sessions))
        
        return len(expired_sessions)