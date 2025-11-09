"""What-if scenario analysis node for Treasury Agent."""

import pandas as pd
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_whatifs(state: AgentState):
    """Run what-if scenario by shifting AP dates by 7 days."""
    tx = api.transactions.copy()
    tx["date"] = pd.to_datetime(tx["date"])
    ap = tx[tx["category"]=="AP"].copy()
    ap["date"] = ap["date"] + pd.Timedelta(days=7)
    others = tx[tx["category"]!="AP"]
    new = pd.concat([others, ap])
    daily = new.groupby(new["date"].dt.date)["amount"].sum()
    state["result"] = {"what_if_daily": daily.tail(60).to_dict()}
    return state