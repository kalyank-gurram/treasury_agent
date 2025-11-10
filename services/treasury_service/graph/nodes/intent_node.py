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
    

    sys = (
        "Classify the user's intent among: balances, forecast, approve_payment, anomalies, kpis, whatifs, exposure, rag_check, narrative. "
        "Return all relevant labels, comma-separated."
    )
    prompt = f"{sys}\nUser: {state['question']}\nLabels:"

    out = llm.invoke(prompt)
    label_str = str(getattr(out,'content',out)).strip().lower()
    # Parse comma-separated labels
    intents = [lbl.strip() for lbl in label_str.split(',') if lbl.strip()]
    if not intents:
        # fallback: use first word if no comma found
        intents = [label_str.split()[0]] if label_str else []

    state["intent"] = intents if len(intents) > 1 else intents[0]
    
    # Log intent classification
    from ...infrastructure.observability import get_observability_manager
    observability = get_observability_manager()
    logger = observability.get_logger("graph.intent")
    logger.info("Intent classified", 
               question=state['question'][:100], 
               classified_intent=state["intent"])
    
    # Record metric
    # Record metric for each classified intent
    if isinstance(state["intent"], list):
        for intent in state["intent"]:
            observability.record_metric(
                "counter", "intent_classifications_total", 1,
                {"intent": intent}
            )
    else:
        observability.record_metric(
            "counter", "intent_classifications_total", 1,
            {"intent": state["intent"]}
        )
    
    return state