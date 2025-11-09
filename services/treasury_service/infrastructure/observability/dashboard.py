"""Real-time Dashboard Service for Treasury Operations.

This module provides comprehensive dashboard capabilities with real-time
data visualization, customizable widgets, and interactive treasury analytics.
"""

import json
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from collections import defaultdict


class WidgetType(Enum):
    """Types of dashboard widgets."""
    METRIC_CARD = "metric_card"           # Single value display
    LINE_CHART = "line_chart"             # Time series data
    BAR_CHART = "bar_chart"               # Categorical data
    PIE_CHART = "pie_chart"               # Proportional data
    GAUGE = "gauge"                       # Progress/percentage indicator
    TABLE = "table"                       # Tabular data display
    HEATMAP = "heatmap"                   # Matrix/correlation data
    ALERT_LIST = "alert_list"             # Active alerts display
    KPI_SUMMARY = "kpi_summary"           # Key performance indicators
    TREND_INDICATOR = "trend_indicator"   # Trend arrows and percentages
    STATUS_GRID = "status_grid"           # Component status overview
    REAL_TIME_FEED = "real_time_feed"     # Live activity feed


class DashboardTheme(Enum):
    """Dashboard visual themes."""
    LIGHT = "light"
    DARK = "dark"
    TREASURY_BLUE = "treasury_blue"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class WidgetConfiguration:
    """Configuration for dashboard widgets."""
    widget_id: str
    title: str
    widget_type: WidgetType
    
    # Data configuration
    data_source: str
    refresh_interval_seconds: int = 30
    
    # Display configuration
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0, "width": 4, "height": 3})
    
    # Widget-specific settings
    chart_config: Dict[str, Any] = field(default_factory=dict)
    display_options: Dict[str, Any] = field(default_factory=dict)
    
    # Filtering and aggregation
    filters: Dict[str, Any] = field(default_factory=dict)
    aggregation_method: str = "avg"  # avg, sum, count, min, max
    time_window: str = "1h"  # 5m, 15m, 1h, 4h, 24h, 7d
    
    # Alerts and thresholds
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Permissions
    required_permissions: List[str] = field(default_factory=list)


@dataclass
class Widget:
    """Dashboard widget with data and configuration."""
    config: WidgetConfiguration
    data: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "loading"  # loading, ready, error, stale
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert widget to dictionary for JSON serialization."""
        return {
            'widget_id': self.config.widget_id,
            'title': self.config.title,
            'widget_type': self.config.widget_type.value,
            'position': self.config.position,
            'data': self.data,
            'last_updated': self.last_updated.isoformat(),
            'status': self.status,
            'error_message': self.error_message,
            'display_options': self.config.display_options,
            'chart_config': self.config.chart_config
        }


@dataclass
class Dashboard:
    """Treasury operations dashboard."""
    dashboard_id: str
    name: str
    description: str
    
    # Dashboard configuration
    widgets: List[Widget] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    theme: DashboardTheme = DashboardTheme.TREASURY_BLUE
    
    # Access control
    owner: str = "system"
    shared_with: List[str] = field(default_factory=list)
    is_public: bool = False
    
    # Dashboard metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    view_count: int = 0
    
    # Auto-refresh settings
    auto_refresh: bool = True
    refresh_interval_seconds: int = 30
    
    def add_widget(self, widget: Widget):
        """Add widget to dashboard."""
        self.widgets.append(widget)
        self.last_modified = datetime.now(timezone.utc)
        
    def remove_widget(self, widget_id: str) -> bool:
        """Remove widget from dashboard."""
        for i, widget in enumerate(self.widgets):
            if widget.config.widget_id == widget_id:
                del self.widgets[i]
                self.last_modified = datetime.now(timezone.utc)
                return True
        return False
        
    def get_widget(self, widget_id: str) -> Optional[Widget]:
        """Get widget by ID."""
        for widget in self.widgets:
            if widget.config.widget_id == widget_id:
                return widget
        return None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary for JSON serialization."""
        return {
            'dashboard_id': self.dashboard_id,
            'name': self.name,
            'description': self.description,
            'theme': self.theme.value,
            'owner': self.owner,
            'shared_with': self.shared_with,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'view_count': self.view_count,
            'auto_refresh': self.auto_refresh,
            'refresh_interval_seconds': self.refresh_interval_seconds,
            'widgets': [widget.to_dict() for widget in self.widgets],
            'layout': self.layout
        }


