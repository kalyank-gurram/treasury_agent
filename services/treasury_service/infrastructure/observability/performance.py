"""Performance Profiling and Optimization for Treasury Operations.

This module provides detailed performance analysis, bottleneck detection,
and optimization recommendations for treasury system components.
"""

import time
import functools
import threading
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import json


class PerformanceMetricType(Enum):
    """Types of performance metrics that can be collected."""
    EXECUTION_TIME = "execution_time"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DATABASE_QUERY_TIME = "database_query_time"
    API_RESPONSE_TIME = "api_response_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceMetric:
    """Represents a single performance measurement."""
    metric_id: str
    metric_type: PerformanceMetricType
    component: str
    operation: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context and metadata
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance context
    concurrent_operations: int = 1
    data_size: Optional[int] = None  # bytes
    user_count: Optional[int] = None


@dataclass
class PerformanceProfile:
    """Performance profile for a specific component or operation."""
    component: str
    operation: str
    
    # Statistical measures
    total_executions: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    median_time_ms: float = 0.0
    p95_time_ms: float = 0.0
    p99_time_ms: float = 0.0
    
    # Performance trends
    recent_executions: deque = field(default_factory=lambda: deque(maxlen=1000))
    trend_direction: str = "stable"  # improving, degrading, stable
    
    # Optimization insights
    bottlenecks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    optimization_opportunities: Dict[str, Any] = field(default_factory=dict)
    
    # Comparison metrics
    baseline_performance: Optional[float] = None
    performance_regression: bool = False
    
    def update_with_metric(self, metric: PerformanceMetric):
        """Update profile with new performance metric."""
        self.total_executions += 1
        self.total_time_ms += metric.value
        self.min_time_ms = min(self.min_time_ms, metric.value)
        self.max_time_ms = max(self.max_time_ms, metric.value)
        self.avg_time_ms = self.total_time_ms / self.total_executions
        
        # Add to recent executions for trend analysis
        self.recent_executions.append({
            'timestamp': metric.timestamp,
            'value': metric.value,
            'metadata': metric.metadata
        })
        
        # Update percentiles
        if len(self.recent_executions) > 10:
            values = [ex['value'] for ex in self.recent_executions]
            self.median_time_ms = statistics.median(values)
            self.p95_time_ms = self._percentile(values, 0.95)
            self.p99_time_ms = self._percentile(values, 0.99)
            
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


