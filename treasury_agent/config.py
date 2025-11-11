import os
from typing import Dict, Any


class Config:
    """Configuration management for Treasury Agent"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "local")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent-specific configuration"""
        return {
            "max_retries": 3,
            "timeout_seconds": 30,
            "enable_logging": True
        }
        
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""  
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "treasury")
        }


config = Config()