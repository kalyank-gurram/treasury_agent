"""Anomaly detection tool for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...detectors.anomaly import TreasuryAnomalyDetector
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class AnomalyInput(BaseModel):
    """Input for anomaly detection tool."""
    entity: str = Field(description="Entity ID to check for anomalies", default="")


class AnomalyTool(BaseTool):
    """Tool to detect treasury anomalies for Treasury Agent."""
    
    name: str = "detect_treasury_anomalies"
    description: str = "Detect anomalies in treasury transactions and cash flows. Use when users ask about unusual patterns, outliers, or suspicious activities."
    args_schema: type[BaseModel] = AnomalyInput
    
    @trace_operation("anomaly_detection_langchain")
    @monitor_performance("anomaly_tool")
    def _run(self, entity: str = "") -> Dict[str, Any]:
        """Execute anomaly detection."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.anomaly")
        
        logger.info("Detecting anomalies via LangChain tool", entity=entity)
        
        try:
            # Create sample cash flow data for anomaly detection
            import pandas as pd
            import numpy as np
            from datetime import datetime, timedelta
            
            # Generate sample daily cash flows with some anomalies
            rng = np.random.default_rng(42)
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            
            # Normal cash flows with some seasonal patterns
            normal_flows = rng.normal(5000, 15000, len(dates))
            
            # Add some anomalies
            anomaly_indices = rng.choice(len(dates), size=10, replace=False)
            for idx in anomaly_indices:
                normal_flows[idx] += rng.choice([-100000, 150000])  # Large outflow or inflow
            
            daily_series = pd.Series(normal_flows, index=dates)
            
            detector = TreasuryAnomalyDetector()
            result = detector.detect_cash_flow_anomalies(daily_series)
            
            # Convert to dictionary format for JSON serialization
            if len(result) > 0:
                result = result.to_dict('records')
                # Convert datetime objects to strings
                for record in result:
                    if 'date' in record:
                        record['date'] = record['date'].strftime('%Y-%m-%d')
            else:
                result = {"message": "No anomalies detected in the cash flow data"}
            
            logger.info("Anomaly detection completed", 
                       entity=entity, anomalies_found=len(result.get("anomalies", [])))
            
            observability.record_metric(
                "counter", "anomaly_detections_total", 1,
                {"source": "langchain_tool", "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity
            }
            
        except Exception as e:
            logger.error("Anomaly detection failed", 
                        entity=entity, error=str(e), error_type=type(e).__name__)
            
            observability.record_metric(
                "counter", "anomaly_detections_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to detect anomalies: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity)