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

# --- Import LangChainChatService ---
try:
    from services.treasury_service.langchain import LangChainChatService
    langchain_chat_service = LangChainChatService()
except ImportError:
    langchain_chat_service = None

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


# --- Updated /chat/message endpoint to use LangChainChatService ---
@app.post("/chat/message")
async def chat_message(message: dict):
    """Treasury chat endpoint using LangChainChatService."""
    original_message = message.get("query") or message.get("message") or ""
    now = datetime.now().isoformat()
    user_entry = {"id": f"msg-{int(datetime.now().timestamp()*1000)}-u", "role": "user", "content": original_message, "timestamp": now}
    _add_history(user_entry)

    if not langchain_chat_service:
        return {"error": "LangChainChatService not available. Please check installation."}

    # Call LangChainChatService to process the chat message
    try:
        result = await langchain_chat_service.process_chat_with_memory(
            question=original_message,
            user_id="demo_user",  # Replace with actual user if available
            entity=None,
            user_role="user"
        )
        assistant_entry = {
            "id": f"msg-{int(datetime.now().timestamp()*1000)}-a",
            "role": "assistant",
            "content": result.get("formatted_response", result.get("result", "I'm sorry, I couldn't process that request.")),
            "timestamp": datetime.now().isoformat()
        }
        _add_history(assistant_entry)
        return assistant_entry
    except Exception as e:
        assistant_entry = {
            "id": f"msg-{int(datetime.now().timestamp()*1000)}-a",
            "role": "assistant",
            "content": f"I'm sorry, I encountered an error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        _add_history(assistant_entry)
        return assistant_entry

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