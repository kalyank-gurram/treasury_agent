"""Authentication API schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from ..domain.entities.user import Role


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserInfo"


class UserInfo(BaseModel):
    """User information schema."""
    user_id: str
    username: str
    email: str
    full_name: str
    role: Role
    entity_access: List[str]
    permissions: List[str]
    is_active: bool
    last_login: Optional[datetime]


class SessionInfo(BaseModel):
    """Session information schema."""
    session_id: str
    username: str
    role: Role
    login_time: datetime
    expires_at: datetime
    ip_address: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class CreateUserRequest(BaseModel):
    """Create user request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    role: Role
    entity_access: List[str] = Field(default_factory=list)


class UserListResponse(BaseModel):
    """User list response schema."""
    users: List[UserInfo]
    total_count: int


class LoginAttemptInfo(BaseModel):
    """Login attempt information."""
    attempt_id: str
    username: str
    ip_address: str
    success: bool
    failure_reason: Optional[str]
    attempted_at: datetime


class SecurityStatsResponse(BaseModel):
    """Security statistics response."""
    active_sessions: int
    total_users: int
    recent_login_attempts: int
    failed_login_attempts: int
    locked_users: int


class LogoutResponse(BaseModel):
    """Logout response schema."""
    message: str
    logged_out_sessions: int = 1


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Update forward reference
LoginResponse.model_rebuild()