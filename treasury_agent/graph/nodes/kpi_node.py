"""KPI calculation node for Treasury Agent."""

from treasury_agent.kpis.working_capital import dso_dpo
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_kpis(state: AgentState):
    """Calculate working capital KPIs (DSO and DPO)."""
    led = api.get_ledger(state.get("entity"))
    dso, dpo = dso_dpo(led)
    state["result"] = {"DSO": dso, "DPO": dpo}
    return state