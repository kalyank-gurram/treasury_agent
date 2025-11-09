#!/usr/bin/env bash

# Treasury Service - Simple & Reliable Startup
# This script avoids the uvicorn reload issues by using a simpler approach

echo "🚀 Starting Treasury Enterprise Service..."
echo "🌐 URL: http://localhost:8005"

cd /Users/kalyan.gurram/workspace/learning/agentic-projects/treasury_agent

# Start the service with uvicorn directly
exec .venv/bin/python -m uvicorn services.treasury_service.enhanced_app:app --host 0.0.0.0 --port 8005