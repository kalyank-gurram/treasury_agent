"""Dependency injection configuration for Treasury Agent."""

from .container import Container, LifetimeScope
from ...domain.repositories.interfaces import (
    AccountRepository, TransactionRepository, PaymentRepository, CounterpartyRepository
)
from ..repositories.in_memory import (
    InMemoryAccountRepository, InMemoryTransactionRepository, 
    InMemoryPaymentRepository, InMemoryCounterpartyRepository
)
from ...domain.services.treasury_services import (
    TreasuryDomainService, PaymentApprovalService, RiskAssessmentService
)


def configure_dependencies() -> Container:
    """Configure dependency injection container.""" 
    container = Container()
    
    # Register the container itself
    container.register_singleton(Container, instance=container)
    
    # Register repositories as singletons
    container.register_singleton(AccountRepository, InMemoryAccountRepository)
    container.register_singleton(TransactionRepository, InMemoryTransactionRepository)
    container.register_singleton(PaymentRepository, InMemoryPaymentRepository)
    container.register_singleton(CounterpartyRepository, InMemoryCounterpartyRepository)
    
    # Register domain services as transient (new instance each time)
    container.register_transient(TreasuryDomainService, TreasuryDomainService)
    container.register_transient(PaymentApprovalService, PaymentApprovalService)
    container.register_transient(RiskAssessmentService, RiskAssessmentService)
    
    # Register security services
    try:
        from ..security.auth_service import AuthenticationService
        from ..security.auth_middleware import AuthMiddleware
        from ..config.settings import get_config
        
        # Get configuration
        config = get_config()
        
        # Register AuthenticationService as singleton with configuration
        container.register_singleton(
            AuthenticationService,
            factory=lambda: AuthenticationService(
                jwt_secret=config.security.jwt_secret_key,
                session_duration_minutes=config.security.session_duration_minutes
            )
        )
        
        # Register AuthMiddleware as singleton (depends on AuthenticationService)
        container.register_singleton(AuthMiddleware, AuthMiddleware)
        
    except ImportError:
        # Security modules not available in this context
        pass
    
    # Register application services (will be added when server is in Python path)
    try:
        from ...services.chat import ChatService
        container.register_transient(ChatService, ChatService)
    except ImportError:
        # Server module not available in this context
        pass
    
    return container


# Global container instance
_configured_container: Container = None


def get_configured_container() -> Container:
    """Get the configured DI container."""
    global _configured_container
    if _configured_container is None:
        _configured_container = configure_dependencies()
    return _configured_container