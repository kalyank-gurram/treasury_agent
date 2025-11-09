"""Main Treasury Agent LangGraph implementation."""

from langgraph.graph import StateGraph, END
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes import (
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

def route(state: AgentState):
    """Route to appropriate node based on classified intent."""
    intent = state.get("intent","")
    mapping = {
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
    return mapping.get(intent, "balances")

def build_graph():
    """Build and compile the Treasury Agent LangGraph workflow."""
    g = StateGraph(AgentState)
    
    # Add all nodes
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

    # Set entry point and routing
    g.set_entry_point("intent")
    g.add_conditional_edges("intent", route, {
        "balances": "balances",
        "forecast": "forecast",
        "approve": "approve",
        "anomalies": "anomalies",
        "kpis": "kpis",
        "whatifs": "whatifs",
        "exposure": "exposure",
        "rag": "rag",
        "narrative": "narrative",
    })
    
    # All terminal nodes end the workflow
    terminal_nodes = ["balances", "forecast", "approve", "anomalies", "kpis", 
                     "whatifs", "exposure", "rag", "narrative"]
    for node in terminal_nodes:
        g.add_edge(node, END)
    
    return g.compile()