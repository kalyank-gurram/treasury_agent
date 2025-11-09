"""Lightweight dependency injection container for Treasury Agent."""

import inspect
from typing import Any, Callable, Dict, Type, TypeVar, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum

T = TypeVar('T')


class LifetimeScope(Enum):
    """Dependency lifetime scopes."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor:
    """Describes a service registration."""
    
    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ):
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        
        # Validation
        provided_count = sum(x is not None for x in [implementation_type, factory, instance])
        if provided_count != 1:
            raise ValueError("Exactly one of implementation_type, factory, or instance must be provided")


class Container:
    """Lightweight dependency injection container."""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
    
    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None
    ) -> 'Container':
        """Register a singleton service."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            instance=instance,
            lifetime=LifetimeScope.SINGLETON
        )
        self._services[service_type] = descriptor
        return self
    
    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """Register a transient service (new instance each time)."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=LifetimeScope.TRANSIENT
        )
        self._services[service_type] = descriptor
        return self
    
    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """Register a scoped service (same instance within scope)."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=LifetimeScope.SCOPED
        )
        self._services[service_type] = descriptor
        return self
    
    def get(self, service_type: Type[T]) -> T:
        """Resolve a service instance."""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} not registered")
        
        descriptor = self._services[service_type]
        
        # Handle singleton lifetime
        if descriptor.lifetime == LifetimeScope.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            instance = self._create_instance(descriptor)
            self._singletons[service_type] = instance
            return instance
        
        # Handle scoped lifetime
        elif descriptor.lifetime == LifetimeScope.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]
            
            instance = self._create_instance(descriptor)
            self._scoped_instances[service_type] = instance
            return instance
        
        # Handle transient lifetime
        else:
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance based on the descriptor."""
        # Direct instance
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Factory function
        if descriptor.factory is not None:
            return self._invoke_with_injection(descriptor.factory)
        
        # Implementation type
        if descriptor.implementation_type is not None:
            return self._create_from_type(descriptor.implementation_type)
        
        raise ValueError("No way to create instance from descriptor")
    
    def _create_from_type(self, impl_type: Type) -> Any:
        """Create instance from type with constructor injection."""
        # Get constructor signature
        sig = inspect.signature(impl_type.__init__)
        parameters = sig.parameters
        
        # Skip 'self' parameter
        param_names = [name for name in parameters.keys() if name != 'self']
        
        # Resolve dependencies
        kwargs = {}
        for param_name in param_names:
            param = parameters[param_name]
            if param.annotation != inspect.Parameter.empty:
                # Try to resolve the parameter type
                try:
                    kwargs[param_name] = self.get(param.annotation)
                except ValueError:
                    # If dependency not registered and has default, use default
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise ValueError(f"Cannot resolve dependency {param.annotation} for {impl_type.__name__}")
        
        return impl_type(**kwargs)
    
    def _invoke_with_injection(self, func: Callable) -> Any:
        """Invoke function with dependency injection."""
        sig = inspect.signature(func)
        parameters = sig.parameters
        
        kwargs = {}
        for param_name, param in parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.get(param.annotation)
                except ValueError:
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise ValueError(f"Cannot resolve dependency {param.annotation} for function {func.__name__}")
        
        return func(**kwargs)
    
    def create_scope(self) -> 'ServiceScope':
        """Create a new service scope."""
        return ServiceScope(self)
    
    def clear_scoped_instances(self) -> None:
        """Clear all scoped instances."""
        self._scoped_instances.clear()


class ServiceScope:
    """Represents a service scope with scoped lifetime management."""
    
    def __init__(self, container: Container):
        self._container = container
        self._original_scoped = container._scoped_instances.copy()
    
    def get(self, service_type: Type[T]) -> T:
        """Get service within this scope."""
        return self._container.get(service_type)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original scoped instances
        self._container._scoped_instances = self._original_scoped


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def configure_container() -> Container:
    """Configure and return the global container."""
    container = get_container()
    
    # Register core dependencies here
    # This will be called during application startup
    
    return container


def inject(service_type: Type[T]) -> T:
    """Convenience function to inject a dependency."""
    return get_container().get(service_type)