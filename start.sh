#!/usr/bin/env bash

# Treasury Service - Simple Startup Script
# Always uses port 8000 and kills any existing process on that port

echo "🚀 Starting Treasury Service on port 8000..."

# Kill any process using port 8000
echo "🔄 Clearing port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "✅ Port 8000 is available"

# Start the service
echo "🌐 Treasury Service: http://localhost:8000"
exec .venv/bin/python -m uvicorn services.treasury_service.enhanced_app:app --port 8000 --reload