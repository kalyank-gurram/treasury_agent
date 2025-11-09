"""Payment approval node for Treasury Agent."""

import re
from treasury_agent.graph.types import AgentState
from treasury_agent.graph.nodes.utils import api

def node_approve(state: AgentState):
    """Approve payments by payment ID or list pending payments."""
    m = re.search(r"PMT-\d{5}", state["question"])
    if not m:
        state["notes"] = "No payment id found; listing pending."
        state["result"] = api.list_payments(status="PENDING").head(20).to_dict(orient="records")
        return state
    ok = api.approve_payment(m.group(0))
    state["result"] = {"approved": ok, "payment_id": m.group(0)}
    return state