class PerformanceProfiler:
    """Advanced performance profiling system for treasury operations."""
    
    def __init__(self, enable_auto_analysis: bool = True):
        self.enable_auto_analysis = enable_auto_analysis
        
        # Performance data storage
        self.performance_metrics: deque = deque(maxlen=100000)
        self.performance_profiles: Dict[str, PerformanceProfile] = {}
        
        # Real-time monitoring
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.operation_lock = threading.RLock()
        
        # Analysis and optimization
        self.performance_thresholds = self._initialize_performance_thresholds()
        self.optimization_rules = self._initialize_optimization_rules()
        
        # Statistics and reporting
        self.profiler_stats = {
            'total_measurements': 0,
            'active_profiles': 0,
            'performance_alerts': 0,
            'optimization_recommendations': 0
        }
        
        # Treasury-specific performance tracking
        self.treasury_operations = [
            'payment_processing',
            'cash_flow_calculation',
            'investment_valuation',
            'risk_assessment',
            'compliance_check',
            'report_generation',
            'database_query',
            'api_call'
        ]
        
        self.logger = logging.getLogger(__name__)
        
    def _initialize_performance_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance thresholds for treasury operations."""
        return {
            'payment_processing': {
                'target_ms': 500,
                'warning_ms': 1000,
                'critical_ms': 5000,
                'target_throughput_per_sec': 100
            },
            'cash_flow_calculation': {
                'target_ms': 200,
                'warning_ms': 500,
                'critical_ms': 2000,
                'target_throughput_per_sec': 50
            },
            'investment_valuation': {
                'target_ms': 1000,
                'warning_ms': 3000,
                'critical_ms': 10000,
                'target_throughput_per_sec': 20
            },
            'risk_assessment': {
                'target_ms': 800,
                'warning_ms': 2000,
                'critical_ms': 8000,
                'target_throughput_per_sec': 25
            },
            'compliance_check': {
                'target_ms': 300,
                'warning_ms': 1000,
                'critical_ms': 5000,
                'target_throughput_per_sec': 75
            },
            'report_generation': {
                'target_ms': 5000,
                'warning_ms': 15000,
                'critical_ms': 30000,
                'target_throughput_per_sec': 5
            },
            'database_query': {
                'target_ms': 50,
                'warning_ms': 200,
                'critical_ms': 1000,
                'target_throughput_per_sec': 500
            },
            'api_call': {
                'target_ms': 300,
                'warning_ms': 1000,
                'critical_ms': 5000,
                'target_throughput_per_sec': 200
            }
        }
        
    def _initialize_optimization_rules(self) -> List[Dict[str, Any]]:
        """Initialize optimization rules and recommendations."""
        return [
            {
                'condition': 'high_database_query_time',
                'threshold': 'avg_time_ms > 200',
                'recommendation': 'Consider adding database indexes or query optimization',
                'impact': 'high'
            },
            {
                'condition': 'high_api_response_time',
                'threshold': 'p95_time_ms > 2000',
                'recommendation': 'Implement response caching or API connection pooling',
                'impact': 'medium'
            },
            {
                'condition': 'payment_processing_bottleneck',
                'threshold': 'avg_time_ms > 1000 AND concurrent_operations > 10',
                'recommendation': 'Implement asynchronous payment processing queue',
                'impact': 'high'
            },
            {
                'condition': 'memory_intensive_operation',
                'threshold': 'memory_usage > 1GB',
                'recommendation': 'Implement data streaming or pagination for large datasets',
                'impact': 'medium'
            },
            {
                'condition': 'frequent_compliance_checks',
                'threshold': 'executions_per_hour > 1000',
                'recommendation': 'Cache compliance rule results with TTL',
                'impact': 'medium'
            }
        ]
        
    def start_operation_timing(self, component: str, operation: str, 
                             metadata: Dict[str, Any] = None) -> str:
        """Start timing an operation."""
        operation_id = f"{component}:{operation}:{int(time.time() * 1000000)}"
        
        with self.operation_lock:
            self.active_operations[operation_id] = {
                'component': component,
                'operation': operation,
                'start_time': time.time(),
                'metadata': metadata or {},
                'thread_id': threading.get_ident()
            }
            
        return operation_id
        
    def end_operation_timing(self, operation_id: str, 
                           additional_metadata: Dict[str, Any] = None) -> Optional[PerformanceMetric]:
        """End timing an operation and record performance metric."""
        with self.operation_lock:
            if operation_id not in self.active_operations:
                self.logger.warning(f"Operation {operation_id} not found in active operations")
                return None
                
            operation_data = self.active_operations.pop(operation_id)
            
        # Calculate execution time
        execution_time_ms = (time.time() - operation_data['start_time']) * 1000
        
        # Merge metadata
        metadata = operation_data['metadata']
        if additional_metadata:
            metadata.update(additional_metadata)
            
        # Create performance metric
        metric = PerformanceMetric(
            metric_id=operation_id,
            metric_type=PerformanceMetricType.EXECUTION_TIME,
            component=operation_data['component'],
            operation=operation_data['operation'],
            value=execution_time_ms,
            unit='milliseconds',
            metadata=metadata
        )
        
        # Record the metric
        self.record_performance_metric(metric)
        
        return metric
        
    def record_performance_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        # Store metric
        self.performance_metrics.append(metric)
        
        # Update performance profile
        profile_key = f"{metric.component}:{metric.operation}"
        if profile_key not in self.performance_profiles:
            self.performance_profiles[profile_key] = PerformanceProfile(
                component=metric.component,
                operation=metric.operation
            )
            
        profile = self.performance_profiles[profile_key]
        profile.update_with_metric(metric)
        
        # Analyze performance if enabled
        if self.enable_auto_analysis:
            self._analyze_performance(profile, metric)
            
        # Update statistics
        self.profiler_stats['total_measurements'] += 1
        self.profiler_stats['active_profiles'] = len(self.performance_profiles)
        
        self.logger.debug(f"Recorded performance metric: {metric.component}:{metric.operation} = {metric.value:.2f}ms")
        
    def profile_function(self, component: str, operation: str = None):
        """Decorator to profile function performance."""
        def decorator(func):
            nonlocal operation
            if operation is None:
                operation = func.__name__
                
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                operation_id = self.start_operation_timing(
                    component=component,
                    operation=operation,
                    metadata={
                        'function_name': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
                try:
                    result = func(*args, **kwargs)
                    self.end_operation_timing(operation_id, {'success': True})
                    return result
                except Exception as e:
                    self.end_operation_timing(operation_id, {
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    raise
                    
            return wrapper
        return decorator
        
    def get_performance_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        cutoff_time = datetime.now(timezone.utc) - time_window
        
        # Filter recent metrics
        recent_metrics = [
            m for m in self.performance_metrics
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'time_window': str(time_window),
                'total_operations': 0,
                'message': 'No performance data available for specified time window'
            }
            
        # Calculate summary statistics
        total_operations = len(recent_metrics)
        avg_response_time = statistics.mean(m.value for m in recent_metrics)
        
        # Group by component and operation
        component_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'operations': set()})
        
        for metric in recent_metrics:
            key = metric.component
            component_stats[key]['count'] += 1
            component_stats[key]['total_time'] += metric.value
            component_stats[key]['operations'].add(metric.operation)
            
        # Format component statistics
        component_summary = {}
        for component, stats in component_stats.items():
            component_summary[component] = {
                'operation_count': stats['count'],
                'avg_response_time_ms': stats['total_time'] / stats['count'],
                'unique_operations': len(stats['operations']),
                'operations': list(stats['operations'])
            }
            
        # Identify performance issues
        performance_issues = self._identify_performance_issues(recent_metrics)
        
        # Get top slowest operations
        slowest_operations = sorted(recent_metrics, key=lambda x: x.value, reverse=True)[:10]
        
        return {
            'time_window': str(time_window),
            'summary_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_operations': total_operations,
            'avg_response_time_ms': round(avg_response_time, 2),
            'component_breakdown': component_summary,
            'performance_issues': performance_issues,
            'slowest_operations': [
                {
                    'component': op.component,
                    'operation': op.operation,
                    'response_time_ms': op.value,
                    'timestamp': op.timestamp.isoformat()
                }
                for op in slowest_operations
            ],
            'profiler_statistics': self.profiler_stats
        }
        
    def get_component_performance_profile(self, component: str, operation: str = None) -> Dict[str, Any]:
        """Get detailed performance profile for a component or specific operation."""
        if operation:
            profile_key = f"{component}:{operation}"
            if profile_key not in self.performance_profiles:
                return {'error': f'No performance data for {component}:{operation}'}
                
            profile = self.performance_profiles[profile_key]
            
            return {
                'component': component,
                'operation': operation,
                'statistics': {
                    'total_executions': profile.total_executions,
                    'avg_time_ms': round(profile.avg_time_ms, 2),
                    'min_time_ms': round(profile.min_time_ms, 2),
                    'max_time_ms': round(profile.max_time_ms, 2),
                    'median_time_ms': round(profile.median_time_ms, 2),
                    'p95_time_ms': round(profile.p95_time_ms, 2),
                    'p99_time_ms': round(profile.p99_time_ms, 2)
                },
                'performance_analysis': {
                    'trend_direction': profile.trend_direction,
                    'bottlenecks': profile.bottlenecks,
                    'recommendations': profile.recommendations,
                    'performance_regression': profile.performance_regression
                },
                'thresholds': self.performance_thresholds.get(operation, {}),
                'optimization_opportunities': profile.optimization_opportunities
            }
        else:
            # Get all operations for the component
            component_profiles = {
                key: profile for key, profile in self.performance_profiles.items()
                if key.startswith(f"{component}:")
            }
            
            return {
                'component': component,
                'operations': list(set(key.split(':')[1] for key in component_profiles.keys())),
                'total_profiles': len(component_profiles),
                'aggregate_statistics': self._calculate_aggregate_statistics(component_profiles)
            }
            
    def get_optimization_recommendations(self, component: str = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance analysis."""
        recommendations = []
        
        profiles_to_analyze = self.performance_profiles
        if component:
            profiles_to_analyze = {
                k: v for k, v in self.performance_profiles.items()
                if k.startswith(f"{component}:")
            }
            
        for profile_key, profile in profiles_to_analyze.items():
            component_name, operation = profile_key.split(':', 1)
            
            # Check against performance thresholds
            thresholds = self.performance_thresholds.get(operation, {})
            
            if thresholds:
                if profile.avg_time_ms > thresholds.get('critical_ms', float('inf')):
                    recommendations.append({
                        'component': component_name,
                        'operation': operation,
                        'priority': 'critical',
                        'issue': f'Average response time ({profile.avg_time_ms:.1f}ms) exceeds critical threshold',
                        'recommendation': f'Immediate optimization required - target: {thresholds.get("target_ms")}ms',
                        'current_performance': profile.avg_time_ms,
                        'target_performance': thresholds.get('target_ms')
                    })
                elif profile.avg_time_ms > thresholds.get('warning_ms', float('inf')):
                    recommendations.append({
                        'component': component_name,
                        'operation': operation,
                        'priority': 'high',
                        'issue': f'Average response time ({profile.avg_time_ms:.1f}ms) exceeds warning threshold',
                        'recommendation': f'Performance optimization recommended - target: {thresholds.get("target_ms")}ms',
                        'current_performance': profile.avg_time_ms,
                        'target_performance': thresholds.get('target_ms')
                    })
                    
            # Add existing recommendations from profile
            for rec in profile.recommendations:
                recommendations.append({
                    'component': component_name,
                    'operation': operation,
                    'priority': 'medium',
                    'issue': 'Performance analysis',
                    'recommendation': rec,
                    'current_performance': profile.avg_time_ms
                })
                
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return recommendations
        
    def generate_performance_report(self, time_window: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        cutoff_time = datetime.now(timezone.utc) - time_window
        
        # Get performance summary
        summary = self.get_performance_summary(time_window)
        
        # Get optimization recommendations
        recommendations = self.get_optimization_recommendations()
        
        # Calculate performance trends
        trends = self._calculate_performance_trends(cutoff_time)
        
        # Identify top performers and problem areas
        top_performers = []
        problem_areas = []
        
        for profile_key, profile in self.performance_profiles.items():
            component, operation = profile_key.split(':', 1)
            thresholds = self.performance_thresholds.get(operation, {})
            
            if thresholds and 'target_ms' in thresholds:
                if profile.avg_time_ms <= thresholds['target_ms']:
                    top_performers.append({
                        'component': component,
                        'operation': operation,
                        'performance': profile.avg_time_ms,
                        'target': thresholds['target_ms']
                    })
                elif profile.avg_time_ms > thresholds.get('warning_ms', float('inf')):
                    problem_areas.append({
                        'component': component,
                        'operation': operation,
                        'performance': profile.avg_time_ms,
                        'target': thresholds['target_ms']
                    })
                    
        return {
            'report_generated_at': datetime.now(timezone.utc).isoformat(),
            'time_window': str(time_window),
            'executive_summary': {
                'total_operations_analyzed': summary['total_operations'],
                'avg_system_response_time_ms': summary.get('avg_response_time_ms', 0),
                'components_monitored': len(summary.get('component_breakdown', {})),
                'performance_issues_identified': len(summary.get('performance_issues', [])),
                'optimization_recommendations': len(recommendations)
            },
            'performance_summary': summary,
            'performance_trends': trends,
            'top_performing_operations': top_performers[:10],
            'problem_areas': problem_areas,
            'optimization_recommendations': recommendations[:15],
            'system_health_indicators': {
                'operations_meeting_sla': len(top_performers),
                'operations_exceeding_thresholds': len(problem_areas),
                'performance_regression_detected': any(
                    p.performance_regression for p in self.performance_profiles.values()
                )
            }
        }
        
    def _analyze_performance(self, profile: PerformanceProfile, metric: PerformanceMetric):
        """Analyze performance and generate recommendations."""
        # Check for performance regression
        if profile.baseline_performance and profile.avg_time_ms > profile.baseline_performance * 1.5:
            profile.performance_regression = True
            
        # Identify bottlenecks
        thresholds = self.performance_thresholds.get(metric.operation, {})
        
        if thresholds:
            if metric.value > thresholds.get('critical_ms', float('inf')):
                if 'critical_performance' not in profile.bottlenecks:
                    profile.bottlenecks.append('critical_performance')
                    
        # Generate recommendations based on operation type and performance
        self._generate_optimization_recommendations(profile, metric)
        
    def _generate_optimization_recommendations(self, profile: PerformanceProfile, metric: PerformanceMetric):
        """Generate specific optimization recommendations."""
        recommendations = []
        
        # Database operation optimizations
        if metric.operation == 'database_query' and metric.value > 200:
            recommendations.append("Consider adding database indexes or optimizing query structure")
            
        # API call optimizations
        elif metric.operation == 'api_call' and metric.value > 1000:
            recommendations.append("Implement connection pooling and response caching")
            
        # Payment processing optimizations
        elif metric.operation == 'payment_processing' and metric.value > 500:
            recommendations.append("Consider asynchronous processing for payment workflows")
            
        # Report generation optimizations
        elif metric.operation == 'report_generation' and metric.value > 10000:
            recommendations.append("Implement incremental report generation and caching")
            
        # Add recommendations to profile (avoid duplicates)
        for rec in recommendations:
            if rec not in profile.recommendations:
                profile.recommendations.append(rec)
                
    def _identify_performance_issues(self, metrics: List[PerformanceMetric]) -> List[Dict[str, Any]]:
        """Identify performance issues from recent metrics."""
        issues = []
        
        # Group metrics by operation
        operation_metrics = defaultdict(list)
        for metric in metrics:
            operation_metrics[metric.operation].append(metric)
            
        # Check each operation against thresholds
        for operation, op_metrics in operation_metrics.items():
            if operation in self.performance_thresholds:
                thresholds = self.performance_thresholds[operation]
                avg_time = statistics.mean(m.value for m in op_metrics)
                
                if avg_time > thresholds.get('critical_ms', float('inf')):
                    issues.append({
                        'severity': 'critical',
                        'operation': operation,
                        'issue': 'Performance critically degraded',
                        'current_avg_ms': round(avg_time, 2),
                        'threshold_ms': thresholds['critical_ms'],
                        'occurrences': len(op_metrics)
                    })
                elif avg_time > thresholds.get('warning_ms', float('inf')):
                    issues.append({
                        'severity': 'warning',
                        'operation': operation,
                        'issue': 'Performance degraded',
                        'current_avg_ms': round(avg_time, 2),
                        'threshold_ms': thresholds['warning_ms'],
                        'occurrences': len(op_metrics)
                    })
                    
        return issues
        
    def _calculate_performance_trends(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Calculate performance trends over time."""
        trends = {}
        
        for profile_key, profile in self.performance_profiles.items():
            component, operation = profile_key.split(':', 1)
            
            # Analyze recent executions for trend
            recent_executions = [
                ex for ex in profile.recent_executions
                if ex['timestamp'] >= cutoff_time
            ]
            
            if len(recent_executions) > 10:
                values = [ex['value'] for ex in recent_executions]
                
                # Calculate trend direction
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                first_avg = statistics.mean(first_half)
                second_avg = statistics.mean(second_half)
                
                if second_avg > first_avg * 1.1:
                    trend_direction = "degrading"
                elif second_avg < first_avg * 0.9:
                    trend_direction = "improving"
                else:
                    trend_direction = "stable"
                    
                profile.trend_direction = trend_direction
                
                trends[profile_key] = {
                    'component': component,
                    'operation': operation,
                    'trend_direction': trend_direction,
                    'performance_change_pct': ((second_avg - first_avg) / first_avg) * 100,
                    'sample_size': len(recent_executions)
                }
                
        return trends
        
    def _calculate_aggregate_statistics(self, profiles: Dict[str, PerformanceProfile]) -> Dict[str, Any]:
        """Calculate aggregate statistics for multiple profiles."""
        if not profiles:
            return {}
            
        total_executions = sum(p.total_executions for p in profiles.values())
        avg_response_times = [p.avg_time_ms for p in profiles.values() if p.total_executions > 0]
        
        if not avg_response_times:
            return {'total_executions': 0}
            
        return {
            'total_executions': total_executions,
            'avg_response_time_ms': statistics.mean(avg_response_times),
            'min_response_time_ms': min(p.min_time_ms for p in profiles.values()),
            'max_response_time_ms': max(p.max_time_ms for p in profiles.values()),
            'operations_with_regressions': sum(
                1 for p in profiles.values() if p.performance_regression
            ),
            'total_recommendations': sum(
                len(p.recommendations) for p in profiles.values()
            )
        }