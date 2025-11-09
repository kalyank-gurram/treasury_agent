"""Treasury Agent Monitoring & Observability Package.

This package provides comprehensive monitoring, observability, and alerting
capabilities for the treasury management platform.

Components:
- MetricsCollector: System and business metrics collection
- AlertManager: Intelligent alerting with escalation
- HealthMonitor: System health and availability monitoring
- PerformanceProfiler: Performance analysis and optimization
- DashboardService: Real-time dashboards and visualization
"""

from .metrics import MetricsCollector, MetricType, MetricValue
from .alerts import AlertManager, AlertSeverity, Alert, AlertRule
from .health import HealthMonitor, HealthStatus, ComponentHealth, get_health_monitor, configure_default_health_checks
from .performance import PerformanceProfiler, PerformanceMetric
from .dashboard import DashboardService, Dashboard, Widget, WidgetType
from .monitoring import (
    get_observability_manager, configure_observability, trace_operation, monitor_performance
)

__all__ = [
    # Metrics
    'MetricsCollector',
    'MetricType', 
    'MetricValue',
    
    # Alerting
    'AlertManager',
    'AlertSeverity',
    'Alert',
    'AlertRule',
    
    # Health Monitoring
    'HealthMonitor',
    'HealthStatus',
    'ComponentHealth',
    
    # Performance
    'PerformanceProfiler',
    'PerformanceMetric',
    
    # Dashboard
    'DashboardService',
    'Dashboard',
    'Widget',
    'WidgetType',
    
    # Observability Core
    'get_observability_manager',
    'configure_observability',
    'get_health_monitor',
    'configure_default_health_checks',
    'trace_operation',
    'monitor_performance'
]