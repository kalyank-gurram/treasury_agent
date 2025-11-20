"""Main Treasury Agent LangGraph implementation."""

from langgraph.graph import StateGraph, END
from .types import AgentState
from .nodes import (
    node_intent,
    node_balances,
    node_forecast,
    node_approve,
    node_anomalies,
    node_kpis,
    node_whatifs,
    node_exposure,
    node_rag,
    node_narrative,
)
from ..guardrails import guardrails_node

# Mapping of intents to node names
INTENT_NODE_MAPPING = {
    "balances": "balances",
    "forecast": "forecast",
    "approve_payment": "approve",
    "anomalies": "anomalies",
    "kpis": "kpis",
    "whatifs": "whatifs",
    "exposure": "exposure",
    "rag_check": "rag",
    "narrative": "narrative",
}

def build_graph(checkpointer=None):
    """Build and compile the Treasury Agent LangGraph workflow.
    
    Args:
        checkpointer: Optional checkpointer for memory persistence
    """
    g = StateGraph(AgentState)

    # Add all agent nodes
    g.add_node("guardrails", guardrails_node)
    g.add_node("intent", node_intent)
    g.add_node("balances", node_balances)
    g.add_node("forecast", node_forecast)
    g.add_node("approve", node_approve)
    g.add_node("anomalies", node_anomalies)
    g.add_node("kpis", node_kpis)
    g.add_node("whatifs", node_whatifs)
    g.add_node("exposure", node_exposure)
    g.add_node("rag", node_rag)
    g.add_node("narrative", node_narrative)

    # Set entry point to guardrails
    g.set_entry_point("guardrails")
    # Route from guardrails to intent (only if passed)
    def guardrails_route(state):
        if state.get("guardrails_status") == "blocked":
            return END
        return "intent"
    g.add_conditional_edges("guardrails", guardrails_route, {"intent": "intent"})

    # Add conditional edges from intent node to all possible nodes
    for intent_name, node_name in INTENT_NODE_MAPPING.items():
        g.add_edge("intent", node_name)

    # All terminal nodes go to END
    terminal_nodes = list(INTENT_NODE_MAPPING.values())
    for node in terminal_nodes:
        g.add_edge(node, END)
    
    # Compile with optional checkpointer for memory
    if checkpointer:
        return g.compile(checkpointer=checkpointer)
    else:
        return g.compile()