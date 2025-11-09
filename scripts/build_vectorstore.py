import os
from dotenv import load_dotenv
load_dotenv()
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

BASE = os.path.dirname(os.path.dirname(__file__))
DOCS = os.path.join(BASE, "rag", "docs")
STORE = os.path.join(BASE, "rag", "faiss_store")

def build():
    # Validate key early to provide clearer error
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set. Populate .env then retry.")
    
    files = [os.path.join(DOCS, f) for f in os.listdir(DOCS) if f.endswith(".md")]
    docs = []
    for fp in files:
        docs.extend(TextLoader(fp).load())
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    splits = splitter.split_documents(docs)
    
    # Use proper LangChain OpenAI embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    
    vs = FAISS.from_documents(splits, embeddings)
    os.makedirs(STORE, exist_ok=True)
    vs.save_local(STORE)
    print("Built FAISS store at", STORE)

if __name__ == "__main__":
    build()