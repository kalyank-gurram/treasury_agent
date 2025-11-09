#!/usr/bin/env bash

# Treasury Enterprise Service Startup Script
# Convenient script to start the treasury service with proper virtual environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Treasury Enterprise Service Startup${NC}"
echo -e "${BLUE}======================================${NC}"

# Get the script directory and workspace root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
TREASURY_SERVICE_DIR="$WORKSPACE_ROOT/services/treasury_service"
VENV_PYTHON="$WORKSPACE_ROOT/.venv/bin/python"

echo -e "${YELLOW}📁 Workspace: $WORKSPACE_ROOT${NC}"
echo -e "${YELLOW}🐍 Python: $VENV_PYTHON${NC}"
echo -e "${YELLOW}📦 Service: $TREASURY_SERVICE_DIR${NC}"

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PYTHON${NC}"
    echo -e "${YELLOW}💡 Please run: poetry install${NC}"
    exit 1
fi

# Check if treasury service directory exists
if [ ! -d "$TREASURY_SERVICE_DIR" ]; then
    echo -e "${RED}❌ Treasury service directory not found: $TREASURY_SERVICE_DIR${NC}"
    exit 1
fi

# Check if enhanced_app.py exists
if [ ! -f "$TREASURY_SERVICE_DIR/enhanced_app.py" ]; then
    echo -e "${RED}❌ enhanced_app.py not found in $TREASURY_SERVICE_DIR${NC}"
    echo -e "${YELLOW}💡 Falling back to simple_app.py${NC}"
    APP_FILE="simple_app.py"
else
    APP_FILE="enhanced_app.py"
fi

echo -e "${GREEN}✅ Starting Treasury Service...${NC}"
echo -e "${BLUE}📊 Features: Health checks, MockBankAPI, Analytics${NC}"
echo -e "${BLUE}🏗️ Architecture: Domain-Driven Microservices${NC}"
echo -e "${BLUE}🌐 URL: http://localhost:8004${NC}"
echo ""

# Change to service directory and start the service
cd "$TREASURY_SERVICE_DIR"
exec "$VENV_PYTHON" "$APP_FILE"