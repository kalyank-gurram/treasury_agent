from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from .routers import chat, analytics, payments, rag, auth
from .infrastructure.config.settings import get_config
from .infrastructure.di.config import configure_dependencies
from .infrastructure.events.event_bus import configure_event_bus
from .infrastructure.observability import (
    configure_observability,
    get_health_monitor,
    configure_default_health_checks,
    get_observability_manager
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    config = get_config()
    
    # Configure infrastructure
    container = configure_dependencies()
    event_bus = configure_event_bus()
    observability = configure_observability(config.observability)
    health_monitor = configure_default_health_checks()
    
    # Store in app state
    app.state.container = container
    app.state.event_bus = event_bus
    app.state.observability = observability
    app.state.health_monitor = health_monitor
    
    logger = observability.get_logger("app")
    logger.info("Treasury Agent API started", version="0.2.0", environment=config.environment.value)
    
    yield
    
    # Shutdown
    logger.info("Treasury Agent API shutting down")


app = FastAPI(
    title="Treasury Agent API", 
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS middleware with security settings
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


# Global exception handler with observability
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging."""
    observability = get_observability_manager()
    logger = observability.get_logger("app.errors")
    
    logger.error(
        "Unhandled exception in API request",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc)
    )
    
    # Record error metric
    observability.record_metric(
        "counter", "api_errors_total", 1,
        {"path": request.url.path, "method": request.method, "error_type": type(exc).__name__}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Application health check."""
    health_monitor = get_health_monitor()
    return await health_monitor.run_all_checks()


@app.get("/health/ready")
async def readiness_check():
    """Application readiness check."""
    health_monitor = get_health_monitor()
    return await health_monitor.get_readiness()


@app.get("/test/mock-api")
def test_mock_api():
    """Test endpoint to verify MockBankAPI functionality."""
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


@app.get("/health/live")
async def liveness_check():
    """Application liveness check."""
    health_monitor = get_health_monitor()
    return health_monitor.get_liveness()


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Application metrics."""
    observability = get_observability_manager()
    return observability.get_metrics_snapshot()


# Include routers
app.include_router(auth.router)
app.include_router(chat.router, prefix="/chat")
app.include_router(analytics.router, prefix="/analytics")
app.include_router(payments.router, prefix="/payments")
app.include_router(rag.router, prefix="/rag")


if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "services.treasury_service.app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        workers=1 if config.debug else config.workers
    )