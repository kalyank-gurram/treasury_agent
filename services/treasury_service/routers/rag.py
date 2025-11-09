from fastapi import APIRouter, Query
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

router = APIRouter()

@router.get("/search")
def search(q: str = Query(..., description="Query text")):
    BASE = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    store = os.path.join(BASE, "rag", "faiss_store")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vs = FAISS.load_local(store, embeddings, allow_dangerous_deserialization=True)
    docs = vs.similarity_search(q, k=4)
    return [{"content": d.page_content} for d in docs]