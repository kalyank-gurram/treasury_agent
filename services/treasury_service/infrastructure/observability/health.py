"""System Health Monitoring for Treasury Operations.

This module provides comprehensive health monitoring capabilities including
system component health checks, dependency monitoring, and service availability tracking.
"""

import asyncio
import time
import json
import psutil
import socket
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import uuid
import requests
from urllib.parse import urlparse


class HealthStatus(Enum):
    """Health status levels for system components."""
    HEALTHY = "healthy"          # Component is functioning normally
    DEGRADED = "degraded"        # Component has minor issues but functional
    UNHEALTHY = "unhealthy"      # Component has significant issues
    CRITICAL = "critical"        # Component is failing or unavailable
    UNKNOWN = "unknown"          # Health status cannot be determined


class ComponentType(Enum):
    """Types of system components that can be monitored."""
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    MICROSERVICE = "microservice"
    QUEUE = "queue"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    COMPUTE = "compute"
    STORAGE = "storage"
    SECURITY_SERVICE = "security_service"


@dataclass
class HealthCheck:
    """Configuration for a health check."""
    check_id: str
    name: str
    component_type: ComponentType
    check_function: Callable[[], Tuple[HealthStatus, Dict[str, Any]]]
    
    # Check configuration
    interval_seconds: int = 60
    timeout_seconds: int = 10
    retry_attempts: int = 3
    
    # Thresholds
    healthy_threshold: float = 0.95    # 95% success rate for healthy
    degraded_threshold: float = 0.80   # 80% success rate for degraded
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    is_critical: bool = False
    is_enabled: bool = True


@dataclass
class ComponentHealth:
    """Health status of a system component."""
    component_id: str
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    last_check_time: datetime
    
    # Health metrics
    response_time_ms: float = 0.0
    success_rate: float = 0.0
    uptime_percentage: float = 0.0
    
    # Status details
    status_message: str = ""
    error_details: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    # History tracking
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    last_status_change: Optional[datetime] = None


