from pydantic import BaseModel

class ChatIn(BaseModel):
    question: str
    entity: str | None = None

class ChatOut(BaseModel):
    intent: str
    result: dict | list | str | None = None
    notes: str | None = None