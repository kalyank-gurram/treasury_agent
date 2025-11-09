"""Anomaly detection node for Treasury Agent."""

from treasury_agent.detectors.anomaly import outflow_anomalies
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_anomalies(state: AgentState):
    """Detect anomalous outflows in cash flow data."""
    hist = api.get_daily_series(state.get("entity"))
    df = outflow_anomalies(hist)
    state["result"] = df.tail(50).reset_index().rename(columns={"index":"date"}).to_dict(orient="records")
    return state