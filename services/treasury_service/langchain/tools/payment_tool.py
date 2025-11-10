"""Payment approval tool for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...graph.nodes.utils import api
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class PaymentInput(BaseModel):
    """Input for payment operations."""
    entity: str = Field(description="Entity ID for payment operations", default="")
    action: str = Field(description="Payment action: 'list', 'approve', 'status'", default="list")


class PaymentTool(BaseTool):
    """Tool for payment operations in Treasury Agent."""
    
    name: str = "manage_payments"
    description: str = "Handle payment operations including listing pending payments, approving payments, and checking payment status. Use when users ask about payments, approvals, or payment workflows."
    args_schema: type[BaseModel] = PaymentInput
    
    @trace_operation("payment_management_langchain")
    @monitor_performance("payment_tool")
    def _run(self, entity: str = "", action: str = "list") -> Dict[str, Any]:
        """Execute payment operations."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.payment")
        
        logger.info("Managing payments via LangChain tool", entity=entity, action=action)
        
        try:
            if action == "list":
                result = api.get_pending_payments(entity)
            elif action == "approve":
                result = {"message": "Payment approval requires specific payment ID and authorization"}
            else:
                result = {"message": f"Payment action '{action}' executed"}
            
            logger.info("Payment operation completed", 
                       entity=entity, action=action)
            
            observability.record_metric(
                "counter", "payment_operations_total", 1,
                {"source": "langchain_tool", "action": action, "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity,
                "action": action
            }
            
        except Exception as e:
            logger.error("Payment operation failed", 
                        entity=entity, action=action, error=str(e), error_type=type(e).__name__)
            
            observability.record_metric(
                "counter", "payment_operations_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to execute payment operation: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "", action: str = "list") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity, action)