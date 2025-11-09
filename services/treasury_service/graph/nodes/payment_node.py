"""Payment approval node for Treasury Agent."""

import re
from ..types import AgentState
from .utils import api
from ...infrastructure.observability import trace_operation, monitor_performance

@trace_operation("payment_approval")
@monitor_performance("payment_node")
def node_approve(state: AgentState):
    """Approve payments by payment ID or list pending payments."""
    from ...infrastructure.observability import get_observability_manager
    
    observability = get_observability_manager()
    logger = observability.get_logger("graph.payment")
    
    question = state["question"]
    logger.info("Processing payment request", question=question[:100])
    
    # Extract payment ID from question
    payment_match = re.search(r"PMT-\d{5}", question)
    
    try:
        if not payment_match:
            # List pending payments
            logger.info("No payment ID found, listing pending payments")
            state["notes"] = "No payment ID found; listing pending payments."
            df = api.list_payments(status="PENDING")
            state["result"] = df.head(20).to_dict(orient="records")
            
            observability.record_metric(
                "counter", "payment_lists_total", 1,
                {"status": "success"}
            )
            return state
        
        # Approve specific payment
        payment_id = payment_match.group(0)
        logger.info("Attempting to approve payment", payment_id=payment_id)
        
        ok = api.approve_payment(payment_id)
        state["result"] = {
            "approved": ok,
            "payment_id": payment_id,
            "message": "Payment processed successfully"
        }
        
        observability.record_metric(
            "counter", "payment_approvals_total", 1,
            {"status": "success" if ok else "failed"}
        )
        
        return state
            
    except Exception as e:
        logger.error("Payment processing failed", 
                    question=question[:100], error=str(e), error_type=type(e).__name__)
        
        observability.record_metric(
            "counter", "payment_approvals_total", 1,
            {"status": "failed"}
        )
        
        state["result"] = {
            "error": f"Payment processing failed: {str(e)}",
            "approved": False
        }
        return state