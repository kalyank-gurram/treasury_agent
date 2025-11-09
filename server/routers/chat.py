from fastapi import APIRouter
from server.schemas.chat import ChatIn, ChatOut
from server.services.chat import run_chat

router = APIRouter()

@router.post("", response_model=ChatOut)
def chat(inp: ChatIn):
    res = run_chat(inp.question, inp.entity)
    return res