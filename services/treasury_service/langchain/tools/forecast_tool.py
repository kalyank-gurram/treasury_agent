"""Forecast tool for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...forecasting.arima_forecaster import arima_forecast
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class ForecastInput(BaseModel):
    """Input for forecast tool."""
    entity: str = Field(description="Entity ID to generate forecast for", default="")
    days: int = Field(description="Number of days to forecast", default=30)


class ForecastTool(BaseTool):
    """Tool to generate cash flow forecasts for Treasury Agent."""
    
    name: str = "generate_cash_forecast"
    description: str = "Generate cash flow forecasts using ARIMA modeling. Use when users ask about future cash flows, predictions, or forecasting."
    args_schema: type[BaseModel] = ForecastInput
    
    @trace_operation("forecast_generation_langchain")
    @monitor_performance("forecast_tool")
    def _run(self, entity: str = "", days: int = 30) -> Dict[str, Any]:
        """Execute forecast generation."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.forecast")
        
        logger.info("Generating forecast via LangChain tool", entity=entity, days=days)
        
        try:
            # Use the same forecasting logic as LangGraph version
            # Create dummy data for demonstration
            import pandas as pd
            import numpy as np
            
            dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
            rng = np.random.default_rng(42)  # For reproducible results
            cash_flows = rng.normal(100000, 20000, days)
            
            series = pd.Series(cash_flows, index=dates)
            result = arima_forecast(series, steps=min(days, 30))
            
            logger.info("Forecast generated successfully", 
                       entity=entity, forecast_days=days)
            
            # Record success metric
            observability.record_metric(
                "counter", "forecast_generations_total", 1,
                {"source": "langchain_tool", "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity,
                "forecast_days": days
            }
            
        except Exception as e:
            logger.error("Forecast generation failed", 
                        entity=entity, error=str(e), error_type=type(e).__name__)
            
            # Record error metric
            observability.record_metric(
                "counter", "forecast_generations_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to generate forecast: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "", days: int = 30) -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity, days)