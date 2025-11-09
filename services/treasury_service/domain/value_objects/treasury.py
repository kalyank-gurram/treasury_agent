"""Treasury-specific value objects for strong typing and validation."""

from decimal import Decimal
from typing import Dict, Optional
from enum import Enum

from ..entities.base import ValueObject


class Currency(ValueObject):
    """Currency value object with ISO 4217 support."""
    
    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "CHF"}
    
    def __init__(self, code: str):
        if not isinstance(code, str):
            raise ValueError("Currency code must be a string")
        
        code = code.upper().strip()
        if len(code) != 3:
            raise ValueError("Currency code must be 3 characters")
        
        if code not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {code}")
        
        self._code = code
    
    @property
    def code(self) -> str:
        return self._code
    
    def __str__(self) -> str:
        return self._code
    
    def __repr__(self) -> str:
        return f"Currency('{self._code}')"


class Money(ValueObject):
    """Money value object with currency and amount."""
    
    def __init__(self, amount: Decimal | float | int, currency: Currency | str):
        if isinstance(currency, str):
            currency = Currency(currency)
        
        if not isinstance(currency, Currency):
            raise ValueError("Currency must be Currency instance or string")
        
        self._amount = Decimal(str(amount))
        self._currency = currency
    
    @property
    def amount(self) -> Decimal:
        return self._amount
    
    @property
    def currency(self) -> Currency:
        return self._currency
    
    def add(self, other: "Money") -> "Money":
        """Add two Money objects (same currency)."""
        if self._currency != other._currency:
            raise ValueError(f"Cannot add different currencies: {self._currency} != {other._currency}")
        return Money(self._amount + other._amount, self._currency)
    
    def subtract(self, other: "Money") -> "Money":
        """Subtract two Money objects (same currency)."""
        if self._currency != other._currency:
            raise ValueError(f"Cannot subtract different currencies: {self._currency} != {other._currency}")
        return Money(self._amount - other._amount, self._currency)
    
    def multiply(self, factor: Decimal | float | int) -> "Money":
        """Multiply money by a factor."""
        return Money(self._amount * Decimal(str(factor)), self._currency)
    
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self._amount > 0
    
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self._amount < 0
    
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self._amount == 0
    
    def __str__(self) -> str:
        return f"{self._amount:.2f} {self._currency}"
    
    def __repr__(self) -> str:
        return f"Money({self._amount}, '{self._currency}')"


class EntityId(ValueObject):
    """Strongly-typed entity identifier."""
    
    def __init__(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Entity ID must be a non-empty string")
        
        # Validate format: ENT-XX
        parts = value.strip().split("-")
        if len(parts) != 2 or parts[0] != "ENT" or not parts[1].isdigit():
            raise ValueError("Entity ID must follow format 'ENT-XX' where XX is numeric")
        
        self._value = value.strip()
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __repr__(self) -> str:
        return f"EntityId('{self._value}')"


class AccountId(ValueObject):
    """Strongly-typed account identifier."""
    
    def __init__(self, entity_id: EntityId | str, account_type: str):
        if isinstance(entity_id, str):
            entity_id = EntityId(entity_id)
        
        if not isinstance(account_type, str) or not account_type.strip():
            raise ValueError("Account type must be a non-empty string")
        
        self._entity_id = entity_id
        self._account_type = account_type.strip()
        self._value = f"{entity_id.value}-{self._account_type}"
    
    @property
    def entity_id(self) -> EntityId:
        return self._entity_id
    
    @property
    def account_type(self) -> str:
        return self._account_type
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __repr__(self) -> str:
        return f"AccountId('{self._entity_id}', '{self._account_type}')"


class PaymentId(ValueObject):
    """Strongly-typed payment identifier."""
    
    def __init__(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Payment ID must be a non-empty string")
        
        # Validate format: PMT-XXXXX
        parts = value.strip().split("-")
        if len(parts) != 2 or parts[0] != "PMT" or not parts[1].isdigit():
            raise ValueError("Payment ID must follow format 'PMT-XXXXX' where XXXXX is numeric")
        
        self._value = value.strip()
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __repr__(self) -> str:
        return f"PaymentId('{self._value}')"


class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"


class TransactionType(Enum):
    """Transaction type enumeration."""
    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"


class TransactionCategory(Enum):
    """Transaction category enumeration."""
    AP = "AP"  # Accounts Payable
    AR = "AR"  # Accounts Receivable
    PAYROLL = "Payroll"
    FX = "FX"  # Foreign Exchange
    FEES = "Fees"
    MISC = "Misc"