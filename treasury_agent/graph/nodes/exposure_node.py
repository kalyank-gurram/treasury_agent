"""Counterparty exposure analysis node for Treasury Agent."""

from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_exposure(state: AgentState):
    """Analyze counterparty exposure and risk concentrations."""
    df = api.get_counterparty_exposure(state.get("entity"))
    state["result"] = df.head(50).to_dict(orient="records")
    return state