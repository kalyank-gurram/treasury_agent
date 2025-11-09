"""Treasury domain entities with rich business logic."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from .base import Entity, AggregateRoot
from ..value_objects.treasury import (
    Money, Currency, EntityId, AccountId, PaymentId, PaymentStatus,
    TransactionType, TransactionCategory
)


class Account(Entity):
    """Account entity representing a treasury account."""
    
    def __init__(
        self,
        account_id: AccountId,
        entity_id: EntityId,
        account_type: str,
        currency: Currency,
        entity_uuid: Optional[UUID] = None
    ):
        super().__init__(entity_uuid)
        self._account_id = account_id
        self._entity_id = entity_id
        self._account_type = account_type
        self._currency = currency
        self._balance = Money(0, currency)
        self._is_active = True
    
    @property
    def account_id(self) -> AccountId:
        return self._account_id
    
    @property
    def entity_id(self) -> EntityId:
        return self._entity_id
    
    @property
    def account_type(self) -> str:
        return self._account_type
    
    @property
    def currency(self) -> Currency:
        return self._currency
    
    @property
    def balance(self) -> Money:
        return self._balance
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def update_balance(self, new_balance: Money) -> None:
        """Update account balance."""
        if self._currency != new_balance.currency:
            raise ValueError(f"Currency mismatch: {self._currency} != {new_balance.currency}")
        
        self._balance = new_balance
        self.mark_modified()
    
    def deactivate(self) -> None:
        """Deactivate the account."""
        self._is_active = False
        self.mark_modified()
    
    def activate(self) -> None:
        """Activate the account."""
        self._is_active = True
        self.mark_modified()


class Transaction(Entity):
    """Transaction entity representing a financial transaction."""
    
    def __init__(
        self,
        account_id: AccountId,
        entity_id: EntityId,
        transaction_date: date,
        transaction_type: TransactionType,
        amount: Money,
        counterparty: str,
        category: TransactionCategory,
        description: Optional[str] = None,
        entity_uuid: Optional[UUID] = None
    ):
        super().__init__(entity_uuid)
        self._account_id = account_id
        self._entity_id = entity_id
        self._transaction_date = transaction_date
        self._transaction_type = transaction_type
        self._amount = amount
        self._counterparty = counterparty
        self._category = category
        self._description = description or ""
    
    @property
    def account_id(self) -> AccountId:
        return self._account_id
    
    @property
    def entity_id(self) -> EntityId:
        return self._entity_id
    
    @property
    def transaction_date(self) -> date:
        return self._transaction_date
    
    @property
    def transaction_type(self) -> TransactionType:
        return self._transaction_type
    
    @property
    def amount(self) -> Money:
        return self._amount
    
    @property
    def counterparty(self) -> str:
        return self._counterparty
    
    @property
    def category(self) -> TransactionCategory:
        return self._category
    
    @property
    def description(self) -> str:
        return self._description
    
    def is_inflow(self) -> bool:
        """Check if transaction is an inflow."""
        return self._transaction_type == TransactionType.INFLOW
    
    def is_outflow(self) -> bool:
        """Check if transaction is an outflow."""
        return self._transaction_type == TransactionType.OUTFLOW


class Payment(AggregateRoot):
    """Payment aggregate root with business logic and state management."""
    
    def __init__(
        self,
        payment_id: PaymentId,
        account_id: AccountId,
        entity_id: EntityId,
        amount: Money,
        counterparty: str,
        due_date: date,
        status: PaymentStatus = PaymentStatus.PENDING,
        description: Optional[str] = None,
        entity_uuid: Optional[UUID] = None
    ):
        super().__init__(entity_uuid)
        self._payment_id = payment_id
        self._account_id = account_id
        self._entity_id = entity_id
        self._amount = amount
        self._counterparty = counterparty
        self._due_date = due_date
        self._status = status
        self._description = description or ""
        self._approval_date: Optional[datetime] = None
        self._rejection_reason: Optional[str] = None
    
    @property
    def payment_id(self) -> PaymentId:
        return self._payment_id
    
    @property
    def account_id(self) -> AccountId:
        return self._account_id
    
    @property
    def entity_id(self) -> EntityId:
        return self._entity_id
    
    @property
    def amount(self) -> Money:
        return self._amount
    
    @property
    def counterparty(self) -> str:
        return self._counterparty
    
    @property
    def due_date(self) -> date:
        return self._due_date
    
    @property
    def status(self) -> PaymentStatus:
        return self._status
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def approval_date(self) -> Optional[datetime]:
        return self._approval_date
    
    @property
    def rejection_reason(self) -> Optional[str]:
        return self._rejection_reason
    
    def approve(self, approval_date: Optional[datetime] = None) -> None:
        """Approve the payment."""
        if self._status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot approve payment in status: {self._status}")
        
        self._status = PaymentStatus.APPROVED
        self._approval_date = approval_date or datetime.now()
        self.mark_modified()
        self.increment_version()
        
        # Add domain event for approval
        from ..events.payment_events import PaymentApprovedEvent
        self.add_domain_event(PaymentApprovedEvent(
            payment_id=self._payment_id,
            entity_id=self._entity_id,
            amount=self._amount,
            approved_at=self._approval_date
        ))
    
    def reject(self, reason: str, rejection_date: Optional[datetime] = None) -> None:
        """Reject the payment with reason."""
        if self._status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot reject payment in status: {self._status}")
        
        if not reason.strip():
            raise ValueError("Rejection reason is required")
        
        self._status = PaymentStatus.REJECTED
        self._rejection_reason = reason.strip()
        self.mark_modified()
        self.increment_version()
        
        # Add domain event for rejection
        from ..events.payment_events import PaymentRejectedEvent
        self.add_domain_event(PaymentRejectedEvent(
            payment_id=self._payment_id,
            entity_id=self._entity_id,
            reason=reason,
            rejected_at=rejection_date or datetime.now()
        ))
    
    def process(self) -> None:
        """Mark payment as processed."""
        if self._status != PaymentStatus.APPROVED:
            raise ValueError(f"Cannot process payment in status: {self._status}")
        
        self._status = PaymentStatus.PROCESSED
        self.mark_modified()
        self.increment_version()
        
        # Add domain event for processing
        from ..events.payment_events import PaymentProcessedEvent
        self.add_domain_event(PaymentProcessedEvent(
            payment_id=self._payment_id,
            entity_id=self._entity_id,
            amount=self._amount,
            processed_at=datetime.now()
        ))
    
    def cancel(self, reason: str) -> None:
        """Cancel the payment."""
        if self._status == PaymentStatus.PROCESSED:
            raise ValueError("Cannot cancel processed payment")
        
        self._status = PaymentStatus.CANCELLED
        self._rejection_reason = reason
        self.mark_modified()
        self.increment_version()
    
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self._status == PaymentStatus.PENDING
    
    def is_approved(self) -> bool:
        """Check if payment is approved."""
        return self._status == PaymentStatus.APPROVED
    
    def is_overdue(self, reference_date: Optional[date] = None) -> bool:
        """Check if payment is overdue."""
        ref_date = reference_date or date.today()
        return self._due_date < ref_date and self._status == PaymentStatus.PENDING


class Counterparty(Entity):
    """Counterparty entity for risk and exposure management."""
    
    def __init__(
        self,
        name: str,
        tier: str,
        rating: str,
        country: str,
        entity_uuid: Optional[UUID] = None
    ):
        super().__init__(entity_uuid)
        self._name = name.strip()
        self._tier = tier
        self._rating = rating
        self._country = country
        self._is_active = True
        
        if not self._name:
            raise ValueError("Counterparty name cannot be empty")
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def tier(self) -> str:
        return self._tier
    
    @property
    def rating(self) -> str:
        return self._rating
    
    @property
    def country(self) -> str:
        return self._country
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def update_rating(self, new_rating: str) -> None:
        """Update counterparty rating."""
        self._rating = new_rating
        self.mark_modified()
    
    def update_tier(self, new_tier: str) -> None:
        """Update counterparty tier."""
        self._tier = new_tier
        self.mark_modified()
    
    def deactivate(self) -> None:
        """Deactivate counterparty."""
        self._is_active = False
        self.mark_modified()
    
    def is_tier_1(self) -> bool:
        """Check if counterparty is tier-1."""
        return self._tier.lower() == "tier-1"