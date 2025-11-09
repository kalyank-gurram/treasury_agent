"""Advanced configuration management with validation and environment support."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
import json
import yaml

T = TypeVar('T')


class Environment(str, Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(default="treasury_agent", description="Database name")
    username: str = Field(default="treasury", description="Database username")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max connection overflow")
    
    @property
    def connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_prefix = "DB_"


class LLMConfig(BaseSettings):
    """LLM configuration."""
    
    # Use exact field names from .env file (no prefix)
    model_provider: str = Field(default="openai", description="LLM provider")
    primary_model: str = Field(default="gpt-4o-mini", description="Primary model")
    cheap_model: str = Field(default="gpt-4o-mini", description="Cheap model")
    anthropic_primary: str = Field(default="claude-3-5-sonnet-latest", description="Anthropic primary model")
    anthropic_cheap: str = Field(default="claude-3-5-haiku-latest", description="Anthropic cheap model")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retries")
    
    @validator('model_provider')
    def validate_provider(cls, v):
        """Validate LLM provider."""
        allowed = ["openai", "anthropic", "hybrid"]
        if v not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v
    
    class Config:
        env_prefix = ""  # No prefix - use exact field names


class EventBusConfig(BaseSettings):
    """Event bus configuration."""
    
    enabled: bool = Field(default=True, description="Enable event bus")
    store_type: str = Field(default="memory", description="Event store type")
    batch_size: int = Field(default=100, description="Event processing batch size")
    retry_attempts: int = Field(default=3, description="Event handler retry attempts")
    retry_delay: float = Field(default=1.0, description="Retry delay in seconds")
    
    class Config:
        env_prefix = "EVENT_"


class SecurityConfig(BaseSettings):
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
    cors_origins: List[str] = Field(
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
    
    @validator('jwt_secret_key')
    def validate_secret_key(cls, v, values):
        """Validate secret key in production."""
        env = values.get('environment', Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION and v == "treasury-agent-jwt-secret-change-in-production":
            raise ValueError("Must set custom JWT secret key in production")
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class ObservabilityConfig(BaseSettings):
    """Observability configuration."""
    
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    metrics_enabled: bool = Field(default=True, description="Enable metrics")
    tracing_enabled: bool = Field(default=False, description="Enable distributed tracing")
    tracing_endpoint: Optional[str] = Field(default=None, description="Tracing endpoint")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    class Config:
        env_prefix = "OBSERVABILITY_"


class PluginConfig(BaseSettings):
    """Plugin system configuration."""
    
    enabled: bool = Field(default=True, description="Enable plugin system")
    discovery_paths: List[str] = Field(default=["treasury_agent/plugins"], description="Plugin discovery paths")
    auto_load: bool = Field(default=True, description="Auto-load discovered plugins")
    plugin_timeout: int = Field(default=30, description="Plugin operation timeout")
    
    class Config:
        env_prefix = "PLUGIN_"


class TreasuryAgentConfig(BaseSettings):
    """Main Treasury Agent configuration."""
    
    # Core settings
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    event_bus: EventBusConfig = Field(default_factory=EventBusConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    
    # Data generation settings
    mock_data_days: int = Field(default=180, description="Days of mock data to generate")
    mock_accounts_per_entity: int = Field(default=5, description="Mock accounts per entity")
    mock_entities_count: int = Field(default=10, description="Number of mock entities")
    
    @validator('debug')
    def validate_debug(cls, v, values):
        """Validate debug mode."""
        env = values.get('environment', Environment.DEVELOPMENT)
        if env == Environment.PRODUCTION and v:
            raise ValueError("Debug mode should not be enabled in production")
        return v
    
    @validator('workers')
    def validate_workers(cls, v):
        """Validate worker count."""
        if v < 1:
            raise ValueError("Worker count must be at least 1")
        return v
    
    # Configuration for pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env
    )


# Configuration utilities (simplified for compatibility)
def load_yaml_config() -> Dict[str, Any]:
    """Load settings from YAML file."""
    yaml_file = os.getenv("CONFIG_YAML_FILE", "config.yaml")
    if not os.path.exists(yaml_file):
        return {}
    
    try:
        with open(yaml_file, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def load_json_config() -> Dict[str, Any]:
    """Load settings from JSON file."""
    json_file = os.getenv("CONFIG_JSON_FILE", "config.json")
    if not os.path.exists(json_file):
        return {}
    
    try:
        with open(json_file, "r") as f:
            return json.load(f)
    except Exception:
        return {}


class ConfigurationManager:
    """Configuration manager with hot-reload capability."""
    
    def __init__(self, config_class: Type[T] = TreasuryAgentConfig):
        self._config_class = config_class
        self._config: Optional[T] = None
        self._watchers: List[callable] = []
    
    def load_config(self) -> T:
        """Load configuration."""
        if self._config is None:
            self._config = self._config_class()
        return self._config
    
    def reload_config(self) -> T:
        """Reload configuration."""
        self._config = self._config_class()
        self._notify_watchers()
        return self._config
    
    def add_watcher(self, callback: callable) -> None:
        """Add configuration change watcher."""
        self._watchers.append(callback)
    
    def _notify_watchers(self) -> None:
        """Notify configuration watchers."""
        for watcher in self._watchers:
            try:
                watcher(self._config)
            except Exception as e:
                # Log error but don't fail
                print(f"Configuration watcher error: {e}")
    
    def get_environment_config(self, env: Environment) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        config_map = {
            Environment.DEVELOPMENT: {
                "debug": True,
                "log_level": LogLevel.DEBUG,
                "database": {"database": "treasury_dev"},
                "cors_origins": ["*"]
            },
            Environment.TESTING: {
                "debug": True,
                "log_level": LogLevel.WARNING,
                "database": {"database": "treasury_test"},
                "event_bus": {"enabled": False}
            },
            Environment.STAGING: {
                "debug": False,
                "log_level": LogLevel.INFO,
                "database": {"database": "treasury_staging"},
                "workers": 2
            },
            Environment.PRODUCTION: {
                "debug": False,
                "log_level": LogLevel.WARNING,
                "database": {"pool_size": 20, "max_overflow": 40},
                "workers": 4,
                "security": {"cors_origins": []}
            }
        }
        
        return config_map.get(env, {})
    
    def export_config(self, format_type: str = "json") -> str:
        """Export current configuration."""
        config = self.load_config()
        
        if format_type.lower() == "json":
            return config.json(indent=2)
        elif format_type.lower() == "yaml":
            import yaml
            return yaml.dump(config.dict(), default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Global configuration manager
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_config() -> TreasuryAgentConfig:
    """Get current configuration."""
    return get_config_manager().load_config()