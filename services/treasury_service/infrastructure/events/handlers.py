"""Event handlers for Treasury domain events."""

import logging
from typing import Type
from datetime import datetime

from ...domain.events.payment_events import (
    DomainEvent, PaymentApprovedEvent, PaymentRejectedEvent, PaymentProcessedEvent
)
from .event_bus import EventHandler, EventMetadata

logger = logging.getLogger(__name__)


class AuditTrailHandler(EventHandler):
    """Handler that logs all events for audit purposes."""
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return DomainEvent  # Handle all domain events
    
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Log event for audit trail."""
        audit_entry = {
            "event_id": str(metadata.event_id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "timestamp": metadata.timestamp.isoformat(),
            "source": metadata.source,
            "payload": event.to_dict()
        }
        
        # In production, this would write to a dedicated audit log store
        logger.info(f"AUDIT: {event.event_type}", extra={"audit_data": audit_entry})


class PaymentApprovedHandler(EventHandler):
    """Handler for payment approved events."""
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return PaymentApprovedEvent
    
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Handle payment approved event."""
        if not isinstance(event, PaymentApprovedEvent):
            return
        
        logger.info(
            f"Payment {event.payment_id.value} approved for entity {event.entity_id.value}",
            extra={
                "payment_id": event.payment_id.value,
                "entity_id": event.entity_id.value,
                "amount": str(event.amount),
                "approved_at": event.approved_at.isoformat()
            }
        )
        
        # In production, this could:
        # 1. Send notifications to stakeholders
        # 2. Update external systems
        # 3. Trigger downstream processes
        # 4. Update dashboards/metrics


class PaymentRejectedHandler(EventHandler):
    """Handler for payment rejected events."""
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return PaymentRejectedEvent
    
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Handle payment rejected event."""
        if not isinstance(event, PaymentRejectedEvent):
            return
        
        logger.warning(
            f"Payment {event.payment_id.value} rejected: {event.reason}",
            extra={
                "payment_id": event.payment_id.value,
                "entity_id": event.entity_id.value,
                "reason": event.reason,
                "rejected_at": event.rejected_at.isoformat()
            }
        )
        
        # In production, this could:
        # 1. Send rejection notifications
        # 2. Log compliance events
        # 3. Update risk metrics
        # 4. Trigger remediation workflows


class PaymentProcessedHandler(EventHandler):
    """Handler for payment processed events."""
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return PaymentProcessedEvent
    
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Handle payment processed event."""
        if not isinstance(event, PaymentProcessedEvent):
            return
        
        logger.info(
            f"Payment {event.payment_id.value} processed successfully",
            extra={
                "payment_id": event.payment_id.value,
                "entity_id": event.entity_id.value,
                "amount": str(event.amount),
                "processed_at": event.processed_at.isoformat()
            }
        )
        
        # In production, this could:
        # 1. Update account balances
        # 2. Send confirmation notifications
        # 3. Update cash flow forecasts
        # 4. Trigger settlement processes


class MetricsHandler(EventHandler):
    """Handler that updates metrics based on events."""
    
    def __init__(self):
        self._payment_metrics = {
            "approved_count": 0,
            "rejected_count": 0,
            "processed_count": 0,
            "total_approved_amount": 0.0,
            "total_processed_amount": 0.0
        }
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return DomainEvent  # Handle all domain events
    
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Update metrics based on events."""
        if isinstance(event, PaymentApprovedEvent):
            self._payment_metrics["approved_count"] += 1
            self._payment_metrics["total_approved_amount"] += float(event.amount.amount)
            
        elif isinstance(event, PaymentRejectedEvent):
            self._payment_metrics["rejected_count"] += 1
            
        elif isinstance(event, PaymentProcessedEvent):
            self._payment_metrics["processed_count"] += 1
            self._payment_metrics["total_processed_amount"] += float(event.amount.amount)
        
        # In production, this would update metrics stores (Prometheus, etc.)
        logger.debug(f"Updated metrics: {self._payment_metrics}")
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return self._payment_metrics.copy()


class ComplianceHandler(EventHandler):
    """Handler for compliance and regulatory requirements."""
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        return DomainEvent  # Handle all domain events
    
    async def handle(self, event: DomainEvent, metadata: EventMetadata) -> None:
        """Handle compliance requirements."""
        # Check for high-value transactions requiring special reporting
        if isinstance(event, (PaymentApprovedEvent, PaymentProcessedEvent)):
            amount = event.amount.amount
            
            # Example: Flag large transactions for regulatory reporting
            if amount >= 10000:  # $10,000 threshold
                compliance_alert = {
                    "alert_type": "LARGE_TRANSACTION",
                    "payment_id": event.payment_id.value,
                    "entity_id": event.entity_id.value,
                    "amount": str(amount),
                    "currency": event.amount.currency.code,
                    "timestamp": metadata.timestamp.isoformat(),
                    "requires_reporting": True
                }
                
                logger.warning(
                    f"Large transaction alert: {event.payment_id.value}",
                    extra={"compliance_alert": compliance_alert}
                )
        
        # Example: Monitor rejection patterns for risk analysis
        elif isinstance(event, PaymentRejectedEvent):
            # Track rejection patterns for risk assessment
            risk_indicator = {
                "risk_type": "PAYMENT_REJECTION",
                "entity_id": event.entity_id.value,
                "reason": event.reason,
                "timestamp": metadata.timestamp.isoformat()
            }
            
            logger.info(
                "Risk indicator: Payment rejection pattern",
                extra={"risk_indicator": risk_indicator}
            )