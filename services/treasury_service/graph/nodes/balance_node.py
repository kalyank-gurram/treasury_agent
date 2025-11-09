"""Balance retrieval node for Treasury Agent."""

from ..types import AgentState
from .utils import api
from ...infrastructure.observability import trace_operation, monitor_performance

@trace_operation("balance_retrieval")
@monitor_performance("balance_node")
def node_balances(state: AgentState):
    """Retrieve account balances for the specified entity using domain services."""
    from ...infrastructure.observability import get_observability_manager
    
    # Get observability
    observability = get_observability_manager()
    logger = observability.get_logger("graph.balances")
    
    entity = state.get("entity")
    logger.info("Retrieving balances", entity=entity)
    
    try:
        # Use legacy API for now (domain service integration can be added later)
        logger.info("Retrieving balances using legacy API", entity=entity)
        df = api.get_account_balances(entity)
        result = df.head(50).to_dict(orient="records")
        
        state["result"] = result
        logger.info("Balances retrieved successfully", 
                   entity=entity, count=len(result))
        
        # Record success metric
        observability.record_metric(
            "counter", "balance_retrievals_total", 1,
            {"source": "api", "status": "success"}
        )
        
        return state
        
    except Exception as e:
        logger.error("Balance retrieval failed", 
                    entity=entity, error=str(e), error_type=type(e).__name__)
        
        # Record error metric
        observability.record_metric(
            "counter", "balance_retrievals_total", 1,
            {"source": "error", "status": "failed"}
        )
        
        # Return error state
        state["result"] = {"error": f"Failed to retrieve balances: {str(e)}"}
        return state