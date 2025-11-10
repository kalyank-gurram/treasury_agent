"""Exposure analysis tool for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class ExposureInput(BaseModel):
    """Input for exposure analysis."""
    entity: str = Field(description="Entity ID for exposure analysis", default="")
    exposure_type: str = Field(description="Type of exposure: currency, interest_rate, counterparty", default="currency")


class ExposureTool(BaseTool):
    """Tool for exposure analysis in Treasury Agent."""
    
    name: str = "analyze_treasury_exposure"
    description: str = "Analyze treasury exposures including currency, interest rate, and counterparty risks. Use when users ask about risk exposure, currency risk, or risk analysis."
    args_schema: type[BaseModel] = ExposureInput
    
    @trace_operation("exposure_analysis_langchain")
    @monitor_performance("exposure_tool")
    def _run(self, entity: str = "", exposure_type: str = "currency") -> Dict[str, Any]:
        """Execute exposure analysis."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.exposure")
        
        logger.info("Analyzing exposure via LangChain tool", entity=entity, exposure_type=exposure_type)
        
        try:
            # Simplified exposure analysis
            result = {
                "exposure_type": exposure_type,
                "entity": entity,
                "exposures": [
                    {"currency": "EUR", "amount": 1000000, "risk_level": "medium"},
                    {"currency": "GBP", "amount": 500000, "risk_level": "low"}
                ],
                "total_exposure": 1500000,
                "recommendations": ["Consider hedging EUR exposure", "Monitor GBP volatility"]
            }
            
            logger.info("Exposure analysis completed", entity=entity, exposure_type=exposure_type)
            
            observability.record_metric(
                "counter", "exposure_analyses_total", 1,
                {"source": "langchain_tool", "type": exposure_type, "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity,
                "exposure_type": exposure_type
            }
            
        except Exception as e:
            logger.error("Exposure analysis failed", 
                        entity=entity, exposure_type=exposure_type, error=str(e), error_type=type(e).__name__)
            
            observability.record_metric(
                "counter", "exposure_analyses_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to analyze exposure: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "", exposure_type: str = "currency") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity, exposure_type)