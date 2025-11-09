"""Domain events for payment-related operations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from ..value_objects.treasury import PaymentId, EntityId, Money


class DomainEvent(ABC):
    """Base domain event class."""
    
    def __init__(self, aggregate_id: Any, occurred_at: datetime = None):
        self.event_id = uuid4()
        self.aggregate_id = aggregate_id
        self.occurred_at = occurred_at or datetime.now()
        self.event_type = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_id": str(self.aggregate_id),
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self._get_payload()
        }
    
    def _get_payload(self) -> Dict[str, Any]:
        """Get event-specific payload. Override in subclasses."""
        return {}


class PaymentApprovedEvent(DomainEvent):
    """Event raised when a payment is approved."""
    
    def __init__(
        self,
        payment_id: PaymentId,
        entity_id: EntityId,
        amount: Money,
        approved_at: datetime
    ):
        super().__init__(payment_id.value)
        self.payment_id = payment_id
        self.entity_id = entity_id
        self.amount = amount
        self.approved_at = approved_at
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id.value,
            "entity_id": self.entity_id.value,
            "amount": str(self.amount.amount),
            "currency": self.amount.currency.code,
            "approved_at": self.approved_at.isoformat()
        }


class PaymentRejectedEvent(DomainEvent):
    """Event raised when a payment is rejected."""
    
    def __init__(
        self,
        payment_id: PaymentId,
        entity_id: EntityId,
        reason: str,
        rejected_at: datetime
    ):
        super().__init__(payment_id.value)
        self.payment_id = payment_id
        self.entity_id = entity_id
        self.reason = reason
        self.rejected_at = rejected_at
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id.value,
            "entity_id": self.entity_id.value,
            "reason": self.reason,
            "rejected_at": self.rejected_at.isoformat()
        }


class PaymentProcessedEvent(DomainEvent):
    """Event raised when a payment is processed."""
    
    def __init__(
        self,
        payment_id: PaymentId,
        entity_id: EntityId,
        amount: Money,
        processed_at: datetime
    ):
        super().__init__(payment_id.value)
        self.payment_id = payment_id
        self.entity_id = entity_id
        self.amount = amount
        self.processed_at = processed_at
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id.value,
            "entity_id": self.entity_id.value,
            "amount": str(self.amount.amount),
            "currency": self.amount.currency.code,
            "processed_at": self.processed_at.isoformat()
        }


class ChatRequestedEvent(DomainEvent):
    """Event raised when a chat request is made."""
    
    def __init__(
        self,
        question: str,
        entity: str = None,
        timestamp: float = None
    ):
        import time
        super().__init__(f"chat_{int(time.time())}")
        self.question = question
        self.entity = entity or ""
        self.timestamp = timestamp or time.time()
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "entity": self.entity,
            "timestamp": self.timestamp
        }