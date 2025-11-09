"""RAG-based policy search node for Treasury Agent."""

import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from ...models.llm_router import LLMRouter
from ..types import AgentState

def node_rag(state: AgentState):
    """Search policy documents using RAG and answer questions."""
    BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    store = os.path.join(BASE, "rag", "faiss_store")
    if not os.path.isdir(store):
        state["result"] = "RAG store not built yet. Run: poetry run python scripts/build_vectorstore.py"
        return state
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vs = FAISS.load_local(store, embeddings, allow_dangerous_deserialization=True)
    llm = LLMRouter().primary()
    query = state["question"]
    docs = vs.similarity_search(query, k=4)
    ctx = "\n\n---\n\n".join([d.page_content for d in docs])
    prompt = f"Context:\n{ctx}\n\nUser question: {query}\nAnswer succinctly and cite policy clauses."
    out = llm.invoke(prompt)
    state["result"] = str(getattr(out,'content',out))
    return state