#!/usr/bin/env bash
set -e

echo "🚀 Starting Treasury Agent Application"
echo "================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your API keys before running in production!"
fi

# Install dependencies if needed
if [ ! -d ".venv" ] && [ ! -f "poetry.lock" ]; then
    echo "📦 Installing dependencies..."
    poetry install
fi

echo "🔍 Checking application health..."
poetry run python -c "
echo "Starting Treasury Agent API Server..."

# Import the FastAPI app from services module
from services.treasury_service.app import app
print('✅ Application imports successfully')
print('🎯 Treasury Agent is ready to start!')
"

echo ""
echo "🌟 Starting Treasury Agent Server..."
echo "   - API: http://127.0.0.1:8000"
echo "   - Health: http://127.0.0.1:8000/health" 
echo "   - Metrics: http://127.0.0.1:8000/metrics"
echo "   - Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
poetry run python server/app.py