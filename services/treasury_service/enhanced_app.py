"""
Enhanced Treasury Service with MockBankAPI

Enterprise treasury service with all key endpoints for testing integration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add the workspace root to Python path for imports
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, workspace_root)

# Create FastAPI app
app = FastAPI(
    title="Treasury Enterprise Service", 
    version="1.0.0",
    description="Enterprise Treasury Management Microservice with MockBankAPI"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# In-memory chat history (rolling window)
CHAT_HISTORY: List[Dict] = []
MAX_CHAT_HISTORY = 100

def _add_history(entry: Dict):
    CHAT_HISTORY.append(entry)
    if len(CHAT_HISTORY) > MAX_CHAT_HISTORY:
        # drop oldest
        CHAT_HISTORY.pop(0)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "treasury-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "enterprise_architecture": "active",
        "apis": ["health", "root", "mock-api", "analytics"]
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Treasury Enterprise Service",
        "status": "running",
        "architecture": "Domain-Driven Microservices",
        "version": "1.0.0",
        "endpoints": ["/health", "/", "/test/mock-api", "/analytics/summary"]
    }

@app.get("/test/mock-api")
async def test_mock_api():
    """Test MockBankAPI functionality without LLM calls."""
    try:
        from tools.mock_bank_api import MockBankAPI
        api = MockBankAPI()
        
        # Test basic functionality
        balances = api.get_account_balances("ENT-01")
        payments = api.list_payments("ENT-01")
        
        return {
            "mock_api_status": "working",
            "sample_balances_count": len(balances),
            "sample_payments_count": len(payments),
            "first_balance_account": list(balances.keys())[0] if balances else None,
            "first_balance_amount": list(balances.values())[0] if balances else None,
            "enterprise_integration": "successful"
        }
    except ImportError as e:
        return {
            "mock_api_status": "import_error",
            "error": str(e),
            "note": "MockBankAPI may need data generation"
        }
    except Exception as e:
        return {
            "mock_api_status": "error", 
            "error": str(e)
        }

@app.get("/analytics/summary")
async def analytics_summary():
    """Basic analytics summary for frontend dashboard."""
    # Return demo analytics data without relying on mock_bank_api
    return {
        "analytics_status": "active",
        "total_balance": 15_750_000,
        "currency": "USD", 
        "total_accounts": 12,
        "pending_payments": 3,
        "approved_payments": 8,
        "monthly_inflow": 2_500_000,
        "monthly_outflow": 1_800_000,
        "cash_position": {
            "checking": 5_200_000,
            "savings": 8_300_000, 
            "investments": 2_250_000
        },
        "recent_transactions": [
            {"date": "2025-11-10", "amount": 50000, "type": "outflow", "description": "Supplier payment"},
            {"date": "2025-11-09", "amount": 125000, "type": "inflow", "description": "Customer payment"},
            {"date": "2025-11-08", "amount": 75000, "type": "outflow", "description": "Equipment purchase"}
        ],
        "timestamp": datetime.now().isoformat(),
        "enterprise_analytics": "operational"
    }

# Authentication endpoints
@app.post("/auth/login")
async def login(credentials: dict):
    """Demo login endpoint - accepts cfo/demo123 and other demo users."""
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    
    # Demo users for testing
    demo_users = {
        "cfo": {"role": "cfo", "name": "Chief Financial Officer", "permissions": "all"},
        "manager": {"role": "manager", "name": "Treasury Manager", "permissions": "manage"},
        "analyst": {"role": "analyst", "name": "Treasury Analyst", "permissions": "view"},
        "admin": {"role": "admin", "name": "Administrator", "permissions": "all"}
    }
    
    if username in demo_users and password == "demo123":
        user_info = demo_users[username]
        return {
            "access_token": f"demo_token_{username}_{datetime.now().timestamp()}",
            "token_type": "bearer",
            "user": {
                "username": username,
                "role": user_info["role"],
                "name": user_info["name"],
                "permissions": user_info["permissions"]
            },
            "message": f"Welcome, {user_info['name']}!"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/auth/me")
async def get_current_user():
    """Get current user info - demo endpoint."""
    return {
        "username": "cfo",
        "role": "cfo", 
        "name": "Chief Financial Officer",
        "permissions": "all"
    }

@app.post("/auth/logout")
async def logout():
    """Demo logout endpoint."""
    return {"message": "Successfully logged out"}

# Additional endpoints for frontend integration
@app.get("/payments")
async def get_payments():
    """Get sample payment data for frontend."""
    # Return array directly as frontend expects payments.map()
    return [
        {
            "id": "1", 
            "amount": 50000, 
            "currency": "USD", 
            "status": "pending", 
            "recipient": "Supplier A",
            "description": "Raw materials payment",
            "created_at": "2025-11-10T10:00:00Z"
        },
        {
            "id": "2", 
            "amount": 25000, 
            "currency": "USD", 
            "status": "approved", 
            "recipient": "Contractor B",
            "description": "Construction services",
            "created_at": "2025-11-09T15:30:00Z"
        },
        {
            "id": "3", 
            "amount": 75000, 
            "currency": "EUR", 
            "status": "processing", 
            "recipient": "Vendor C",
            "description": "Equipment purchase",
            "created_at": "2025-11-08T09:15:00Z"
        },
        {
            "id": "4", 
            "amount": 120000, 
            "currency": "USD", 
            "status": "rejected", 
            "recipient": "Supplier D",
            "description": "Office supplies - over budget",
            "created_at": "2025-11-07T14:45:00Z"
        }
    ]

@app.post("/payments/{payment_id}/approve")
async def approve_payment(payment_id: str):
    """Approve a payment - demo endpoint."""
    return {
        "id": payment_id,
        "status": "approved",
        "message": f"Payment {payment_id} has been approved",
        "approved_at": datetime.now().isoformat()
    }

@app.post("/payments/{payment_id}/reject")
async def reject_payment(payment_id: str, reason: dict = None):
    """Reject a payment - demo endpoint."""
    rejection_reason = reason.get("reason", "Not specified") if reason else "Not specified"
    return {
        "id": payment_id,
        "status": "rejected", 
        "message": f"Payment {payment_id} has been rejected",
        "reason": rejection_reason,
        "rejected_at": datetime.now().isoformat()
    }

@app.get("/chat/history")
async def chat_history():
    """Return recent chat history messages."""
    return {"messages": CHAT_HISTORY}

@app.post("/chat/message")
async def chat_message(message: dict):
    """Treasury chat endpoint with domain intelligence & liquidity risk analysis."""
    # Support both "message" and "query" keys
    original_message = message.get("query") or message.get("message") or ""
    user_message = original_message.lower().strip()

    now = datetime.utcnow().isoformat()
    user_entry = {"id": f"msg-{int(datetime.utcnow().timestamp()*1000)}-u", "role": "user", "content": original_message, "timestamp": now}
    _add_history(user_entry)

    def respond(content: str, data: Dict | None = None):
        entry = {
            "id": f"msg-{int(datetime.utcnow().timestamp()*1000)}-a",
            "role": "assistant",
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if data:
            entry["data"] = data
        _add_history(entry)
        return entry

    if not user_message:
        return respond("Please provide a query. For example: 'latest payment approvals' or 'analyze liquidity risk'.")

    tokens = set(user_message.split())

    # --- Payment approvals ---
    if {"payment", "approve", "approval"} & tokens:
        if {"latest", "recent"} & tokens:
            approvals = [
                {"id": "PAY-001", "amount": 125000, "counterparty": "ABC Corp", "approved_by": "CFO", "date": "2025-11-10"},
                {"id": "PAY-002", "amount": 75000, "counterparty": "XYZ Suppliers", "approved_by": "Manager", "date": "2025-11-09"},
                {"id": "PAY-003", "amount": 200000, "counterparty": "DEF Industries", "approved_by": "CFO", "date": "2025-11-08"},
            ]
            text = "Latest payment approvals:\n" + "\n".join(
                f"- {p['id']}: ${p['amount']:,} to {p['counterparty']} (approved by {p['approved_by']} on {p['date']})" for p in approvals
            )
            return respond(text, {"approvals": approvals})
        if "pending" in tokens or "queue" in tokens or "waiting" in tokens:
            pending = [
                {"id": "PAY-204", "amount": 88000, "counterparty": "Global Parts", "status": "PENDING", "submitted": "2025-11-10"},
                {"id": "PAY-219", "amount": 143000, "counterparty": "Metro Logistics", "status": "PENDING", "submitted": "2025-11-09"},
            ]
            txt = "Pending payments:\n" + "\n".join(
                f"- {p['id']}: ${p['amount']:,} to {p['counterparty']} (submitted {p['submitted']})" for p in pending
            )
            return respond(txt, {"pending": pending})
        return respond("Specify 'latest payment approvals' or include 'pending' to refine your payment query.")

    # --- Cash position ---
    if {"cash", "position", "balance"} & tokens:
        cash_data = {
            "checking": 5_200_000,
            "savings": 8_300_000,
            "investments": 2_250_000,
        }
        total = sum(cash_data.values())
        text = (
            "Current cash position:\n" +
            f"- Checking: ${cash_data['checking']:,}\n" +
            f"- Savings: ${cash_data['savings']:,}\n" +
            f"- Investments: ${cash_data['investments']:,}\n\n" +
            f"Total Balance: ${total:,}"
        )
        return respond(text, {"cash_position": cash_data, "total_balance": total})

    # --- Liquidity / risk analysis ---
    if "liquidity" in tokens or "risk" in tokens or "runway" in tokens or "exposure" in tokens:
        cash_on_hand = 15_750_000
        credit_lines = 5_000_000
        committed_outflows_30d = 6_100_000
        avg_daily_net_outflow = 180_000
        runway_days = round((cash_on_hand + credit_lines - committed_outflows_30d) / avg_daily_net_outflow, 1)
        buffer_ratio = round((cash_on_hand + credit_lines) / committed_outflows_30d, 2)
        stressed_outflow = avg_daily_net_outflow * 1.8
        stressed_runway = round((cash_on_hand + credit_lines - committed_outflows_30d) / stressed_outflow, 1)
        risk_level = "LOW" if buffer_ratio >= 2 else ("MODERATE" if buffer_ratio >= 1.2 else "HIGH")
        text = (
            "Liquidity Risk Analysis:\n"
            f"- Buffer Ratio: {buffer_ratio} (Target ≥ 1.5)\n"
            f"- Base Runway: {runway_days} days\n"
            f"- Stressed Runway: {stressed_runway} days (stress factor 1.8x)\n"
            f"- Credit Lines Available: ${credit_lines:,}\n"
            f"- Risk Level: {risk_level}\n\n"
            "Recommendations:\n"
            "• Reconfirm large upcoming outflows (> $250K)\n"
            "• Consider activating additional short-term credit if runway < 90 days\n"
            "• Accelerate collection on top 10 AR exposures\n"
        )
        data = {
            "buffer_ratio": buffer_ratio,
            "base_runway_days": runway_days,
            "stressed_runway_days": stressed_runway,
            "risk_level": risk_level,
            "credit_lines": credit_lines,
        }
        return respond(text, data)

    # --- KPI metrics ---
    if "kpi" in tokens or "metrics" in tokens:
        kpis = {"dso": 42.3, "dpo": 47.8, "working_capital_ratio": 1.26, "operating_cash_flow_ytd": 12_400_000}
        text = "Working Capital KPIs:\n" + "\n".join(f"- {k}: {v}" for k, v in kpis.items())
        return respond(text, {"kpis": kpis})

    # Fallback help
    return respond(
        "Treasury assistant help:\n"
        "Examples:\n"
        "- latest payment approvals\n"
        "- pending payments\n"
        "- cash position\n"
        "- analyze liquidity risk\n"
        "- show KPIs"
    )

@app.get("/api/frontend-config")
async def frontend_config():
    """Configuration for frontend dashboard."""
    return {
        "api_base_url": "http://localhost:8000",
        "service_name": "Treasury Enterprise Service",
        "version": "1.0.0",
        "features": {
            "analytics": True,
            "payments": True,
            "mock_api": True,
            "real_time": False
        },
        "enterprise_mode": True,
        "demo_users": {
            "cfo": "Chief Financial Officer", 
            "manager": "Treasury Manager",
            "analyst": "Treasury Analyst",
            "admin": "Administrator"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Treasury Enterprise Service...")
    print("📊 Features: Health checks, MockBankAPI, Analytics")
    print("🏗️ Architecture: Domain-Driven Microservices")
    
    uvicorn.run(
        "enhanced_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )