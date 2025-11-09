"""Test helper to properly initialize FastAPI app for testing."""

from fastapi.testclient import TestClient
from .app import app
from .infrastructure.config.settings import get_config
from .infrastructure.di.config import configure_dependencies
from .infrastructure.events.event_bus import configure_event_bus
from .infrastructure.observability import (
    configure_observability,
    get_health_monitor,
    configure_default_health_checks
)


def get_test_client() -> TestClient:
    """Get a properly configured test client with DI container."""
    
    # Manually configure app state (since TestClient doesn't trigger lifespan)
    if not hasattr(app.state, 'container'):
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
    
    return TestClient(app)


def test_endpoints():
    """Test various API endpoints."""
    client = get_test_client()
    
    print("🧪 Testing API endpoints with proper DI setup...")
    print()
    
    # Test health endpoint
    health_response = client.get('/health')
    print(f"✅ Health endpoint: {health_response.status_code}")
    if health_response.status_code == 200:
        print(f"   Response: {health_response.json()}")
    print()
    
    # Test metrics endpoint
    metrics_response = client.get('/metrics')
    print(f"✅ Metrics endpoint: {metrics_response.status_code}")
    print()
    
    # Test unauthenticated auth endpoint (should return 401)
    auth_response = client.get('/auth/me')
    print(f"✅ Auth /me endpoint (no auth): {auth_response.status_code}")
    print(f"   Expected 401, got: {auth_response.status_code}")
    print()
    
    # Test chat endpoint without auth (should return 401)
    chat_response = client.post('/chat/message', json={
        'message': 'What is the current cash position?'
    })
    print(f"✅ Chat endpoint (no auth): {chat_response.status_code}")
    print(f"   Expected 401, got: {chat_response.status_code}")
    print()
    
    # Test registration endpoint
    register_response = client.post('/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'full_name': 'Test User',
        'role': 'viewer'
    })
    print(f"✅ Auth register: {register_response.status_code}")
    if register_response.status_code not in [200, 201]:
        print(f"   Response: {register_response.json()}")
    print()
    
    return client


if __name__ == "__main__":
    test_endpoints()