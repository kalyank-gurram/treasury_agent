from fastapi import FastAPI
from server.routers import chat, analytics, payments, rag

app = FastAPI(title="Treasury Agent API", version="0.2.0")

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])