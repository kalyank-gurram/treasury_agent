# Treasury Enterprise Workspace

**Enterprise-grade Domain-Driven Microservices architecture** for treasury & cash management featuring:

## 🏗️ **Enterprise Architecture**
- **Microservices:** Domain-bounded services with clear boundaries  
- **Monorepo:** Organized workspace with `services/`, `apps/`, `shared/`, `config/`
- **Environment Separation:** Local, development, staging, production configs
- **Event-Driven:** Async communication between service boundaries

## 🚀 **Treasury Capabilities**  
- **LangGraph** intelligent routing + domain subgraphs (9+ use cases)
- **Large datasets** (optimized ~30k transactions, 5-second generation)
- **Forecasting** (ARIMA + GradientBoost models)
- **Anomaly detection** (statistical outlier detection)
- **Working-capital KPIs** (DSO/DPO analytics)
- **Liquidity modeling** with scenario analysis
- **Counterparty exposure** management
- **RAG-powered** policy search
- **Narrative reporting** with automated insights

## 🎯 **Modern Frontend**
- **Next.js Dashboard** (React, TypeScript, Tailwind CSS)
- **Role-based authentication** and authorization
- **Real-time updates** and responsive design

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

**✅ Simple Commands**
```bash
# Start treasury service (kills any process on port 8000 first)
./start.sh

# Start frontend dashboard (in another terminal)
cd apps/treasury-dashboard && npm run dev
```

**Alternative: Manual Command**
```bash
# Manual startup (from project root)
.venv/bin/python -m uvicorn services.treasury_service.enhanced_app:app --port 8000 --reload
```

**Access the backend at:** `http://localhost:8000`  
**Access the frontend at:** `http://localhost:3000`

### 🔐 **Demo Login Credentials**
Use these credentials to login to the frontend:
- **CFO**: `cfo` / `demo123` (Full access)
- **Manager**: `manager` / `demo123` (Management access)  
- **Analyst**: `analyst` / `demo123` (View access)
- **Admin**: `admin` / `demo123` (Admin access)

## Data Generation

The mock data script generates realistic treasury datasets:
- **Accounts:** 50 accounts across 10 entities
- **Transactions:** ~12k transactions over 6 months
- **Payments:** 2k payment records
- **AR/AP:** 15k receivables/payables entries
- **Counterparties:** 700 business partners

**Performance:** Completes in ~5 seconds (optimized from original 900-day dataset)

## Enterprise Architecture

### 🏗️ **Workspace Structure**
```
treasury_agent/                    # Enterprise workspace root
├── services/                      # Domain-bounded microservices
│   └── treasury_service/          # Core treasury management service
│       ├── routers/              # FastAPI HTTP controllers
│       ├── domain/               # Business logic and entities
│       ├── infrastructure/       # External concerns (DB, cache, etc.)
│       └── tools/                # Service-specific utilities
├── apps/                         # Frontend applications
│   └── treasury-dashboard/       # Next.js React dashboard
├── shared/                       # Cross-cutting concerns
│   ├── types/                    # Common type definitions
│   ├── utils/                    # Shared utilities
│   └── config/                   # Configuration management
├── config/                       # Environment-specific configs
│   ├── local/                    # Local development
│   ├── development/              # Dev environment
│   ├── staging/                  # Staging environment
│   └── production/               # Production environment
└── infrastructure/               # Platform and deployment
    ├── environments/             # Environment-specific infrastructure
    ├── monitoring/               # Observability and logging
    └── security/                 # Security configurations
```

### 🎯 **Service Boundaries**
- **`services/treasury_service/`**: Core treasury domain service with LangGraph agents, forecasting, KPIs, and RAG
- **`apps/treasury-dashboard/`**: Modern React dashboard with TypeScript, authentication, and real-time features
- **`shared/`**: Enterprise utilities, types, and cross-cutting concerns

## API Endpoints

- **`/chat`**: Main agent interaction endpoint
- **`/analytics`**: Treasury analytics and KPIs
- **`/payments`**: Payment processing operations
- **`/rag/search`**: Policy document search

### 🔎 Chat Usage Examples

Interactive treasury assistant queries (after starting backend):

```bash
# Latest approvals
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"latest payment approvals"}' | jq .content

# Liquidity risk analysis
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"analyze liquidity risk"}' | jq .content

# Cash position
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"cash position"}' | jq .data

# Working capital KPIs
curl -X POST http://localhost:8000/chat/message \
    -H 'Content-Type: application/json' \
    -d '{"query":"show kpis"}' | jq .data

# Chat history (rolling last 100 messages)
curl http://localhost:8000/chat/history | jq .messages | head -n 20
```

Returned fields:
- `content`: Render-ready assistant reply
- `data`: Structured payload (approvals, cash_position, kpis, etc.)
- `id`, `role`, `timestamp`: For UI rendering and history

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