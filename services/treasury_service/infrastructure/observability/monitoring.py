"""Comprehensive observability framework with logging, metrics, and tracing."""

import logging
import logging.config
import time
import uuid
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timezone
from contextlib import contextmanager
import json
import threading
from collections import defaultdict, Counter

from ..config.settings import ObservabilityConfig, LogLevel


class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(self, name: str, config: ObservabilityConfig):
        self.name = name
        self.config = config
        self._context_data = threading.local()
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup structured logging configuration."""
        # Check if pythonjsonlogger is available for JSON formatting
        json_formatter_available = False
        try:
            import pythonjsonlogger.jsonlogger
            json_formatter_available = True
        except ImportError:
            # Fall back to text formatting if pythonjsonlogger is not available
            pass
        
        # Configure formatters based on availability
        formatters = {
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        if json_formatter_available and self.config.log_format == "json":
            formatters["json"] = {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s"
            }
            formatter_type = "json"
        else:
            # Use text formatter as fallback
            formatter_type = "text"
        
        logger_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_type,
                    "level": self.config.log_level.value
                }
            },
            "loggers": {
                self.name: {
                    "handlers": ["console"],
                    "level": self.config.log_level.value,
                    "propagate": False
                }
            }
        }
        
        logging.config.dictConfig(logger_config)
        self.logger = logging.getLogger(self.name)
    
    @contextmanager
    def context(self, **kwargs):
        """Add context data to logs."""
        if not hasattr(self._context_data, 'data'):
            self._context_data.data = {}
        
        original_data = self._context_data.data.copy()
        self._context_data.data.update(kwargs)
        
        try:
            yield
        finally:
            self._context_data.data = original_data
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current context data."""
        if not hasattr(self._context_data, 'data'):
            return {}
        return getattr(self._context_data, 'data', {})
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """Log message with context."""
        context = self._get_context()
        extra_data = {**context, **kwargs}
        
        # Add standard fields
        extra_data.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "treasury-agent",
            "correlation_id": extra_data.get("correlation_id", str(uuid.uuid4()))
        })
        
        self.logger.log(level, message, extra={"structured_data": extra_data})
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)


class MetricsCollector:
    """Metrics collection and aggregation."""
    
    def __init__(self):
        self._counters = defaultdict(int)
        self._gauges = {}
        self._histograms = defaultdict(list)
        self._timers = {}
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            metric_key = self._build_metric_key(name, labels)
            self._counters[metric_key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            metric_key = self._build_metric_key(name, labels)
            self._gauges[metric_key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value for histogram metric."""
        with self._lock:
            metric_key = self._build_metric_key(name, labels)
            self._histograms[metric_key].append(value)
    
    @contextmanager
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Timer context manager."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.observe_histogram(f"{name}_duration_seconds", duration, labels)
    
    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Build metric key with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self._calculate_histogram_stats(v) for k, v in self._histograms.items()},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_histogram_stats(self, values: list) -> Dict[str, float]:
        """Calculate histogram statistics."""
        if not values:
            return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}
        
        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }


class TraceContext:
    """Distributed tracing context."""
    
    def __init__(self, trace_id: str = None, span_id: str = None, parent_span_id: str = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.tags = {}
        self.logs = []
    
    def set_tag(self, key: str, value: Any) -> None:
        """Set a tag on the trace."""
        self.tags[key] = value
    
    def log(self, message: str, **kwargs) -> None:
        """Add a log entry to the trace."""
        self.logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "data": kwargs
        })
    
    def finish(self) -> Dict[str, Any]:
        """Finish the trace and return span data."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": time.time(),
            "duration": time.time() - self.start_time,
            "tags": self.tags,
            "logs": self.logs
        }


class ObservabilityManager:
    """Central observability manager."""
    
    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self.logger = StructuredLogger("treasury-agent", config)
        self.metrics = MetricsCollector() if config.metrics_enabled else None
        self._current_trace = threading.local()
    
    def get_logger(self, name: str = None) -> StructuredLogger:
        """Get a logger instance."""
        logger_name = f"treasury-agent.{name}" if name else "treasury-agent"
        return StructuredLogger(logger_name, self.config)
    
    def start_trace(self, operation_name: str, parent_trace: TraceContext = None) -> Optional[TraceContext]:
        """Start a new trace."""
        if not self.config.tracing_enabled:
            return None
        
        parent_span_id = parent_trace.span_id if parent_trace else None
        trace_id = parent_trace.trace_id if parent_trace else None
        
        trace = TraceContext(trace_id=trace_id, parent_span_id=parent_span_id)
        trace.set_tag("operation.name", operation_name)
        trace.set_tag("service.name", "treasury-agent")
        
        self._current_trace.context = trace
        return trace
    
    def get_current_trace(self) -> Optional[TraceContext]:
        """Get current trace context."""
        return getattr(self._current_trace, 'context', None)
    
    def record_metric(self, metric_type: str, name: str, value: Any, labels: Dict[str, str] = None) -> None:
        """Record a metric."""
        if not self.metrics:
            return
        
        if metric_type == "counter":
            self.metrics.increment_counter(name, value, labels)
        elif metric_type == "gauge":
            self.metrics.set_gauge(name, value, labels)
        elif metric_type == "histogram":
            self.metrics.observe_histogram(name, value, labels)
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        if not self.metrics:
            return {}
        return self.metrics.get_metrics()


def trace_operation(operation_name: str):
    """Decorator to trace function execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            observability = get_observability_manager()
            
            if not observability.config.tracing_enabled:
                return func(*args, **kwargs)
            
            trace = observability.start_trace(operation_name)
            if trace:
                trace.set_tag("function.name", func.__name__)
                trace.set_tag("function.module", func.__module__)
            
            try:
                result = func(*args, **kwargs)
                if trace:
                    trace.set_tag("success", True)
                return result
            except Exception as e:
                if trace:
                    trace.set_tag("error", True)
                    trace.set_tag("error.message", str(e))
                    trace.log("Exception occurred", error_type=type(e).__name__)
                raise
            finally:
                if trace:
                    span_data = trace.finish()
                    observability.logger.debug("Trace completed", **span_data)
        
        return wrapper
    return decorator


def monitor_performance(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            observability = get_observability_manager()
            
            # Record function call
            call_labels = {**(labels or {}), "function": func.__name__}
            observability.record_metric("counter", f"{metric_name}_calls", 1, call_labels)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # Record success
                success_labels = {**call_labels, "status": "success"}
                observability.record_metric("counter", f"{metric_name}_results", 1, success_labels)
                return result
            except Exception as e:
                # Record error
                error_labels = {**call_labels, "status": "error", "error_type": type(e).__name__}
                observability.record_metric("counter", f"{metric_name}_results", 1, error_labels)
                raise
            finally:
                # Record duration
                duration = time.time() - start_time
                observability.record_metric("histogram", f"{metric_name}_duration", duration, call_labels)
        
        return wrapper
    return decorator


# Global observability manager
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager() -> ObservabilityManager:
    """Get global observability manager."""
    global _observability_manager
    if _observability_manager is None:
        from ..config.settings import get_config
        config = get_config()
        _observability_manager = ObservabilityManager(config.observability)
    return _observability_manager


def configure_observability(config: ObservabilityConfig) -> ObservabilityManager:
    """Configure global observability."""
    global _observability_manager
    _observability_manager = ObservabilityManager(config)
    return _observability_manager