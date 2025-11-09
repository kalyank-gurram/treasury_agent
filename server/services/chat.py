from treasury_agent.graph.graph import build_graph

graph = build_graph()

def run_chat(question: str, entity: str | None = None):
    state = {"question": question, "entity": entity or ""}
    final = graph.invoke(state)
    return {
        "intent": final.get("intent",""),
        "result": final.get("result"),
        "notes": final.get("notes","")
    }