"""In-memory repository implementations for development and testing."""

from datetime import date
from typing import List, Optional, Dict
from uuid import UUID

from ...domain.entities.treasury import Account, Transaction, Payment, Counterparty
from ...domain.value_objects.treasury import (
    EntityId, AccountId, PaymentId, PaymentStatus
)
from ...domain.repositories.interfaces import (
    AccountRepository, TransactionRepository, PaymentRepository, CounterpartyRepository
)


class InMemoryAccountRepository(AccountRepository):
    """In-memory implementation of AccountRepository."""
    
    def __init__(self):
        self._accounts: Dict[str, Account] = {}
    
    async def find_by_id(self, account_id: AccountId) -> Optional[Account]:
        """Find account by ID."""
        return self._accounts.get(account_id.value)
    
    async def find_by_entity(self, entity_id: EntityId) -> List[Account]:
        """Find all accounts for an entity."""
        return [
            account for account in self._accounts.values()
            if account.entity_id == entity_id
        ]
    
    async def save(self, account: Account) -> None:
        """Save account."""
        self._accounts[account.account_id.value] = account
    
    async def delete(self, account: Account) -> None:
        """Delete account."""
        self._accounts.pop(account.account_id.value, None)


class InMemoryTransactionRepository(TransactionRepository):
    """In-memory implementation of TransactionRepository."""
    
    def __init__(self):
        self._transactions: Dict[str, Transaction] = {}
    
    async def find_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Find transaction by ID."""
        return self._transactions.get(str(transaction_id))
    
    async def find_by_account(
        self,
        account_id: AccountId,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Find transactions for an account within date range."""
        transactions = [
            tx for tx in self._transactions.values()
            if tx.account_id == account_id
        ]
        
        if start_date:
            transactions = [tx for tx in transactions if tx.transaction_date >= start_date]
        
        if end_date:
            transactions = [tx for tx in transactions if tx.transaction_date <= end_date]
        
        return sorted(transactions, key=lambda x: x.transaction_date)
    
    async def find_by_entity(
        self,
        entity_id: EntityId,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Find transactions for an entity within date range."""
        transactions = [
            tx for tx in self._transactions.values()
            if tx.entity_id == entity_id
        ]
        
        if start_date:
            transactions = [tx for tx in transactions if tx.transaction_date >= start_date]
        
        if end_date:
            transactions = [tx for tx in transactions if tx.transaction_date <= end_date]
        
        return sorted(transactions, key=lambda x: x.transaction_date)
    
    async def find_by_counterparty(
        self,
        counterparty: str,
        entity_id: Optional[EntityId] = None
    ) -> List[Transaction]:
        """Find transactions by counterparty."""
        transactions = [
            tx for tx in self._transactions.values()
            if tx.counterparty == counterparty
        ]
        
        if entity_id:
            transactions = [tx for tx in transactions if tx.entity_id == entity_id]
        
        return sorted(transactions, key=lambda x: x.transaction_date)
    
    async def save(self, transaction: Transaction) -> None:
        """Save transaction."""
        self._transactions[str(transaction.id)] = transaction
    
    async def save_many(self, transactions: List[Transaction]) -> None:
        """Save multiple transactions."""
        for transaction in transactions:
            await self.save(transaction)


class InMemoryPaymentRepository(PaymentRepository):
    """In-memory implementation of PaymentRepository."""
    
    def __init__(self):
        self._payments: Dict[str, Payment] = {}
    
    async def find_by_id(self, payment_id: PaymentId) -> Optional[Payment]:
        """Find payment by ID."""
        return self._payments.get(payment_id.value)
    
    async def find_by_status(
        self,
        status: PaymentStatus,
        entity_id: Optional[EntityId] = None
    ) -> List[Payment]:
        """Find payments by status."""
        payments = [
            payment for payment in self._payments.values()
            if payment.status == status
        ]
        
        if entity_id:
            payments = [p for p in payments if p.entity_id == entity_id]
        
        return sorted(payments, key=lambda x: x.due_date)
    
    async def find_by_entity(self, entity_id: EntityId) -> List[Payment]:
        """Find all payments for an entity."""
        payments = [
            payment for payment in self._payments.values()
            if payment.entity_id == entity_id
        ]
        
        return sorted(payments, key=lambda x: x.due_date)
    
    async def find_overdue_payments(
        self,
        as_of_date: date,
        entity_id: Optional[EntityId] = None
    ) -> List[Payment]:
        """Find overdue payments."""
        payments = [
            payment for payment in self._payments.values()
            if payment.is_overdue(as_of_date)
        ]
        
        if entity_id:
            payments = [p for p in payments if p.entity_id == entity_id]
        
        return sorted(payments, key=lambda x: x.due_date)
    
    async def save(self, payment: Payment) -> None:
        """Save payment aggregate."""
        self._payments[payment.payment_id.value] = payment
    
    async def delete(self, payment: Payment) -> None:
        """Delete payment."""
        self._payments.pop(payment.payment_id.value, None)


class InMemoryCounterpartyRepository(CounterpartyRepository):
    """In-memory implementation of CounterpartyRepository."""
    
    def __init__(self):
        self._counterparties: Dict[str, Counterparty] = {}
    
    async def find_by_name(self, name: str) -> Optional[Counterparty]:
        """Find counterparty by name."""
        return self._counterparties.get(name)
    
    async def find_by_tier(self, tier: str) -> List[Counterparty]:
        """Find counterparties by tier."""
        return [
            cp for cp in self._counterparties.values()
            if cp.tier.lower() == tier.lower()
        ]
    
    async def find_by_rating(self, rating: str) -> List[Counterparty]:
        """Find counterparties by rating."""
        return [
            cp for cp in self._counterparties.values()
            if cp.rating.lower() == rating.lower()
        ]
    
    async def find_active(self) -> List[Counterparty]:
        """Find all active counterparties."""
        return [
            cp for cp in self._counterparties.values()
            if cp.is_active
        ]
    
    async def save(self, counterparty: Counterparty) -> None:
        """Save counterparty."""
        self._counterparties[counterparty.name] = counterparty
    
    async def delete(self, counterparty: Counterparty) -> None:
        """Delete counterparty."""
        self._counterparties.pop(counterparty.name, None)