class DashboardService:
    """Comprehensive dashboard service for treasury operations."""
    
    def __init__(self, metrics_collector=None, alert_manager=None, health_monitor=None):
        # Service dependencies
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_monitor = health_monitor
        
        # Dashboard storage
        self.dashboards: Dict[str, Dashboard] = {}
        self.widget_data_cache: Dict[str, Dict[str, Any]] = {}
        self.data_providers: Dict[str, Callable] = {}
        
        # Real-time subscriptions
        self.active_subscriptions: Dict[str, List[str]] = defaultdict(list)  # dashboard_id -> [widget_ids]
        
        # Initialize default dashboards
        self._initialize_treasury_dashboards()
        
        # Register data providers
        self._register_data_providers()
        
        self.logger = logging.getLogger(__name__)
        
    def _initialize_treasury_dashboards(self):
        """Initialize default treasury dashboards."""
        
        # Executive Treasury Overview Dashboard
        executive_dashboard = self.create_dashboard(
            dashboard_id="treasury_executive_overview",
            name="Treasury Executive Overview",
            description="High-level treasury metrics and KPIs for executive leadership",
            owner="treasury_team"
        )
        
        # Add executive widgets
        self._add_executive_widgets(executive_dashboard)
        
        # Treasury Operations Dashboard
        operations_dashboard = self.create_dashboard(
            dashboard_id="treasury_operations",
            name="Treasury Operations",
            description="Detailed operational metrics for treasury team",
            owner="treasury_team"
        )
        
        # Add operations widgets
        self._add_operations_widgets(operations_dashboard)
        
        # Risk Management Dashboard
        risk_dashboard = self.create_dashboard(
            dashboard_id="risk_management",
            name="Risk Management",
            description="Risk monitoring and compliance tracking",
            owner="risk_team"
        )
        
        # Add risk widgets
        self._add_risk_widgets(risk_dashboard)
        
        # System Health Dashboard
        health_dashboard = self.create_dashboard(
            dashboard_id="system_health",
            name="System Health & Performance",
            description="Technology infrastructure monitoring",
            owner="it_team"
        )
        
        # Add health widgets
        self._add_health_widgets(health_dashboard)
        
    def _add_executive_widgets(self, dashboard: Dashboard):
        """Add widgets for executive dashboard."""
        
        # Cash Position Summary
        cash_summary_widget = Widget(
            config=WidgetConfiguration(
                widget_id="cash_position_summary",
                title="Total Cash Position",
                widget_type=WidgetType.METRIC_CARD,
                data_source="treasury_metrics",
                refresh_interval_seconds=300,
                position={"x": 0, "y": 0, "width": 3, "height": 2},
                display_options={
                    "show_trend": True,
                    "format": "currency_usd",
                    "trend_period": "24h"
                },
                time_window="24h"
            )
        )
        dashboard.add_widget(cash_summary_widget)
        
        # Daily Cash Flow
        cash_flow_widget = Widget(
            config=WidgetConfiguration(
                widget_id="daily_cash_flow_chart",
                title="Daily Cash Flow Trend",
                widget_type=WidgetType.LINE_CHART,
                data_source="cash_flow_data",
                refresh_interval_seconds=600,
                position={"x": 3, "y": 0, "width": 6, "height": 4},
                chart_config={
                    "x_axis": "date",
                    "y_axis": "cash_flow",
                    "line_color": "#2E86AB",
                    "show_grid": True
                },
                time_window="7d"
            )
        )
        dashboard.add_widget(cash_flow_widget)
        
        # Investment Portfolio Value
        portfolio_widget = Widget(
            config=WidgetConfiguration(
                widget_id="portfolio_value",
                title="Investment Portfolio",
                widget_type=WidgetType.METRIC_CARD,
                data_source="investment_metrics",
                refresh_interval_seconds=300,
                position={"x": 9, "y": 0, "width": 3, "height": 2},
                display_options={
                    "show_trend": True,
                    "format": "currency_usd",
                    "trend_period": "24h"
                }
            )
        )
        dashboard.add_widget(portfolio_widget)
        
        # Risk Metrics Summary
        risk_summary_widget = Widget(
            config=WidgetConfiguration(
                widget_id="risk_metrics_summary",
                title="Risk Summary",
                widget_type=WidgetType.KPI_SUMMARY,
                data_source="risk_metrics",
                refresh_interval_seconds=180,
                position={"x": 0, "y": 2, "width": 6, "height": 3},
                display_options={
                    "kpis": ["liquidity_ratio", "var_95", "credit_exposure"],
                    "show_status_indicators": True
                }
            )
        )
        dashboard.add_widget(risk_summary_widget)
        
        # Active Alerts
        alerts_widget = Widget(
            config=WidgetConfiguration(
                widget_id="active_alerts_executive",
                title="Critical Alerts",
                widget_type=WidgetType.ALERT_LIST,
                data_source="alert_data",
                refresh_interval_seconds=60,
                position={"x": 6, "y": 2, "width": 6, "height": 3},
                filters={"severity": ["critical", "high"]},
                display_options={"max_items": 10}
            )
        )
        dashboard.add_widget(alerts_widget)
        
    def _add_operations_widgets(self, dashboard: Dashboard):
        """Add widgets for operations dashboard."""
        
        # Payment Processing Volume
        payment_volume_widget = Widget(
            config=WidgetConfiguration(
                widget_id="payment_processing_volume",
                title="Payment Processing Volume",
                widget_type=WidgetType.BAR_CHART,
                data_source="payment_metrics",
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                chart_config={
                    "x_axis": "hour",
                    "y_axis": "payment_count",
                    "bar_color": "#A23B72"
                },
                time_window="24h"
            )
        )
        dashboard.add_widget(payment_volume_widget)
        
        # Payment Success Rate
        success_rate_widget = Widget(
            config=WidgetConfiguration(
                widget_id="payment_success_rate",
                title="Payment Success Rate",
                widget_type=WidgetType.GAUGE,
                data_source="payment_metrics",
                position={"x": 6, "y": 0, "width": 3, "height": 4},
                display_options={
                    "min_value": 0,
                    "max_value": 100,
                    "unit": "%",
                    "thresholds": {"warning": 95, "critical": 90}
                }
            )
        )
        dashboard.add_widget(success_rate_widget)
        
        # System Performance Metrics
        performance_widget = Widget(
            config=WidgetConfiguration(
                widget_id="system_performance_grid",
                title="System Performance",
                widget_type=WidgetType.STATUS_GRID,
                data_source="performance_metrics",
                position={"x": 9, "y": 0, "width": 3, "height": 4},
                display_options={
                    "metrics": ["api_response_time", "database_latency", "cpu_usage", "memory_usage"]
                }
            )
        )
        dashboard.add_widget(performance_widget)
        
        # Recent Transactions
        transactions_widget = Widget(
            config=WidgetConfiguration(
                widget_id="recent_transactions",
                title="Recent Large Transactions",
                widget_type=WidgetType.TABLE,
                data_source="transaction_data",
                position={"x": 0, "y": 4, "width": 12, "height": 4},
                filters={"amount_threshold": 1000000},
                display_options={
                    "columns": ["timestamp", "amount", "type", "status", "counterparty"],
                    "max_rows": 20
                }
            )
        )
        dashboard.add_widget(transactions_widget)
        
    def _add_risk_widgets(self, dashboard: Dashboard):
        """Add widgets for risk management dashboard."""
        
        # Liquidity Risk Heatmap
        liquidity_heatmap_widget = Widget(
            config=WidgetConfiguration(
                widget_id="liquidity_risk_heatmap",
                title="Liquidity Risk by Currency",
                widget_type=WidgetType.HEATMAP,
                data_source="liquidity_metrics",
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                chart_config={
                    "x_axis": "currency",
                    "y_axis": "maturity_bucket",
                    "value_field": "risk_score"
                }
            )
        )
        dashboard.add_widget(liquidity_heatmap_widget)
        
        # Credit Exposure Distribution
        credit_exposure_widget = Widget(
            config=WidgetConfiguration(
                widget_id="credit_exposure_distribution",
                title="Credit Exposure by Counterparty",
                widget_type=WidgetType.PIE_CHART,
                data_source="credit_metrics",
                position={"x": 6, "y": 0, "width": 6, "height": 4},
                chart_config={
                    "value_field": "exposure_amount",
                    "label_field": "counterparty_name",
                    "max_slices": 10
                }
            )
        )
        dashboard.add_widget(credit_exposure_widget)
        
        # Compliance Violations
        compliance_widget = Widget(
            config=WidgetConfiguration(
                widget_id="compliance_violations",
                title="Compliance Violations",
                widget_type=WidgetType.ALERT_LIST,
                data_source="compliance_data",
                position={"x": 0, "y": 4, "width": 12, "height": 3},
                filters={"event_type": "compliance_violation"},
                display_options={
                    "show_severity": True,
                    "group_by_type": True
                }
            )
        )
        dashboard.add_widget(compliance_widget)
        
    def _add_health_widgets(self, dashboard: Dashboard):
        """Add widgets for system health dashboard."""
        
        # Component Health Overview
        health_overview_widget = Widget(
            config=WidgetConfiguration(
                widget_id="component_health_overview",
                title="System Component Health",
                widget_type=WidgetType.STATUS_GRID,
                data_source="health_data",
                position={"x": 0, "y": 0, "width": 8, "height": 4},
                display_options={
                    "show_response_times": True,
                    "group_by_type": True
                }
            )
        )
        dashboard.add_widget(health_overview_widget)
        
        # Performance Trends
        performance_trends_widget = Widget(
            config=WidgetConfiguration(
                widget_id="performance_trends",
                title="Performance Trends",
                widget_type=WidgetType.LINE_CHART,
                data_source="performance_data",
                position={"x": 8, "y": 0, "width": 4, "height": 4},
                chart_config={
                    "multiple_series": True,
                    "metrics": ["api_response_time", "database_query_time", "cpu_usage"]
                },
                time_window="4h"
            )
        )
        dashboard.add_widget(performance_trends_widget)
        
    def _register_data_providers(self):
        """Register data provider functions for widgets."""
        
        # Treasury metrics provider
        self.data_providers["treasury_metrics"] = self._get_treasury_metrics_data
        self.data_providers["cash_flow_data"] = self._get_cash_flow_data
        self.data_providers["investment_metrics"] = self._get_investment_metrics_data
        self.data_providers["payment_metrics"] = self._get_payment_metrics_data
        self.data_providers["transaction_data"] = self._get_transaction_data
        self.data_providers["risk_metrics"] = self._get_risk_metrics_data
        self.data_providers["liquidity_metrics"] = self._get_liquidity_metrics_data
        self.data_providers["credit_metrics"] = self._get_credit_metrics_data
        self.data_providers["compliance_data"] = self._get_compliance_data
        self.data_providers["alert_data"] = self._get_alert_data
        self.data_providers["health_data"] = self._get_health_data
        self.data_providers["performance_data"] = self._get_performance_data
        self.data_providers["performance_metrics"] = self._get_performance_metrics_data
        
    def create_dashboard(self, dashboard_id: str, name: str, description: str,
                        owner: str = "system", theme: DashboardTheme = DashboardTheme.TREASURY_BLUE) -> Dashboard:
        """Create a new dashboard."""
        dashboard = Dashboard(
            dashboard_id=dashboard_id,
            name=name,
            description=description,
            owner=owner,
            theme=theme
        )
        
        self.dashboards[dashboard_id] = dashboard
        self.logger.info(f"Created dashboard: {name}")
        
        return dashboard
        
    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self.dashboards.get(dashboard_id)
        
    def list_dashboards(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List available dashboards for a user."""
        dashboard_list = []
        
        for dashboard in self.dashboards.values():
            # Check access permissions
            if (dashboard.is_public or 
                dashboard.owner == user_id or 
                user_id in dashboard.shared_with or
                user_id == "admin"):
                
                dashboard_list.append({
                    'dashboard_id': dashboard.dashboard_id,
                    'name': dashboard.name,
                    'description': dashboard.description,
                    'owner': dashboard.owner,
                    'created_at': dashboard.created_at.isoformat(),
                    'last_modified': dashboard.last_modified.isoformat(),
                    'widget_count': len(dashboard.widgets),
                    'view_count': dashboard.view_count
                })
                
        return sorted(dashboard_list, key=lambda x: x['last_modified'], reverse=True)
        
    def update_dashboard_data(self, dashboard_id: str) -> bool:
        """Update data for all widgets in a dashboard."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return False
            
        updated_widgets = 0
        
        for widget in dashboard.widgets:
            try:
                if self._should_refresh_widget(widget):
                    new_data = self._fetch_widget_data(widget)
                    if new_data:
                        widget.data = new_data
                        widget.last_updated = datetime.now(timezone.utc)
                        widget.status = "ready"
                        widget.error_message = None
                        updated_widgets += 1
                        
            except Exception as e:
                widget.status = "error"
                widget.error_message = str(e)
                self.logger.error(f"Failed to update widget {widget.config.widget_id}: {e}")
                
        self.logger.debug(f"Updated {updated_widgets} widgets for dashboard {dashboard_id}")
        return updated_widgets > 0
        
    def get_dashboard_json(self, dashboard_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get dashboard data in JSON format."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None
            
        # Check access permissions
        if not (dashboard.is_public or 
               dashboard.owner == user_id or 
               user_id in dashboard.shared_with or
               user_id == "admin"):
            return None
            
        # Update view count
        dashboard.view_count += 1
        
        # Refresh data if needed
        self.update_dashboard_data(dashboard_id)
        
        return dashboard.to_dict()
        
    def add_widget_to_dashboard(self, dashboard_id: str, widget_config: WidgetConfiguration) -> bool:
        """Add a widget to an existing dashboard."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return False
            
        widget = Widget(config=widget_config)
        
        # Fetch initial data
        try:
            initial_data = self._fetch_widget_data(widget)
            widget.data = initial_data or {}
            widget.status = "ready" if initial_data else "error"
        except Exception as e:
            widget.status = "error"
            widget.error_message = str(e)
            
        dashboard.add_widget(widget)
        return True
        
    def _should_refresh_widget(self, widget: Widget) -> bool:
        """Check if widget data should be refreshed."""
        if widget.status == "loading":
            return False
            
        time_since_update = (datetime.now(timezone.utc) - widget.last_updated).total_seconds()
        return time_since_update >= widget.config.refresh_interval_seconds
        
    def _fetch_widget_data(self, widget: Widget) -> Optional[Dict[str, Any]]:
        """Fetch data for a widget from its data source."""
        data_provider = self.data_providers.get(widget.config.data_source)
        if not data_provider:
            raise ValueError(f"Unknown data source: {widget.config.data_source}")
            
        return data_provider(widget.config)
        
    # Data provider methods (simulated data for demonstration)
    
    def _get_treasury_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get treasury metrics data."""
        # In production, this would query actual metrics
        return {
            "value": 15750000,  # $15.75M
            "currency": "USD",
            "trend": "+2.3%",
            "trend_direction": "up",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    def _get_cash_flow_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get cash flow chart data."""
        # Simulated 7-day cash flow data
        import random
        base_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        data_points = []
        for i in range(7):
            date = base_date + timedelta(days=i)
            cash_flow = random.randint(-2000000, 5000000)  # -$2M to +$5M
            data_points.append({
                "date": date.strftime("%Y-%m-%d"),
                "cash_flow": cash_flow
            })
            
        return {
            "chart_type": "line",
            "data": data_points,
            "x_axis": "date",
            "y_axis": "cash_flow"
        }
        
    def _get_investment_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get investment portfolio data."""
        return {
            "value": 45200000,  # $45.2M
            "currency": "USD", 
            "yield": "3.25%",
            "trend": "+1.8%",
            "trend_direction": "up"
        }
        
    def _get_payment_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get payment processing metrics."""
        if config.widget_type == WidgetType.BAR_CHART:
            # Hourly payment volume
            import random
            hours = []
            for i in range(24):
                hour = f"{i:02d}:00"
                count = random.randint(50, 500)
                hours.append({"hour": hour, "payment_count": count})
                
            return {
                "chart_type": "bar",
                "data": hours,
                "x_axis": "hour",
                "y_axis": "payment_count"
            }
        else:
            # Success rate gauge
            return {
                "value": 98.7,
                "unit": "%",
                "status": "healthy",
                "total_payments": 12450
            }
            
    def _get_transaction_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get recent transaction data."""
        # Simulated large transactions
        transactions = []
        for i in range(10):
            transactions.append({
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                "amount": f"${random.randint(1000000, 10000000):,}",
                "type": random.choice(["Wire Transfer", "Investment Purchase", "Loan Disbursement"]),
                "status": random.choice(["Completed", "Pending", "Processing"]),
                "counterparty": f"Entity {chr(65 + i)}"
            })
            
        return {
            "table_type": "transactions",
            "data": transactions,
            "total_count": len(transactions)
        }
        
    def _get_risk_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get risk metrics summary."""
        return {
            "kpis": {
                "liquidity_ratio": {"value": 1.45, "status": "healthy", "threshold": 1.2},
                "var_95": {"value": "2.1M", "status": "warning", "threshold": "2.5M"},
                "credit_exposure": {"value": "125M", "status": "healthy", "threshold": "150M"}
            }
        }
        
    def _get_liquidity_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get liquidity risk heatmap data."""
        currencies = ["USD", "EUR", "GBP", "JPY"]
        maturities = ["0-30d", "31-90d", "91-180d", "181-365d"]
        
        heatmap_data = []
        for currency in currencies:
            for maturity in maturities:
                import random
                risk_score = random.uniform(0.1, 0.9)
                heatmap_data.append({
                    "currency": currency,
                    "maturity_bucket": maturity,
                    "risk_score": risk_score
                })
                
        return {
            "chart_type": "heatmap",
            "data": heatmap_data
        }
        
    def _get_credit_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get credit exposure distribution."""
        counterparties = [
            {"name": "Bank A", "exposure": 45000000},
            {"name": "Bank B", "exposure": 32000000},
            {"name": "Corp C", "exposure": 28000000},
            {"name": "Fund D", "exposure": 20000000},
            {"name": "Others", "exposure": 15000000}
        ]
        
        return {
            "chart_type": "pie",
            "data": counterparties,
            "value_field": "exposure",
            "label_field": "name"
        }
        
    def _get_compliance_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get compliance violations data."""
        violations = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "violation_type": "SOX Control Failure",
                "severity": "high",
                "description": "Segregation of duties violation in payment approval",
                "status": "investigating"
            }
        ]
        
        return {
            "alerts": violations,
            "total_count": len(violations)
        }
        
    def _get_alert_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get active alerts data."""
        alerts = [
            {
                "alert_id": "alert_001",
                "title": "Cash Balance Low",
                "severity": "high",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "active"
            },
            {
                "alert_id": "alert_002", 
                "title": "Payment Processing Slow",
                "severity": "medium",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
                "status": "acknowledged"
            }
        ]
        
        return {
            "alerts": alerts,
            "total_count": len(alerts)
        }
        
    def _get_health_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get system health data."""
        components = [
            {"name": "Database", "status": "healthy", "response_time": "15ms"},
            {"name": "Payment API", "status": "healthy", "response_time": "120ms"},
            {"name": "Cache", "status": "degraded", "response_time": "45ms"},
            {"name": "Authentication", "status": "healthy", "response_time": "8ms"}
        ]
        
        return {
            "components": components,
            "overall_status": "healthy"
        }
        
    def _get_performance_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get performance trends data."""
        import random
        
        # Generate 4 hours of data points
        data_points = []
        base_time = datetime.now(timezone.utc) - timedelta(hours=4)
        
        for i in range(48):  # 5-minute intervals
            timestamp = base_time + timedelta(minutes=i*5)
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "api_response_time": random.uniform(100, 300),
                "database_query_time": random.uniform(10, 50),
                "cpu_usage": random.uniform(20, 80)
            })
            
        return {
            "chart_type": "multi_line",
            "data": data_points,
            "metrics": ["api_response_time", "database_query_time", "cpu_usage"]
        }
        
    def _get_performance_metrics_data(self, config: WidgetConfiguration) -> Dict[str, Any]:
        """Get system performance grid data."""
        return {
            "metrics": {
                "api_response_time": {"value": "245ms", "status": "healthy", "threshold": "500ms"},
                "database_latency": {"value": "32ms", "status": "healthy", "threshold": "100ms"}, 
                "cpu_usage": {"value": "45%", "status": "healthy", "threshold": "80%"},
                "memory_usage": {"value": "67%", "status": "warning", "threshold": "85%"}
            }
        }