from fastapi import APIRouter, Query
from treasury_agent.tools.mock_bank_api import MockBankAPI

router = APIRouter()
api = MockBankAPI()

@router.get("")
def list_payments(status: str | None = Query(default=None)):
    return api.list_payments(status).to_dict(orient="records")

@router.post("/approve/{payment_id}")
def approve(payment_id: str):
    ok = api.approve_payment(payment_id)
    return {"payment_id": payment_id, "approved": ok}