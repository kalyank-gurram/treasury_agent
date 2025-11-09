"""Repository interfaces (ports) for the Treasury domain."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from ..entities.treasury import Account, Transaction, Payment, Counterparty
from ..value_objects.treasury import (
    EntityId, AccountId, PaymentId, PaymentStatus
)


class AccountRepository(ABC):
    """Repository interface for Account entities."""
    
    @abstractmethod
    async def find_by_id(self, account_id: AccountId) -> Optional[Account]:
        """Find account by ID."""
        pass
    
    @abstractmethod
    async def find_by_entity(self, entity_id: EntityId) -> List[Account]:
        """Find all accounts for an entity."""
        pass
    
    @abstractmethod
    async def save(self, account: Account) -> None:
        """Save account."""
        pass
    
    @abstractmethod
    async def delete(self, account: Account) -> None:
        """Delete account."""
        pass


class TransactionRepository(ABC):
    """Repository interface for Transaction entities."""
    
    @abstractmethod
    async def find_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Find transaction by ID."""
        pass
    
    @abstractmethod
    async def find_by_account(
        self,
        account_id: AccountId,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Find transactions for an account within date range."""
        pass
    
    @abstractmethod
    async def find_by_entity(
        self,
        entity_id: EntityId,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Find transactions for an entity within date range."""
        pass
    
    @abstractmethod
    async def find_by_counterparty(
        self,
        counterparty: str,
        entity_id: Optional[EntityId] = None
    ) -> List[Transaction]:
        """Find transactions by counterparty."""
        pass
    
    @abstractmethod
    async def save(self, transaction: Transaction) -> None:
        """Save transaction."""
        pass
    
    @abstractmethod
    async def save_many(self, transactions: List[Transaction]) -> None:
        """Save multiple transactions."""
        pass


class PaymentRepository(ABC):
    """Repository interface for Payment aggregates."""
    
    @abstractmethod
    async def find_by_id(self, payment_id: PaymentId) -> Optional[Payment]:
        """Find payment by ID."""
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: PaymentStatus,
        entity_id: Optional[EntityId] = None
    ) -> List[Payment]:
        """Find payments by status."""
        pass
    
    @abstractmethod
    async def find_by_entity(self, entity_id: EntityId) -> List[Payment]:
        """Find all payments for an entity."""
        pass
    
    @abstractmethod
    async def find_overdue_payments(
        self,
        as_of_date: date,
        entity_id: Optional[EntityId] = None
    ) -> List[Payment]:
        """Find overdue payments."""
        pass
    
    @abstractmethod
    async def save(self, payment: Payment) -> None:
        """Save payment aggregate."""
        pass
    
    @abstractmethod
    async def delete(self, payment: Payment) -> None:
        """Delete payment."""
        pass


class CounterpartyRepository(ABC):
    """Repository interface for Counterparty entities."""
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Counterparty]:
        """Find counterparty by name."""
        pass
    
    @abstractmethod
    async def find_by_tier(self, tier: str) -> List[Counterparty]:
        """Find counterparties by tier."""
        pass
    
    @abstractmethod
    async def find_by_rating(self, rating: str) -> List[Counterparty]:
        """Find counterparties by rating."""
        pass
    
    @abstractmethod
    async def find_active(self) -> List[Counterparty]:
        """Find all active counterparties."""
        pass
    
    @abstractmethod
    async def save(self, counterparty: Counterparty) -> None:
        """Save counterparty."""
        pass
    
    @abstractmethod
    async def delete(self, counterparty: Counterparty) -> None:
        """Delete counterparty."""
        pass