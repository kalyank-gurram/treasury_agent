"""Base domain entity with common functionality."""

from abc import ABC
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class Entity(ABC):
    """Base entity class with identity and domain event support."""
    
    def __init__(self, entity_id: Optional[UUID] = None):
        self._id = entity_id or uuid4()
        self._domain_events: List[Any] = []
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)
    
    @property
    def id(self) -> UUID:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def mark_modified(self) -> None:
        """Mark entity as modified."""
        self._updated_at = datetime.now(timezone.utc)
    
    def add_domain_event(self, event: Any) -> None:
        """Add a domain event to be published."""
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """Clear all domain events."""
        self._domain_events.clear()
    
    def get_domain_events(self) -> List[Any]:
        """Get all domain events."""
        return self._domain_events.copy()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)


class ValueObject(ABC):
    """Base value object class with immutability and equality by value."""
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


class AggregateRoot(Entity):
    """Base aggregate root with enhanced domain event support."""
    
    def __init__(self, entity_id: Optional[UUID] = None):
        super().__init__(entity_id)
        self._version = 0
    
    @property
    def version(self) -> int:
        """Optimistic locking version."""
        return self._version
    
    def increment_version(self) -> None:
        """Increment version for optimistic locking."""
        self._version += 1
        self.mark_modified()