class HealthMonitor:
    """Comprehensive health monitoring system for treasury operations."""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        # Health check registry
        self.health_checks: Dict[str, HealthCheck] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        # Health history and statistics
        self.health_history = {}  # component_id -> list of health records
        self.health_statistics = {
            'total_checks_performed': 0,
            'failed_checks': 0,
            'avg_response_time': 0.0,
            'components_monitored': 0
        }
        
        # Alert callbacks
        self.health_change_callbacks: List[Callable[[ComponentHealth], None]] = []
        
        # Initialize treasury-specific health checks
        self._initialize_treasury_health_checks()
        
    def _initialize_treasury_health_checks(self):
        """Initialize health checks for treasury system components."""
        
        # Database health check
        self.register_health_check(HealthCheck(
            check_id="treasury_database",
            name="Treasury Database Connection",
            component_type=ComponentType.DATABASE,
            check_function=self._check_database_health,
            interval_seconds=30,
            is_critical=True,
            description="Primary treasury database connectivity and performance"
        ))
        
        # Cache health check
        self.register_health_check(HealthCheck(
            check_id="redis_cache",
            name="Redis Cache Service",
            component_type=ComponentType.CACHE,
            check_function=self._check_redis_health,
            interval_seconds=60,
            description="Redis cache for session and data caching"
        ))
        
        # Payment API health check
        self.register_health_check(HealthCheck(
            check_id="payment_api",
            name="Payment Processing API",
            component_type=ComponentType.EXTERNAL_API,
            check_function=self._check_payment_api_health,
            interval_seconds=45,
            is_critical=True,
            description="External payment processing service"
        ))
        
        # Investment data API
        self.register_health_check(HealthCheck(
            check_id="market_data_api",
            name="Market Data API",
            component_type=ComponentType.EXTERNAL_API,
            check_function=self._check_market_data_api_health,
            interval_seconds=120,
            description="Market data provider for investment pricing"
        ))
        
        # System resource checks
        self.register_health_check(HealthCheck(
            check_id="system_resources",
            name="System Resources",
            component_type=ComponentType.COMPUTE,
            check_function=self._check_system_resources,
            interval_seconds=30,
            is_critical=True,
            description="CPU, memory, and disk utilization"
        ))
        
        # File system health
        self.register_health_check(HealthCheck(
            check_id="file_system",
            name="File System Health",
            component_type=ComponentType.FILE_SYSTEM,
            check_function=self._check_file_system_health,
            interval_seconds=300,  # 5 minutes
            description="Disk space and file system availability"
        ))
        
        # Network connectivity
        self.register_health_check(HealthCheck(
            check_id="network_connectivity",
            name="Network Connectivity",
            component_type=ComponentType.NETWORK,
            check_function=self._check_network_connectivity,
            interval_seconds=60,
            description="External network connectivity and DNS resolution"
        ))
        
        # Security service health
        self.register_health_check(HealthCheck(
            check_id="security_service",
            name="Security Authentication Service",
            component_type=ComponentType.SECURITY_SERVICE,
            check_function=self._check_security_service_health,
            interval_seconds=45,
            is_critical=True,
            description="Authentication and authorization service health"
        ))
        
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check."""
        self.health_checks[health_check.check_id] = health_check
        
        # Initialize component health tracking
        self.component_health[health_check.check_id] = ComponentHealth(
            component_id=health_check.check_id,
            component_name=health_check.name,
            component_type=health_check.component_type,
            status=HealthStatus.UNKNOWN,
            last_check_time=datetime.now(timezone.utc),
            dependencies=health_check.dependencies.copy()
        )
        
        self.logger.info(f"Registered health check: {health_check.name}")
        
    def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_active:
            self.logger.warning("Health monitoring already active")
            return
            
        self.monitoring_active = True
        self.shutdown_event.clear()
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("Started health monitoring")
        
    def stop_monitoring(self):
        """Stop health monitoring."""
        if not self.monitoring_active:
            return
            
        self.monitoring_active = False
        self.shutdown_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
            
        self.logger.info("Stopped health monitoring")
        
    def perform_health_check(self, check_id: str) -> ComponentHealth:
        """Perform a single health check."""
        if check_id not in self.health_checks:
            raise ValueError(f"Health check {check_id} not found")
            
        health_check = self.health_checks[check_id]
        
        if not health_check.is_enabled:
            return self.component_health[check_id]
            
        start_time = time.time()
        attempts = 0
        last_error = None
        
        while attempts < health_check.retry_attempts:
            try:
                # Perform the health check
                status, metadata = health_check.check_function()
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Update component health
                component_health = self.component_health[check_id]
                previous_status = component_health.status
                
                component_health.status = status
                component_health.last_check_time = datetime.now(timezone.utc)
                component_health.response_time_ms = response_time
                component_health.metadata.update(metadata)
                component_health.error_details = None
                
                # Update success rate
                self._update_success_rate(check_id, True)
                
                # Track status changes
                if previous_status != status:
                    component_health.last_status_change = datetime.now(timezone.utc)
                    self._notify_health_change(component_health)
                    
                # Add to history
                self._add_to_history(check_id, status, response_time, metadata)
                
                # Update statistics
                self.health_statistics['total_checks_performed'] += 1
                self._update_avg_response_time(response_time)
                
                break
                
            except Exception as e:
                attempts += 1
                last_error = str(e)
                
                if attempts >= health_check.retry_attempts:
                    # Mark as unhealthy after all retries failed
                    component_health = self.component_health[check_id]
                    previous_status = component_health.status
                    
                    component_health.status = HealthStatus.CRITICAL
                    component_health.last_check_time = datetime.now(timezone.utc)
                    component_health.error_details = last_error
                    component_health.response_time_ms = (time.time() - start_time) * 1000
                    
                    # Update failure statistics
                    self._update_success_rate(check_id, False)
                    self.health_statistics['failed_checks'] += 1
                    self.health_statistics['total_checks_performed'] += 1
                    
                    # Track status changes
                    if previous_status != component_health.status:
                        component_health.last_status_change = datetime.now(timezone.utc)
                        self._notify_health_change(component_health)
                        
                    self.logger.error(f"Health check {check_id} failed after {attempts} attempts: {last_error}")
                else:
                    time.sleep(1)  # Wait before retry
                    
        return self.component_health[check_id]
        
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary."""
        current_time = datetime.now(timezone.utc)
        
        # Count components by status
        status_counts = {}
        critical_components = []
        unhealthy_components = []
        
        for component_health in self.component_health.values():
            status = component_health.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if component_health.status == HealthStatus.CRITICAL:
                critical_components.append({
                    'id': component_health.component_id,
                    'name': component_health.component_name,
                    'error': component_health.error_details
                })
            elif component_health.status == HealthStatus.UNHEALTHY:
                unhealthy_components.append({
                    'id': component_health.component_id,
                    'name': component_health.component_name,
                    'error': component_health.error_details
                })
                
        # Calculate overall system health
        overall_status = self._calculate_overall_health()
        
        # Get uptime statistics
        uptime_stats = self._calculate_uptime_statistics()
        
        return {
            'timestamp': current_time.isoformat(),
            'overall_status': overall_status.value,
            'components_monitored': len(self.component_health),
            'status_distribution': status_counts,
            'critical_components': critical_components,
            'unhealthy_components': unhealthy_components,
            'uptime_statistics': uptime_stats,
            'monitoring_statistics': self.health_statistics,
            'last_check_time': max(
                (c.last_check_time for c in self.component_health.values()),
                default=current_time
            ).isoformat()
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks and return comprehensive results."""
        try:
            # Perform all health checks
            for check_id in self.health_checks.keys():
                self.perform_health_check(check_id)
            
            # Return system health summary
            return self.get_system_health_summary()
        except Exception as e:
            self.logger.error(f"Error running health checks: {str(e)}")
            return {
                'status': 'error',
                'message': 'Failed to run health checks',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Check if the application is ready to serve traffic."""
        try:
            # Run critical health checks
            critical_checks = ['database', 'redis', 'system_resources']
            all_ready = True
            failed_checks = []
            
            for check_id in critical_checks:
                if check_id in self.health_checks:
                    health = self.perform_health_check(check_id)
                    if health.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                        all_ready = False
                        failed_checks.append({
                            'component': health.component_name,
                            'status': health.status.value,
                            'error': health.error_details
                        })
            
            return {
                'ready': all_ready,
                'status': 'ready' if all_ready else 'not_ready',
                'failed_checks': failed_checks,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error checking readiness: {str(e)}")
            return {
                'ready': False,
                'status': 'error',
                'message': 'Failed to check readiness',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
    def get_component_health(self, component_id: str = None) -> Dict[str, ComponentHealth]:
        """Get health status of specific component or all components."""
        if component_id:
            if component_id in self.component_health:
                return {component_id: self.component_health[component_id]}
            else:
                return {}
        return self.component_health.copy()
        
    def get_health_trends(self, component_id: str, 
                         time_window: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """Get health trends for a component over time window."""
        if component_id not in self.health_history:
            return {'error': 'No history available for component'}
            
        cutoff_time = datetime.now(timezone.utc) - time_window
        history = self.health_history[component_id]
        
        # Filter history within time window
        recent_history = [
            record for record in history
            if record['timestamp'] > cutoff_time
        ]
        
        if not recent_history:
            return {'error': 'No data in specified time window'}
            
        # Calculate trends
        status_changes = len([
            r for i, r in enumerate(recent_history[1:], 1)
            if r['status'] != recent_history[i-1]['status']
        ])
        
        avg_response_time = sum(r['response_time_ms'] for r in recent_history) / len(recent_history)
        
        status_distribution = {}
        for record in recent_history:
            status = record['status'].value
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
        return {
            'time_window': str(time_window),
            'total_checks': len(recent_history),
            'status_changes': status_changes,
            'avg_response_time_ms': round(avg_response_time, 2),
            'status_distribution': status_distribution,
            'stability_score': 1.0 - (status_changes / len(recent_history)) if recent_history else 0.0
        }
        
    def register_health_change_callback(self, callback: Callable[[ComponentHealth], None]):
        """Register callback for health status changes."""
        self.health_change_callbacks.append(callback)
        
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active and not self.shutdown_event.is_set():
            try:
                start_time = time.time()
                
                # Perform all enabled health checks
                for check_id, health_check in self.health_checks.items():
                    if health_check.is_enabled:
                        # Check if it's time for this check
                        component_health = self.component_health[check_id]
                        time_since_last = (
                            datetime.now(timezone.utc) - component_health.last_check_time
                        ).total_seconds()
                        
                        if time_since_last >= health_check.interval_seconds:
                            self.perform_health_check(check_id)
                            
                # Calculate sleep time to maintain check interval
                loop_time = time.time() - start_time
                sleep_time = max(0, self.check_interval - loop_time)
                
                self.shutdown_event.wait(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                self.shutdown_event.wait(self.check_interval)
                
    def _check_database_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check database connectivity and performance."""
        try:
            # Simulate database health check
            start_time = time.time()
            
            # In a real implementation, this would:
            # - Test database connection
            # - Check connection pool status
            # - Verify critical tables exist
            # - Test basic query performance
            
            # Simulated check
            response_time = (time.time() - start_time) * 1000
            
            metadata = {
                'connection_pool_active': 10,
                'connection_pool_max': 20,
                'query_response_time_ms': response_time,
                'last_backup': '2025-11-09T12:00:00Z'
            }
            
            if response_time > 1000:  # > 1 second
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.CRITICAL, {'error': str(e)}
            
    def _check_redis_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check Redis cache service health."""
        try:
            # Simulate Redis health check
            metadata = {
                'memory_usage_mb': 256,
                'connected_clients': 15,
                'hit_rate': 0.94,
                'evicted_keys': 0
            }
            
            if metadata['hit_rate'] < 0.8:
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.CRITICAL, {'error': str(e)}
            
    def _check_payment_api_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check external payment API health."""
        try:
            # Simulate payment API health check
            # In real implementation, this would make a test API call
            
            start_time = time.time()
            
            # Simulate API response
            time.sleep(0.1)  # Simulate network latency
            response_time = (time.time() - start_time) * 1000
            
            metadata = {
                'api_version': 'v2.1',
                'response_time_ms': response_time,
                'rate_limit_remaining': 950,
                'last_successful_call': datetime.now(timezone.utc).isoformat()
            }
            
            if response_time > 5000:  # > 5 seconds
                return HealthStatus.UNHEALTHY, metadata
            elif response_time > 2000:  # > 2 seconds
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.CRITICAL, {'error': str(e)}
            
    def _check_market_data_api_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check market data API health."""
        try:
            # Simulate market data API check
            metadata = {
                'data_freshness_minutes': 2,
                'symbols_available': 5000,
                'last_update': datetime.now(timezone.utc).isoformat(),
                'api_status': 'operational'
            }
            
            if metadata['data_freshness_minutes'] > 15:
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.CRITICAL, {'error': str(e)}
            
    def _check_system_resources(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check system resource utilization."""
        try:
            # Get actual system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metadata = {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'available_memory_mb': memory.available // (1024 * 1024),
                'available_disk_gb': disk.free // (1024 * 1024 * 1024)
            }
            
            # Determine status based on resource usage
            if cpu_percent > 90 or memory.percent > 95 or metadata['disk_usage_percent'] > 95:
                return HealthStatus.CRITICAL, metadata
            elif cpu_percent > 75 or memory.percent > 85 or metadata['disk_usage_percent'] > 85:
                return HealthStatus.UNHEALTHY, metadata
            elif cpu_percent > 60 or memory.percent > 70 or metadata['disk_usage_percent'] > 70:
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.UNKNOWN, {'error': str(e)}
            
    def _check_file_system_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check file system health and disk space."""
        try:
            disk = psutil.disk_usage('/')
            
            # Check for write permissions
            test_file = '/tmp/treasury_health_check'
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                import os
                os.remove(test_file)
                write_test_passed = True
            except:
                write_test_passed = False
                
            metadata = {
                'total_disk_gb': disk.total // (1024 * 1024 * 1024),
                'free_disk_gb': disk.free // (1024 * 1024 * 1024),
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'write_test_passed': write_test_passed
            }
            
            if not write_test_passed or metadata['disk_usage_percent'] > 95:
                return HealthStatus.CRITICAL, metadata
            elif metadata['disk_usage_percent'] > 85:
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.CRITICAL, {'error': str(e)}
            
    def _check_network_connectivity(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check network connectivity and DNS resolution."""
        try:
            # Test DNS resolution
            socket.gethostbyname('google.com')
            
            # Test external connectivity (simulate)
            connectivity_tests = [
                {'host': 'google.com', 'port': 80, 'status': 'ok'},
                {'host': 'api.treasury-provider.com', 'port': 443, 'status': 'ok'}
            ]
            
            metadata = {
                'dns_resolution': 'ok',
                'connectivity_tests': connectivity_tests,
                'external_connectivity': 'ok'
            }
            
            return HealthStatus.HEALTHY, metadata
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, {'error': str(e)}
            
    def _check_security_service_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check security authentication service health."""
        try:
            # Simulate security service check
            metadata = {
                'auth_service_status': 'operational',
                'active_sessions': 145,
                'failed_logins_last_hour': 3,
                'security_alerts': 0
            }
            
            if metadata['failed_logins_last_hour'] > 100:
                return HealthStatus.DEGRADED, metadata
            else:
                return HealthStatus.HEALTHY, metadata
                
        except Exception as e:
            return HealthStatus.CRITICAL, {'error': str(e)}
            
    def _calculate_overall_health(self) -> HealthStatus:
        """Calculate overall system health based on component health."""
        if not self.component_health:
            return HealthStatus.UNKNOWN
            
        critical_count = 0
        unhealthy_count = 0
        degraded_count = 0
        healthy_count = 0
        
        for component_health in self.component_health.values():
            health_check = self.health_checks[component_health.component_id]
            
            if component_health.status == HealthStatus.CRITICAL:
                critical_count += 1
                # Critical components have higher weight
                if health_check.is_critical:
                    critical_count += 2
            elif component_health.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1
            elif component_health.status == HealthStatus.DEGRADED:
                degraded_count += 1
            elif component_health.status == HealthStatus.HEALTHY:
                healthy_count += 1
                
        # Determine overall status
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > healthy_count:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
            
    def _calculate_uptime_statistics(self) -> Dict[str, Any]:
        """Calculate system uptime statistics."""
        current_time = datetime.now(timezone.utc)
        
        # Calculate average uptime across components
        total_uptime = 0
        components_with_data = 0
        
        for component_id, component_health in self.component_health.items():
            if component_id in self.health_history:
                history = self.health_history[component_id]
                if history:
                    # Calculate uptime percentage based on health history
                    healthy_checks = len([
                        r for r in history
                        if r['status'] in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
                    ])
                    uptime_pct = (healthy_checks / len(history)) * 100 if history else 0
                    total_uptime += uptime_pct
                    components_with_data += 1
                    
        avg_uptime = total_uptime / components_with_data if components_with_data > 0 else 0
        
        return {
            'average_uptime_percentage': round(avg_uptime, 2),
            'components_tracked': components_with_data,
            'monitoring_duration_hours': 24,  # Simulate 24-hour monitoring
            'last_incident_time': None  # Would track actual incidents
        }
        
    def _update_success_rate(self, component_id: str, success: bool):
        """Update success rate for a component."""
        component_health = self.component_health[component_id]
        
        # Simple success rate calculation (could be more sophisticated)
        if hasattr(component_health, '_success_count'):
            component_health._success_count += 1 if success else 0
            component_health._total_count += 1
        else:
            component_health._success_count = 1 if success else 0
            component_health._total_count = 1
            
        component_health.success_rate = (
            component_health._success_count / component_health._total_count
        )
        
    def _add_to_history(self, component_id: str, status: HealthStatus,
                       response_time: float, metadata: Dict[str, Any]):
        """Add health check result to history."""
        if component_id not in self.health_history:
            self.health_history[component_id] = []
            
        history_record = {
            'timestamp': datetime.now(timezone.utc),
            'status': status,
            'response_time_ms': response_time,
            'metadata': metadata.copy()
        }
        
        self.health_history[component_id].append(history_record)
        
        # Keep only last 1000 records per component
        if len(self.health_history[component_id]) > 1000:
            self.health_history[component_id] = self.health_history[component_id][-1000:]
            
    def _notify_health_change(self, component_health: ComponentHealth):
        """Notify registered callbacks of health status changes."""
        for callback in self.health_change_callbacks:
            try:
                callback(component_health)
            except Exception as e:
                self.logger.error(f"Health change callback error: {e}")
                
    def _update_avg_response_time(self, response_time: float):
        """Update average response time statistics."""
        current_avg = self.health_statistics['avg_response_time']
        total_checks = self.health_statistics['total_checks_performed']
        
        if total_checks <= 1:
            self.health_statistics['avg_response_time'] = response_time
        else:
            # Update rolling average
            self.health_statistics['avg_response_time'] = (
                (current_avg * (total_checks - 1) + response_time) / total_checks
            )


# Global health monitor instance  
_health_monitor: HealthMonitor = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


def configure_default_health_checks() -> HealthMonitor:
    """Configure and return health monitor with default checks."""
    monitor = get_health_monitor()
    # The monitor already initializes with default treasury health checks
    return monitor