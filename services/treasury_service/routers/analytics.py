from fastapi import APIRouter, Query, Depends, HTTPException, Request
from ..tools.mock_bank_api import MockBankAPI
from ..detectors.anomaly import outflow_anomalies
from ..domain.entities.user import User, Permission
from ..infrastructure.security.auth_middleware import AuthMiddleware

router = APIRouter()
api = MockBankAPI()


def get_auth_middleware(request: Request) -> AuthMiddleware:
    """Get auth middleware from DI container."""
    container = request.app.state.container
    return container.get(AuthMiddleware)

@router.get("/balances")
def balances(
    request: Request,
    entity: str | None = Query(default=None),
    auth_middleware: AuthMiddleware = Depends(get_auth_middleware),
    current_user: User = Depends(lambda r: get_auth_middleware(r).require_permission(Permission.VIEW_BALANCES)())
):
    """Get account balances with entity access control."""
    # Check entity access if entity is specified
    if entity and not current_user.can_access_entity(entity):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to entity: {entity}"
        )
    
    return api.get_account_balances(entity).to_dict(orient="records")

@router.get("/anomalies")
def anomalies(
    request: Request,
    entity: str | None = Query(default=None),
    auth_middleware: AuthMiddleware = Depends(get_auth_middleware),
    current_user: User = Depends(lambda r: get_auth_middleware(r).require_permission(Permission.VIEW_ANALYTICS)())
):
    """Get anomaly detection results with entity access control."""
    # Check entity access if entity is specified
    if entity and not current_user.can_access_entity(entity):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to entity: {entity}"
        )
    
    s = api.get_daily_series(entity)
    df = outflow_anomalies(s).reset_index().rename(columns={"index":"date"})
    return df.to_dict(orient="records")