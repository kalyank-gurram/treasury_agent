"""Intent classification node for Treasury Agent."""

from ...models.llm_router import LLMRouter
from ..types import AgentState
from ...infrastructure.observability import trace_operation, monitor_performance

@trace_operation("intent_classification")
@monitor_performance("intent_node")
def node_intent(state: AgentState):
    """Classify user intent among available Treasury Agent capabilities."""
    # Use existing LLM router (could be moved to DI in future)
    llm = LLMRouter().cheap()
    
    sys = "Classify the user's intent among: balances, forecast, approve_payment, anomalies, kpis, whatifs, exposure, rag_check, narrative."
    prompt = f"{sys}\nUser: {state['question']}\nReturn one label."
    
    out = llm.invoke(prompt)
    label = str(getattr(out,'content',out)).strip().lower()
    intent = label.split()[0]
    
    state["intent"] = intent
    
    # Log intent classification
    from ...infrastructure.observability import get_observability_manager
    observability = get_observability_manager()
    logger = observability.get_logger("graph.intent")
    logger.info("Intent classified", 
               question=state['question'][:100], 
               classified_intent=intent)
    
    # Record metric
    observability.record_metric(
        "counter", "intent_classifications_total", 1,
        {"intent": intent}
    )
    
    return state