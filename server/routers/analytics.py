from fastapi import APIRouter, Query
from treasury_agent.tools.mock_bank_api import MockBankAPI
from treasury_agent.detectors.anomaly import outflow_anomalies

router = APIRouter()
api = MockBankAPI()

@router.get("/balances")
def balances(entity: str | None = Query(default=None)):
    return api.get_account_balances(entity).to_dict(orient="records")

@router.get("/anomalies")
def anomalies(entity: str | None = Query(default=None)):
    s = api.get_daily_series(entity)
    df = outflow_anomalies(s).reset_index().rename(columns={"index":"date"})
    return df.to_dict(orient="records")