"""
Treasury Service - Simplified Startup

Enterprise treasury service with minimal dependencies for testing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime

# Create a simple FastAPI app for testing
app = FastAPI(
    title="Treasury Service", 
    version="1.0.0",
    description="Enterprise Treasury Management Microservice"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "treasury-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "enterprise_architecture": "active"
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Treasury Enterprise Service",
        "status": "running",
        "architecture": "Domain-Driven Microservices",
        "version": "1.0.0"
    }

@app.get("/test/mock-api")
async def test_mock_api():
    """Test endpoint to verify MockBankAPI functionality."""
    try:
        from .tools.mock_bank_api import MockBankAPI
        api = MockBankAPI()
        
        # Test basic functionality
        balances = api.get_account_balances("ENT-01")
        payments = api.list_payments("ENT-01")
        
        return {
            "mock_api_status": "working",
            "sample_balances_count": len(balances),
            "sample_payments_count": len(payments),
            "first_balance_account": list(balances.keys())[0] if balances else None,
            "first_balance_amount": list(balances.values())[0] if balances else None
        }
    except ImportError as e:
        return {
            "mock_api_status": "import_error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "mock_api_status": "error", 
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )