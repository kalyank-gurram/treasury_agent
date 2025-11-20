# Treasury Agent - LangGraph Multi-Agent System

**Enterprise Treasury Management powered by LangGraph** featuring intelligent agent workflows for cash management, forecasting, and analytics.

## 🤖 **LangGraph Agent Architecture**
- **Multi-Node Workflow:** 10 specialized nodes with intelligent routing
- **State Management:** Persistent conversation memory and context
- **Intent Classification:** Automatic routing to appropriate treasury functions
- **Agent Nodes:** balances, forecast, approve, anomalies, kpis, whatifs, exposure, rag, narrative

## 🏗️ **Core Components**
- **`services/treasury_service/`** - Main FastAPI service with LangGraph integration
- **`services/treasury_service/graph/`** - LangGraph workflow definitions and nodes
- **`services/treasury_service/models/`** - LLM routing and model management
- **`services/treasury_service/forecasting/`** - ARIMA & GradientBoost forecasting models
- **`services/treasury_service/kpis/`** - Working capital analytics (DSO/DPO)
- **`services/treasury_service/detectors/`** - Anomaly detection algorithms
- **`rag/`** - RAG system with FAISS vectorstore for policy search
- **`apps/treasury-dashboard/`** - Next.js React dashboard

## 🚀 **Treasury Capabilities**  
- **LangGraph Workflow:** 10-node intelligent agent system
- **Mock Data Generation:** ~30k realistic treasury transactions (5-second setup)
- **Forecasting Models:** ARIMA + GradientBoost for cash flow prediction
- **Anomaly Detection:** Statistical outlier detection for transactions
- **Working Capital KPIs:** DSO/DPO analytics and liquidity modeling
- **RAG System:** FAISS-powered policy document search
- **Chat Interface:** Natural language treasury assistant
- **Real-time Analytics:** Live treasury metrics and reporting

## Quickstart

### Prerequisites
```bash
poetry install
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Frontend dependencies
cd apps/treasury-dashboard && npm install
```

### One-Command Setup (Recommended)
```bash
poetry run python scripts/setup.py
```

### Manual Setup (Alternative)
```bash
# Run these setup scripts only ONCE (first time or when files are missing)
poetry run python scripts/generate_mock_data.py
poetry run python scripts/build_vectorstore.py
```

### Start Services

**✅ Quick Start Commands**
```bash
# Start treasury service (port 8000, auto-restarts on changes)
./start.sh

# Start frontend dashboard (in another terminal)
cd apps/treasury-dashboard && npm run dev
```

**Manual Startup (Alternative)**
```bash
# Direct uvicorn command
.venv/bin/python -m uvicorn services.treasury_service.enhanced_app:app --port 8000 --reload
```

**Access the backend at:** `http://localhost:8000`  
**Access the frontend at:** `http://localhost:3000`

### 🔐 **Access URLs**
- **Backend API:** `http://localhost:8000` (FastAPI with LangGraph)
- **Frontend Dashboard:** `http://localhost:3000` (Next.js React)
- **API Documentation:** `http://localhost:8000/docs` (Interactive Swagger UI)

## Data Generation

The mock data script generates realistic treasury datasets:
- **Accounts:** 50 accounts across 10 entities
- **Transactions:** ~12k transactions over 6 months
- **Payments:** 2k payment records
- **AR/AP:** 15k receivables/payables entries
- **Counterparties:** 700 business partners

**Performance:** Completes in ~5 seconds (optimized from original 900-day dataset)

## Enterprise Architecture

### 🏗️ **Project Structure**
```
treasury_agent/
├── services/treasury_service/      # Main FastAPI service
│   ├── enhanced_app.py            # FastAPI application entry point
│   ├── graph/                     # LangGraph workflow system
│   │   ├── graph.py              # Main workflow orchestration
│   │   ├── nodes/                # Individual agent nodes
│   │   └── types.py              # State definitions
│   ├── models/                    # LLM model management
│   ├── forecasting/              # ARIMA & GradientBoost models
│   ├── kpis/                     # Working capital analytics
│   ├── detectors/                # Anomaly detection
│   ├── routers/                  # FastAPI route handlers
│   └── tools/                    # Utility functions
├── apps/treasury-dashboard/       # Next.js React frontend
├── rag/                          # RAG system & vectorstore
│   ├── docs/                     # Policy documents
│   └── faiss_store/              # FAISS vector database
├── data/                         # Generated mock datasets
├── scripts/                      # Setup & data generation
└── start.sh                     # Quick startup script
```

