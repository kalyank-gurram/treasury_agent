from fastapi import APIRouter, Query, Depends, HTTPException, Request
from ..tools.mock_bank_api import MockBankAPI
from ..domain.entities.user import User, Permission
from ..infrastructure.security.auth_middleware import AuthMiddleware

router = APIRouter()
api = MockBankAPI()


def get_auth_middleware(request: Request) -> AuthMiddleware:
    """Get auth middleware from DI container."""
    container = request.app.state.container
    return container.get(AuthMiddleware)

@router.get("")
def list_payments(
    request: Request,
    status: str | None = Query(default=None),
    auth_middleware: AuthMiddleware = Depends(get_auth_middleware),
    current_user: User = Depends(lambda r: get_auth_middleware(r).require_permission(Permission.VIEW_TRANSACTIONS)())
):
    """List payments with role-based access control."""
    return api.list_payments(status).to_dict(orient="records")

@router.post("/approve/{payment_id}")
def approve(
    payment_id: str,
    request: Request,
    auth_middleware: AuthMiddleware = Depends(get_auth_middleware),
    current_user: User = Depends(lambda r: get_auth_middleware(r).require_any_permission([
        Permission.APPROVE_PAYMENTS_LOW,
        Permission.APPROVE_PAYMENTS_MED,
        Permission.APPROVE_PAYMENTS_HIGH
    ])())
):
    """
    Approve payment with role-based authorization.
    
    User must have appropriate approval permission based on payment amount.
    """
    # Get payment details to check amount
    payments_df = api.list_payments()
    payment_row = payments_df[payments_df['payment_id'] == payment_id]
    
    if payment_row.empty:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment_amount = payment_row.iloc[0]['amount']
    
    # Check if user can approve this payment amount
    if not current_user.can_approve_payment(payment_amount):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permission to approve payment of ${payment_amount:,.2f}"
        )
    
    ok = api.approve_payment(payment_id)
    return {
        "payment_id": payment_id, 
        "approved": ok,
        "amount": payment_amount,
        "approved_by": current_user.username
    }