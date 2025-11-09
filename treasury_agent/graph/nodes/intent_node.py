"""Intent classification node for Treasury Agent."""

from treasury_agent.models.llm_router import LLMRouter
from treasury_agent.graph.types import AgentState

def node_intent(state: AgentState):
    """Classify user intent among available Treasury Agent capabilities."""
    llm = LLMRouter().cheap()
    sys = "Classify the user's intent among: balances, forecast, approve_payment, anomalies, kpis, whatifs, exposure, rag_check, narrative."
    prompt = f"{sys}\nUser: {state['question']}\nReturn one label."
    out = llm.invoke(prompt)
    label = str(getattr(out,'content',out)).strip().lower()
    state["intent"] = label.split()[0]
    return state