### 🎯 **Key Components**
- **`services/treasury_service/enhanced_app.py`**: Main FastAPI server with all endpoints
- **`services/treasury_service/graph/graph.py`**: LangGraph workflow with 10 specialized nodes
- **`apps/treasury-dashboard/`**: Next.js React dashboard with TypeScript
- **`rag/`**: RAG system with FAISS vectorstore for policy document search
- **`data/`**: Auto-generated realistic treasury datasets for testing

## 🌐 **API Endpoints**

- **`/chat/message`** - Main LangGraph agent interaction
- **`/chat/history`** - Conversation history retrieval
- **`/analytics/*`** - Treasury analytics and KPIs
- **`/payments/*`** - Payment processing with MockBankAPI
- **`/rag/search`** - Policy document search via RAG
- **`/health`** - Service health check

### 🔎 **LangGraph Agent Queries**

The LangGraph agent automatically routes queries to appropriate nodes:

```bash
# Cash balances & positions
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"show cash balances"}'

# Forecasting & predictions  
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"forecast next month cash flow"}'

# Working capital KPIs
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"calculate DSO and DPO"}'

# Anomaly detection
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"find transaction anomalies"}'

# RAG policy search
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"payment approval policies"}'

# Chat history (last 100 messages)
curl http://localhost:8000/chat/history | jq
```

**LangGraph Response Structure:**
- `content`: Human-readable agent response
- `data`: Structured data (balances, forecasts, KPIs, etc.)
- `intent`: Detected intent and routing decision
- `metadata`: Agent execution details

## Deploy

See `deploy/Dockerfile` and `deploy/Procfile` for containerized deployment. For Hugging Face Spaces, run both server and UI together or host backend separately.

Quickstart
poetry install
cp .env.example .env

# Run these setup scripts only ONCE (first time or when files are missing)
poetry run python scripts/generate_mock_data.py
poetry run python scripts/build_vectorstore.py

# Start backend and UI
poetry run uvicorn server.app:app --reload --port 8000
poetry run python ui/gradio_app.py

Setup Script (Recommended)

Instead of manually running the data and vectorstore scripts each time, you can use this helper setup command:

poetry run python scripts/setup.py


This script automatically:

Checks if mock data already exists under /data/

Checks if the FAISS vectorstore exists under /rag/faiss_store/

Regenerates only what’s missing

It’s completely safe to run multiple times — it skips anything already built.

Example output:

Treasury Agent setup starting...

Mock data already exists — skipping.
No FAISS store found — building vectorstore...

Setup complete! You can now run:
   poetry run uvicorn server.app:app --reload --port 8000
   poetry run python ui/gradio_app.py

## Setup Scripts Overview

| Script | Purpose | Run When |
|--------|---------|----------|
| `scripts/setup.py` | **Smart setup** - checks and builds only what's missing | **Recommended** - safe to run anytime |
| `scripts/generate_mock_data.py` | Generates synthetic datasets (~30k records in ~5 seconds) | First setup only, or if `/data/` is missing |
| `scripts/build_vectorstore.py` | Builds FAISS vector store for policy RAG | First setup only, or if `/rag/docs/` changed |

**Daily Development:**
```bash
# Terminal 1 - Treasury Service
./start.sh

# Terminal 2 - Dashboard Frontend  
cd apps/treasury-dashboard && npm run dev
```

## Architecture Overview

- **`server/routers/*`** - FastAPI controllers (REST endpoints)
- **`server/services/*`** - Domain logic that calls treasury_agent modules  
- **`treasury_agent/*`** - Core agent intelligence (LangGraph, forecasting, RAG, KPIs, etc.)
- **`ui/`** - Gradio thin client (decoupled, can be replaced with Next.js or React)
- **`scripts/`** - Setup and data generation utilities
- **`deploy/`** - Docker and Procfile for containerized deployment

## Generated Data Overview

The optimized mock data generation creates:
- **50 accounts** across 10 entities  
- **~12k transactions** over 6 months (180 days)
- **2k payment records** with various statuses
- **15k AR/AP entries** for DSO/DPO calculations
- **700 counterparties** with risk ratings

**Performance:** ~5 seconds execution time (optimized from original 900-day dataset)

## Deploy

For cloud deployment or Hugging Face Spaces:

**Option 1:** Single container with both backend and frontend
**Option 2:** Separate backend deployment with frontend pointing to remote server

See `deploy/Dockerfile` and `deploy/Procfile` for examples.

### Container Setup Tip

Include the automated setup in your container build:

```dockerfile
RUN poetry run python scripts/setup.py
```

This ensures every environment has mock data and the vectorstore prebuilt before startup.

## API Endpoints

- **`/chat`** - Main agent interaction endpoint
- **`/analytics`** - Treasury analytics and KPIs  
- **`/payments`** - Payment processing operations
- **`/rag/search`** - Policy document search