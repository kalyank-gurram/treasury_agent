"""Balance retrieval node for Treasury Agent."""

from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_balances(state: AgentState):
    """Retrieve account balances for the specified entity."""
    df = api.get_account_balances(state.get("entity"))
    state["result"] = df.head(50).to_dict(orient="records")
    return state