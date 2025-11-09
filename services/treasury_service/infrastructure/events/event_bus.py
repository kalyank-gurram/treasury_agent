"""Event bus implementation for decoupled communication and audit trails."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Type, TypeVar, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import json
import logging
from uuid import UUID, uuid4

from ...domain.events.payment_events import DomainEvent

T = TypeVar('T', bound=DomainEvent)

logger = logging.getLogger(__name__)


@dataclass
class EventMetadata:
    """Metadata for event processing."""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "causation_id": str(self.causation_id) if self.causation_id else None,
            "version": self.version
        }


@dataclass
class EventEnvelope:
    """Wrapper for events with metadata."""
    event: DomainEvent
    metadata: EventMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event": self.event.to_dict(),
            "metadata": self.metadata.to_dict()
        }


class EventHandler(ABC):
    """Base class for event handlers."""
    
    @abstractmethod
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Handle the event."""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> Type[DomainEvent]:
        """The type of event this handler processes."""
        pass


class EventStore(ABC):
    """Abstract event store for persisting events."""
    
    @abstractmethod
    async def save_event(self, envelope: EventEnvelope) -> None:
        """Save an event to the store."""
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[EventEnvelope]:
        """Get events for an aggregate."""
        pass
    
    @abstractmethod
    async def get_all_events(
        self,
        event_types: Optional[List[str]] = None,
        from_timestamp: Optional[datetime] = None
    ) -> List[EventEnvelope]:
        """Get all events matching criteria."""
        pass


class InMemoryEventStore(EventStore):
    """In-memory event store for development and testing."""
    
    def __init__(self):
        self._events: List[EventEnvelope] = []
        self._events_by_aggregate: Dict[str, List[EventEnvelope]] = {}
        self._lock = asyncio.Lock()
    
    async def save_event(self, envelope: EventEnvelope) -> None:
        """Save an event to the store."""
        async with self._lock:
            self._events.append(envelope)
            
            # Index by aggregate ID
            aggregate_id = str(envelope.event.aggregate_id)
            if aggregate_id not in self._events_by_aggregate:
                self._events_by_aggregate[aggregate_id] = []
            self._events_by_aggregate[aggregate_id].append(envelope)
            
            logger.debug(f"Saved event {envelope.event.event_type} for aggregate {aggregate_id}")
    
    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[EventEnvelope]:
        """Get events for an aggregate."""
        async with self._lock:
            events = self._events_by_aggregate.get(aggregate_id, [])
            return [e for e in events if e.metadata.version >= from_version]
    
    async def get_all_events(
        self,
        event_types: Optional[List[str]] = None,
        from_timestamp: Optional[datetime] = None
    ) -> List[EventEnvelope]:
        """Get all events matching criteria."""
        async with self._lock:
            events = self._events.copy()
            
            if event_types:
                events = [e for e in events if e.event.event_type in event_types]
            
            if from_timestamp:
                events = [e for e in events if e.metadata.timestamp >= from_timestamp]
            
            return events


class EventBus:
    """Central event bus for publishing and subscribing to events."""
    
    def __init__(self, event_store: Optional[EventStore] = None):
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._middleware: List[Callable[[EventEnvelope], None]] = []
        self._event_store = event_store or InMemoryEventStore()
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._is_processing = False
    
    def subscribe(self, handler: EventHandler) -> None:
        """Subscribe an event handler."""
        event_type = handler.event_type
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__class__.__name__} for {event_type.__name__}")
    
    def add_middleware(self, middleware: Callable[[EventEnvelope], None]) -> None:
        """Add middleware to process events."""
        self._middleware.append(middleware)
    
    async def publish(
        self,
        event: DomainEvent,
        source: str = "",
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None
    ) -> None:
        """Publish an event."""
        metadata = EventMetadata(
            source=source,
            correlation_id=correlation_id,
            causation_id=causation_id
        )
        envelope = EventEnvelope(event=event, metadata=metadata)
        
        # Save to event store
        await self._event_store.save_event(envelope)
        
        # Add to processing queue
        await self._processing_queue.put(envelope)
        
        # Start processing if not already running
        if not self._is_processing:
            self._start_processing()
    
    def _start_processing(self) -> None:
        """Start the event processing loop."""
        if self._processing_task and not self._processing_task.done():
            return
        
        self._is_processing = True
        self._processing_task = asyncio.create_task(self._process_events())
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        try:
            while self._is_processing:
                try:
                    # Wait for event with timeout
                    envelope = await asyncio.wait_for(
                        self._processing_queue.get(),
                        timeout=1.0
                    )
                    
                    await self._handle_event(envelope)
                    
                except asyncio.TimeoutError:
                    # No events in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Event processing loop error: {e}", exc_info=True)
        finally:
            self._is_processing = False
    
    async def _handle_event(self, envelope: EventEnvelope) -> None:
        """Handle a single event."""
        event = envelope.event
        metadata = envelope.metadata
        
        # Apply middleware
        for middleware in self._middleware:
            try:
                middleware(envelope)
            except Exception as e:
                logger.error(f"Middleware error: {e}", exc_info=True)
        
        # Find and execute handlers
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for event type {event_type.__name__}")
            return
        
        # Execute handlers concurrently
        handler_tasks = [
            self._execute_handler(handler, event, metadata)
            for handler in handlers
        ]
        
        if handler_tasks:
            await asyncio.gather(*handler_tasks, return_exceptions=True)
    
    async def _execute_handler(
        self,
        handler: EventHandler,
        event: DomainEvent,
        metadata: EventMetadata
    ) -> None:
        """Execute a single event handler."""
        try:
            await handler.handle(event, metadata)
            logger.debug(f"Handler {handler.__class__.__name__} processed {event.event_type}")
        except Exception as e:
            logger.error(
                f"Handler {handler.__class__.__name__} failed to process {event.event_type}: {e}",
                exc_info=True
            )
    
    async def stop_processing(self) -> None:
        """Stop event processing."""
        self._is_processing = False
        if self._processing_task:
            await self._processing_task
    
    async def get_audit_trail(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit trail for an aggregate."""
        events = await self._event_store.get_events(aggregate_id, from_version)
        return [envelope.to_dict() for envelope in events]
    
    async def replay_events(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> None:
        """Replay events for an aggregate."""
        events = await self._event_store.get_events(aggregate_id, from_version)
        for envelope in events:
            await self._handle_event(envelope)


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def configure_event_bus(event_store: Optional[EventStore] = None) -> EventBus:
    """Configure and return the global event bus."""
    global _event_bus
    _event_bus = EventBus(event_store)
    return _event_bus