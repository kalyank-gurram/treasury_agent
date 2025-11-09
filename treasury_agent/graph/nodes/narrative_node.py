"""Narrative reporting node for Treasury Agent."""

from treasury_agent.detectors.anomaly import outflow_anomalies
from treasury_agent.reports.narrative import daily_cfo_brief
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_narrative(state: AgentState):
    """Generate executive narrative report for CFO briefing."""
    hist = api.get_daily_series(state.get("entity"))
    balances = api.get_account_balances(state.get("entity")).groupby("entity")["balance"].sum().to_dict()
    anomalies = outflow_anomalies(hist).tail(5).to_dict()
    exposure = api.get_counterparty_exposure(state.get("entity")).head(5).to_dict(orient="records")
    metrics = {"balances": balances, "anomalies": anomalies, "top_counterparties": exposure}
    state["result"] = daily_cfo_brief(metrics)
    return state