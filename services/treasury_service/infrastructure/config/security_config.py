"""Security configuration for authentication and authorization."""

from pydantic import BaseModel, Field
from typing import List


class SecurityConfig(BaseModel):
    """Security-related configuration."""
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        default="treasury-agent-jwt-secret-change-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    
    # Session Configuration  
    session_duration_minutes: int = Field(
        default=30, 
        description="Session timeout in minutes"
    )
    
    # Login Security
    max_login_attempts: int = Field(
        default=5, 
        description="Maximum failed login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=15, 
        description="Account lockout duration in minutes"
    )
    
    # Password Policy
    min_password_length: int = Field(
        default=8, 
        description="Minimum password length"
    )
    require_password_complexity: bool = Field(
        default=False, 
        description="Require complex passwords (uppercase, lowercase, numbers, symbols)"
    )
    
    # API Security
    require_https: bool = Field(
        default=False, 
        description="Require HTTPS for all requests (enable in production)"
    )
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:7861",
            "http://localhost:7861"
        ],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    enable_rate_limiting: bool = Field(
        default=True, 
        description="Enable API rate limiting"
    )
    rate_limit_requests_per_minute: int = Field(
        default=100, 
        description="API requests per minute per user"
    )
    
    # Audit & Monitoring
    log_login_attempts: bool = Field(
        default=True, 
        description="Log all login attempts"
    )
    log_api_access: bool = Field(
        default=True, 
        description="Log API access with user context"
    )
    
    # Demo Mode Settings
    enable_demo_users: bool = Field(
        default=True, 
        description="Enable demo users for testing (disable in production)"
    )
    demo_password: str = Field(
        default="demo123", 
        description="Default password for demo users"
    )