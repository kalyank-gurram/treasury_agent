"""Advanced Metrics Collection and Analysis System for Treasury Operations.

This module provides comprehensive metrics collection capabilities for monitoring
treasury operations, system performance, and business KPIs with real-time analytics.
"""

import asyncio
import time
import json
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import threading
import uuid


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"          # Monotonically increasing (e.g., total payments)
    GAUGE = "gauge"              # Current value (e.g., cash balance)
    HISTOGRAM = "histogram"      # Distribution of values (e.g., payment amounts)
    TIMER = "timer"              # Duration measurements (e.g., API response time)
    RATE = "rate"                # Events per time unit (e.g., transactions/sec)
    BUSINESS_KPI = "business_kpi" # Business key performance indicators


class MetricUnit(Enum):
    """Units of measurement for metrics."""
    COUNT = "count"
    PERCENTAGE = "percentage"
    MILLISECONDS = "ms"
    SECONDS = "s"
    MINUTES = "min"
    HOURS = "h"
    BYTES = "bytes"
    MEGABYTES = "mb"
    CURRENCY_USD = "usd"
    CURRENCY_EUR = "eur"
    RATIO = "ratio"
    BPS = "bps"  # Basis points


@dataclass
class MetricValue:
    """Represents a single metric measurement."""
    name: str
    value: Union[float, int]
    metric_type: MetricType
    unit: MetricUnit
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricAggregation:
    """Aggregated metric statistics over time."""
    name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    p99_value: float
    sum_value: float
    std_dev: float
    time_window: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricBuffer:
    """Thread-safe circular buffer for metric values."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
        
    def add(self, metric: MetricValue):
        """Add a metric to the buffer."""
        with self.lock:
            self.buffer.append(metric)
            
    def get_recent(self, count: int = None) -> List[MetricValue]:
        """Get recent metrics from buffer."""
        with self.lock:
            if count is None:
                return list(self.buffer)
            return list(self.buffer)[-count:]
            
    def get_in_range(self, start_time: datetime, end_time: datetime) -> List[MetricValue]:
        """Get metrics within time range."""
        with self.lock:
            return [
                metric for metric in self.buffer 
                if start_time <= metric.timestamp <= end_time
            ]
            
    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.buffer.clear()


class MetricsCollector:
    """Advanced metrics collection system for treasury operations."""
    
    def __init__(self, buffer_size: int = 50000, 
                 enable_real_time_alerts: bool = True):
        self.buffer_size = buffer_size
        self.enable_real_time_alerts = enable_real_time_alerts
        
        # Metric storage
        self.metric_buffers: Dict[str, MetricBuffer] = defaultdict(
            lambda: MetricBuffer(buffer_size)
        )
        
        # Aggregation caches
        self.aggregation_cache: Dict[str, MetricAggregation] = {}
        self.cache_ttl = timedelta(minutes=5)  # Cache TTL
        
        # Real-time monitoring
        self.alert_thresholds: Dict[str, Dict[str, Any]] = {}
        self.metric_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Performance tracking
        self.collection_stats = {
            'metrics_collected': 0,
            'collection_errors': 0,
            'last_collection_time': None,
            'avg_collection_latency': 0.0
        }
        
        # Treasury-specific metric definitions
        self.treasury_metrics = self._initialize_treasury_metrics()
        
        self.logger = logging.getLogger(__name__)
        
    def _initialize_treasury_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize treasury-specific metric definitions."""
        return {
            # Cash Management Metrics
            'cash_balance_total': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.CURRENCY_USD,
                'description': 'Total cash balance across all accounts',
                'alert_threshold': {'min': 1000000, 'max': None}  # Min $1M
            },
            'daily_cash_flow': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.CURRENCY_USD,
                'description': 'Net daily cash flow',
                'alert_threshold': {'min': -5000000, 'max': None}  # Alert if outflow > $5M
            },
            'working_capital_ratio': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.RATIO,
                'description': 'Working capital ratio',
                'alert_threshold': {'min': 1.2, 'max': None}  # Min 1.2 ratio
            },
            
            # Payment Processing Metrics
            'payments_processed_count': {
                'type': MetricType.COUNTER,
                'unit': MetricUnit.COUNT,
                'description': 'Total number of payments processed'
            },
            'payment_processing_time': {
                'type': MetricType.TIMER,
                'unit': MetricUnit.MILLISECONDS,
                'description': 'Time to process payment requests',
                'alert_threshold': {'max': 5000}  # Alert if > 5 seconds
            },
            'payment_failure_rate': {
                'type': MetricType.RATE,
                'unit': MetricUnit.PERCENTAGE,
                'description': 'Percentage of failed payments',
                'alert_threshold': {'max': 0.05}  # Alert if > 5% failure rate
            },
            'large_payment_count': {
                'type': MetricType.COUNTER,
                'unit': MetricUnit.COUNT,
                'description': 'Count of payments > $1M',
                'alert_threshold': {'rate_limit': 10}  # Alert if > 10 per hour
            },
            
            # Investment Metrics
            'portfolio_value': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.CURRENCY_USD,
                'description': 'Total investment portfolio value'
            },
            'investment_yield': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.PERCENTAGE,
                'description': 'Current portfolio yield',
                'alert_threshold': {'min': 0.02}  # Alert if yield < 2%
            },
            'investment_risk_score': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.RATIO,
                'description': 'Portfolio risk score (0-1)',
                'alert_threshold': {'max': 0.8}  # Alert if risk > 0.8
            },
            
            # System Performance Metrics
            'api_response_time': {
                'type': MetricType.TIMER,
                'unit': MetricUnit.MILLISECONDS,
                'description': 'API endpoint response times',
                'alert_threshold': {'max': 1000}  # Alert if > 1 second
            },
            'database_connection_pool': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.COUNT,
                'description': 'Active database connections',
                'alert_threshold': {'max': 80}  # Alert if > 80% pool usage
            },
            'system_cpu_usage': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.PERCENTAGE,
                'description': 'System CPU utilization',
                'alert_threshold': {'max': 0.85}  # Alert if > 85%
            },
            'system_memory_usage': {
                'type': MetricType.GAUGE,
                'unit': MetricUnit.PERCENTAGE,
                'description': 'System memory utilization',
                'alert_threshold': {'max': 0.90}  # Alert if > 90%
            },
            
            # Security Metrics
            'authentication_attempts': {
                'type': MetricType.COUNTER,
                'unit': MetricUnit.COUNT,
                'description': 'Total authentication attempts'
            },
            'failed_login_rate': {
                'type': MetricType.RATE,
                'unit': MetricUnit.PERCENTAGE,
                'description': 'Failed login attempt rate',
                'alert_threshold': {'max': 0.10}  # Alert if > 10% failure rate
            },
            'security_violations': {
                'type': MetricType.COUNTER,
                'unit': MetricUnit.COUNT,
                'description': 'Security violations detected',
                'alert_threshold': {'rate_limit': 1}  # Alert on any violation
            },
            
            # Compliance Metrics
            'compliance_check_failures': {
                'type': MetricType.COUNTER,
                'unit': MetricUnit.COUNT,
                'description': 'Failed compliance checks',
                'alert_threshold': {'rate_limit': 0}  # Alert on any failure
            },
            'audit_events_logged': {
                'type': MetricType.COUNTER,
                'unit': MetricUnit.COUNT,
                'description': 'Total audit events logged'
            },
            'regulatory_report_generation_time': {
                'type': MetricType.TIMER,
                'unit': MetricUnit.SECONDS,
                'description': 'Time to generate regulatory reports',
                'alert_threshold': {'max': 300}  # Alert if > 5 minutes
            }
        }
        
    def record_metric(self, name: str, value: Union[float, int],
                     metric_type: MetricType = None, unit: MetricUnit = None,
                     tags: Dict[str, str] = None, metadata: Dict[str, Any] = None) -> str:
        """Record a single metric measurement."""
        start_time = time.time()
        
        try:
            # Use predefined metric config if available
            if name in self.treasury_metrics:
                config = self.treasury_metrics[name]
                metric_type = metric_type or config['type']
                unit = unit or config['unit']
                
            # Create metric value
            metric = MetricValue(
                name=name,
                value=value,
                metric_type=metric_type or MetricType.GAUGE,
                unit=unit or MetricUnit.COUNT,
                tags=tags or {},
                metadata=metadata or {}
            )
            
            # Store in buffer
            self.metric_buffers[name].add(metric)
            
            # Check for real-time alerts
            if self.enable_real_time_alerts:
                self._check_alert_thresholds(metric)
                
            # Execute registered callbacks
            for callback in self.metric_callbacks.get(name, []):
                try:
                    callback(metric)
                except Exception as e:
                    self.logger.error(f"Metric callback error: {e}")
                    
            # Update collection stats
            self.collection_stats['metrics_collected'] += 1
            self.collection_stats['last_collection_time'] = datetime.now(timezone.utc)
            
            collection_time = time.time() - start_time
            self._update_avg_latency(collection_time)
            
            return metric.name
            
        except Exception as e:
            self.collection_stats['collection_errors'] += 1
            self.logger.error(f"Failed to record metric {name}: {e}")
            raise
            
    def record_treasury_cash_balance(self, account_id: str, balance: float, 
                                   currency: str = "USD") -> str:
        """Record treasury cash balance for specific account."""
        return self.record_metric(
            name='cash_balance_total',
            value=balance,
            tags={'account_id': account_id, 'currency': currency},
            metadata={'measurement_type': 'end_of_day_balance'}
        )
        
    def record_payment_processing(self, payment_id: str, amount: float,
                                processing_time_ms: float, success: bool) -> List[str]:
        """Record payment processing metrics."""
        metrics_recorded = []
        
        # Payment count
        metrics_recorded.append(
            self.record_metric('payments_processed_count', 1, MetricType.COUNTER)
        )
        
        # Processing time
        metrics_recorded.append(
            self.record_metric(
                'payment_processing_time',
                processing_time_ms,
                tags={'payment_id': payment_id, 'success': str(success)}
            )
        )
        
        # Large payment tracking
        if amount >= 1000000:  # $1M+
            metrics_recorded.append(
                self.record_metric(
                    'large_payment_count',
                    1,
                    MetricType.COUNTER,
                    tags={'amount_tier': 'large', 'success': str(success)}
                )
            )
            
        # Failure tracking
        if not success:
            failure_rate = self._calculate_payment_failure_rate()
            metrics_recorded.append(
                self.record_metric('payment_failure_rate', failure_rate)
            )
            
        return metrics_recorded
        
    def record_investment_metrics(self, portfolio_value: float, yield_rate: float,
                                risk_score: float) -> List[str]:
        """Record investment portfolio metrics."""
        return [
            self.record_metric('portfolio_value', portfolio_value),
            self.record_metric('investment_yield', yield_rate),
            self.record_metric('investment_risk_score', risk_score)
        ]
        
    def record_system_performance(self, endpoint: str, response_time_ms: float,
                                cpu_usage: float, memory_usage: float) -> List[str]:
        """Record system performance metrics."""
        return [
            self.record_metric(
                'api_response_time',
                response_time_ms,
                tags={'endpoint': endpoint}
            ),
            self.record_metric('system_cpu_usage', cpu_usage),
            self.record_metric('system_memory_usage', memory_usage)
        ]
        
    def get_metric_aggregation(self, metric_name: str, 
                             time_window: timedelta = timedelta(hours=1),
                             force_refresh: bool = False) -> Optional[MetricAggregation]:
        """Get aggregated statistics for a metric over specified time window."""
        cache_key = f"{metric_name}_{time_window.total_seconds()}"
        
        # Check cache first
        if not force_refresh and cache_key in self.aggregation_cache:
            cached = self.aggregation_cache[cache_key]
            if datetime.now(timezone.utc) - cached.timestamp < self.cache_ttl:
                return cached
                
        # Calculate aggregation
        end_time = datetime.now(timezone.utc)
        start_time = end_time - time_window
        
        metrics = self.metric_buffers[metric_name].get_in_range(start_time, end_time)
        
        if not metrics:
            return None
            
        values = [m.value for m in metrics]
        
        if not values:
            return None
            
        # Calculate statistics
        aggregation = MetricAggregation(
            name=metric_name,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            median_value=statistics.median(values),
            p95_value=self._percentile(values, 0.95),
            p99_value=self._percentile(values, 0.99),
            sum_value=sum(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            time_window=str(time_window)
        )
        
        # Cache result
        self.aggregation_cache[cache_key] = aggregation
        
        return aggregation
        
    def get_real_time_metrics(self, metric_names: List[str] = None,
                            last_n_minutes: int = 5) -> Dict[str, List[MetricValue]]:
        """Get real-time metrics for specified metrics."""
        if metric_names is None:
            metric_names = list(self.metric_buffers.keys())
            
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=last_n_minutes)
        
        real_time_data = {}
        for metric_name in metric_names:
            if metric_name in self.metric_buffers:
                recent_metrics = self.metric_buffers[metric_name].get_recent(1000)
                real_time_data[metric_name] = [
                    m for m in recent_metrics if m.timestamp >= cutoff_time
                ]
                
        return real_time_data
        
    def get_treasury_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for treasury operations."""
        dashboard_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cash_management': {},
            'payments': {},
            'investments': {},
            'system_health': {},
            'security': {},
            'compliance': {}
        }
        
        # Cash management metrics
        cash_metrics = ['cash_balance_total', 'daily_cash_flow', 'working_capital_ratio']
        for metric in cash_metrics:
            agg = self.get_metric_aggregation(metric, timedelta(hours=24))
            if agg:
                dashboard_data['cash_management'][metric] = {
                    'current': agg.avg_value,
                    'min_24h': agg.min_value,
                    'max_24h': agg.max_value,
                    'trend': self._calculate_trend(metric)
                }
                
        # Payment metrics
        payment_metrics = ['payments_processed_count', 'payment_processing_time', 'payment_failure_rate']
        for metric in payment_metrics:
            agg = self.get_metric_aggregation(metric, timedelta(hours=1))
            if agg:
                dashboard_data['payments'][metric] = {
                    'current': agg.avg_value,
                    'hourly_avg': agg.avg_value,
                    'p95': agg.p95_value
                }
                
        # Investment metrics
        investment_metrics = ['portfolio_value', 'investment_yield', 'investment_risk_score']
        for metric in investment_metrics:
            agg = self.get_metric_aggregation(metric, timedelta(hours=24))
            if agg:
                dashboard_data['investments'][metric] = {
                    'current': agg.avg_value,
                    'daily_change': self._calculate_change(metric)
                }
                
        # System health
        system_metrics = ['api_response_time', 'system_cpu_usage', 'system_memory_usage']
        for metric in system_metrics:
            agg = self.get_metric_aggregation(metric, timedelta(minutes=15))
            if agg:
                dashboard_data['system_health'][metric] = {
                    'current': agg.avg_value,
                    'status': self._get_health_status(metric, agg.avg_value)
                }
                
        return dashboard_data
        
    def register_metric_callback(self, metric_name: str, callback: Callable[[MetricValue], None]):
        """Register callback function for specific metric updates."""
        self.metric_callbacks[metric_name].append(callback)
        
    def set_alert_threshold(self, metric_name: str, threshold_config: Dict[str, Any]):
        """Set custom alert threshold for a metric."""
        self.alert_thresholds[metric_name] = threshold_config
        
    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get metrics collection performance statistics."""
        return {
            **self.collection_stats,
            'active_metrics': len(self.metric_buffers),
            'total_data_points': sum(
                len(buffer.buffer) for buffer in self.metric_buffers.values()
            ),
            'cache_size': len(self.aggregation_cache),
            'memory_usage_estimate': self._estimate_memory_usage()
        }
        
    def _check_alert_thresholds(self, metric: MetricValue):
        """Check if metric value exceeds alert thresholds."""
        thresholds = self.alert_thresholds.get(
            metric.name,
            self.treasury_metrics.get(metric.name, {}).get('alert_threshold')
        )
        
        if not thresholds:
            return
            
        alerts_triggered = []
        
        # Min/Max threshold checks
        if 'min' in thresholds and thresholds['min'] is not None:
            if metric.value < thresholds['min']:
                alerts_triggered.append(f"Below minimum threshold: {metric.value} < {thresholds['min']}")
                
        if 'max' in thresholds and thresholds['max'] is not None:
            if metric.value > thresholds['max']:
                alerts_triggered.append(f"Above maximum threshold: {metric.value} > {thresholds['max']}")
                
        # Rate limit checks
        if 'rate_limit' in thresholds:
            rate = self._calculate_metric_rate(metric.name, timedelta(hours=1))
            if rate > thresholds['rate_limit']:
                alerts_triggered.append(f"Rate limit exceeded: {rate}/hour > {thresholds['rate_limit']}/hour")
                
        # Log alerts (in production, this would integrate with AlertManager)
        for alert_msg in alerts_triggered:
            self.logger.warning(f"ALERT - {metric.name}: {alert_msg}")
            
    def _calculate_payment_failure_rate(self) -> float:
        """Calculate payment failure rate over last hour."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        processing_metrics = self.metric_buffers['payment_processing_time'].get_in_range(start_time, end_time)
        
        if not processing_metrics:
            return 0.0
            
        failed_count = sum(1 for m in processing_metrics if m.tags.get('success') == 'False')
        total_count = len(processing_metrics)
        
        return (failed_count / total_count) if total_count > 0 else 0.0
        
    def _calculate_metric_rate(self, metric_name: str, time_window: timedelta) -> float:
        """Calculate rate of metric occurrences over time window."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - time_window
        
        metrics = self.metric_buffers[metric_name].get_in_range(start_time, end_time)
        
        if metrics and metrics[0].metric_type == MetricType.COUNTER:
            return len(metrics) / time_window.total_seconds() * 3600  # Rate per hour
            
        return 0.0
        
    def _calculate_trend(self, metric_name: str) -> str:
        """Calculate trend direction for metric."""
        recent_agg = self.get_metric_aggregation(metric_name, timedelta(hours=2))
        older_agg = self.get_metric_aggregation(metric_name, timedelta(hours=4))
        
        if not recent_agg or not older_agg:
            return "insufficient_data"
            
        if recent_agg.avg_value > older_agg.avg_value * 1.05:
            return "increasing"
        elif recent_agg.avg_value < older_agg.avg_value * 0.95:
            return "decreasing"
        else:
            return "stable"
            
    def _calculate_change(self, metric_name: str) -> float:
        """Calculate percentage change for metric."""
        current_agg = self.get_metric_aggregation(metric_name, timedelta(hours=1))
        previous_agg = self.get_metric_aggregation(metric_name, timedelta(hours=25))  # Previous day
        
        if not current_agg or not previous_agg or previous_agg.avg_value == 0:
            return 0.0
            
        return ((current_agg.avg_value - previous_agg.avg_value) / previous_agg.avg_value) * 100
        
    def _get_health_status(self, metric_name: str, current_value: float) -> str:
        """Determine health status based on metric value."""
        thresholds = self.treasury_metrics.get(metric_name, {}).get('alert_threshold', {})
        
        if 'max' in thresholds and thresholds['max'] is not None:
            if current_value > thresholds['max']:
                return "critical"
            elif current_value > thresholds['max'] * 0.8:
                return "warning"
                
        if 'min' in thresholds and thresholds['min'] is not None:
            if current_value < thresholds['min']:
                return "critical"
            elif current_value < thresholds['min'] * 1.2:
                return "warning"
                
        return "healthy"
        
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
        
    def _update_avg_latency(self, new_latency: float):
        """Update rolling average collection latency."""
        current_avg = self.collection_stats['avg_collection_latency']
        count = self.collection_stats['metrics_collected']
        
        if count <= 1:
            self.collection_stats['avg_collection_latency'] = new_latency
        else:
            # Exponential moving average
            alpha = 0.1  # Smoothing factor
            self.collection_stats['avg_collection_latency'] = (
                alpha * new_latency + (1 - alpha) * current_avg
            )
            
    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of metrics system."""
        total_metrics = sum(len(buffer.buffer) for buffer in self.metric_buffers.values())
        # Rough estimate: 500 bytes per metric
        estimated_bytes = total_metrics * 500
        
        if estimated_bytes > 1024 * 1024:  # MB
            return f"{estimated_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{estimated_bytes / 1024:.1f} KB"