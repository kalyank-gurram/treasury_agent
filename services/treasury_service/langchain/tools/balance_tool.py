"""Balance retrieval tool for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...graph.nodes.utils import api
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class BalanceInput(BaseModel):
    """Input for balance retrieval tool."""
    entity: str = Field(description="Entity ID to retrieve balances for", default="")


class BalanceTool(BaseTool):
    """Tool to retrieve account balances for Treasury Agent."""
    
    name: str = "get_account_balances"
    description: str = "Retrieve account balances for a specific entity. Use this when users ask about cash positions, account balances, or available funds."
    args_schema: type[BaseModel] = BalanceInput
    
    @trace_operation("balance_retrieval_langchain")
    @monitor_performance("balance_tool")
    def _run(self, entity: str = "") -> Dict[str, Any]:
        """Execute balance retrieval."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.balance")
        
        logger.info("Retrieving balances via LangChain tool", entity=entity)
        
        try:
            # Use the same API as LangGraph version
            df = api.get_account_balances(entity)
            result = df.head(50).to_dict(orient="records")
            
            logger.info("Balances retrieved successfully", 
                       entity=entity, count=len(result))
            
            # Record success metric
            observability.record_metric(
                "counter", "balance_retrievals_total", 1,
                {"source": "langchain_tool", "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity,
                "count": len(result)
            }
            
        except Exception as e:
            logger.error("Balance retrieval failed", 
                        entity=entity, error=str(e), error_type=type(e).__name__)
            
            # Record error metric
            observability.record_metric(
                "counter", "balance_retrievals_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to retrieve balances: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity)