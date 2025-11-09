"""
Treasury Service Configuration Module

Handles environment-specific configuration loading with proper enterprise patterns.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Centralized configuration management for treasury service."""
    
    def __init__(self, environment: str = "local"):
        self.environment = environment
        self.config_root = Path(__file__).parent.parent.parent.parent / "config"
        self._config_cache: Dict[str, Any] = {}
    
    def load_database_config(self) -> Dict[str, Any]:
        """Load database configuration for current environment."""
        config_file = self.config_root / self.environment / "database.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        
        # Fallback to environment variables
        return {
            "database": {
                "host": os.getenv("DATABASE_HOST", "localhost"),
                "port": int(os.getenv("DATABASE_PORT", "5432")),
                "name": os.getenv("DATABASE_NAME", "treasury_local"),
                "username": os.getenv("DATABASE_USERNAME", "treasury_user"),
                "password": os.getenv("DATABASE_PASSWORD", "password"),
                "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
                "ssl_mode": os.getenv("DATABASE_SSL_MODE", "disabled")
            }
        }
    
    def load_service_config(self) -> Dict[str, Any]:
        """Load service-specific configuration."""
        return {
            "service": {
                "name": "treasury-service",
                "version": "1.0.0",
                "port": int(os.getenv("SERVICE_PORT", "8000")),
                "host": os.getenv("SERVICE_HOST", "0.0.0.0"),
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "INFO")
            }
        }
    
    def get_config(self, section: str) -> Dict[str, Any]:
        """Get configuration section with caching."""
        if section not in self._config_cache:
            if section == "database":
                self._config_cache[section] = self.load_database_config()
            elif section == "service":
                self._config_cache[section] = self.load_service_config()
            else:
                self._config_cache[section] = {}
        
        return self._config_cache[section]


# Global configuration instance
config_manager = ConfigManager(
    environment=os.getenv("TREASURY_ENV", "local")
)