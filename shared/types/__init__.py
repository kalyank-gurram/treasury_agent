"""
Shared Types for Treasury Enterprise Workspace

Common type definitions used across services and applications.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# Treasury Domain Types
class TransactionType(Enum):
    """Transaction type enumeration."""
    PAYMENT = "payment"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    FOREX = "forex"
    INVESTMENT = "investment"


class TransactionStatus(Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Transaction:
    """Treasury transaction data model."""
    id: str
    type: TransactionType
    status: TransactionStatus
    amount: float
    currency: str
    description: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


# Service Communication Types
@dataclass
class ServiceResponse:
    """Standard service response format."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class APIError:
    """API error response format."""
    code: int
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


# Configuration Types
@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    name: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    ssl_mode: str = "disabled"


@dataclass
class ServiceConfig:
    """Service configuration."""
    name: str
    version: str
    port: int
    host: str = "0.0.0.0"
    debug: bool = False
    log_level: str = "INFO"


# Analytics Types
@dataclass
class PerformanceMetric:
    """Performance metric data."""
    name: str
    value: Union[int, float]
    unit: str
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None


@dataclass
class Alert:
    """System alert data."""
    id: str
    severity: str
    message: str
    component: str
    timestamp: datetime
    resolved: bool = False
    metadata: Optional[Dict[str, Any]] = None


# Export commonly used types
__all__ = [
    "Transaction",
    "TransactionType", 
    "TransactionStatus",
    "ServiceResponse",
    "APIError",
    "DatabaseConfig",
    "ServiceConfig",
    "PerformanceMetric",
    "Alert"
]