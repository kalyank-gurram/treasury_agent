# Simple Treasury Learning System 📚# Super Simple 2-Agent Learning System 📚# Simple E-commerce Multi-Agent System 🛒# Treasury Enterprise Workspace



**Follows exact treasury agent patterns but simplified for learning**



## Structure (Same as Treasury Agent) 🏗️**Extremely simplified multi-agent system for learning core concepts**



```

services/treasury_service/

├── agents/## What This Shows 🎯**A simplified learning application demonstrating enterprise multi-agent architecture****Enterprise-grade Domain-Driven Microservices architecture** for treasury & cash management featuring:

│   ├── base_agent.py      # Simple base (like treasury agent)

│   ├── order_agent.py     # 2 operations only

│   └── risk_agent.py      # 2 operations only  

├── graph/- **2 Agents Only**: Order Agent + Payment Agent

│   └── graph.py           # 3 nodes (like treasury agent)

├── routers/- **3 Simple Operations Total**: receive_order, process_payment, complete_order

│   └── orders.py          # FastAPI routes

└── app.py                 # Main service- **Clear Flow**: FastAPI → Agents → Graph → Model → Response## What This App Does## 🏗️ **Enterprise Architecture**



server/- **Same Structure** as treasury agent for easy understanding

└── app.py                 # FastAPI server (like treasury agent)

```- **Microservices:** Domain-bounded services with clear boundaries  



## What You'll Learn 🎯## The Flow (SUPER SIMPLE) 🔄



✅ **Agent Communication** - 2 agents talking to each otherThis is a **clean, educational implementation** of a multi-agent system that processes e-commerce orders. It shows:- **Monorepo:** Organized workspace with `services/`, `apps/`, `shared/`, `config/`

✅ **Graph Workflows** - 3 nodes processing orders  

✅ **RAG System** - Simple document search```

✅ **Memory Persistence** - Chat history saving

✅ **FastAPI Integration** - API → Agents → Graphs → Model1. POST /order → Order Agent- **Environment Separation:** Local, development, staging, production configs



## Quick Start 🚀2. Order Agent → Graph Node 1 (receive_order)



```bash3. Graph calls Payment Agent - **3 Agents working together**- **Event-Driven:** Async communication between service boundaries

# Run demo

python demo.py4. Payment Agent → Graph Node 2 (process_payment)



# Start server5. Graph Node 3 (complete_order) → Model Call- **4-node LangGraph workflow** 

python server/app.py

6. Response back through the chain

# Test order

curl -X POST localhost:8000/orders \```- **FastAPI integration**## 🚀 **Treasury Capabilities**  

  -d '{"item":"laptop", "amount":1000}'

```

## Structure 🏗️- **Agent-to-agent communication**- **LangGraph** intelligent routing + domain subgraphs (9+ use cases)



```- **Enterprise patterns made simple**- **Large datasets** (optimized ~30k transactions, 5-second generation)

services/simple_service/

├── agents/- **Forecasting** (ARIMA + GradientBoost models)

│   ├── base_agent.py      # Minimal base (50 lines)

│   ├── order_agent.py     # 2 operations only## The Flow 🔄- **Anomaly detection** (statistical outlier detection)

│   └── payment_agent.py   # 2 operations only

├── graph/- **Working-capital KPIs** (DSO/DPO analytics)

│   └── simple_graph.py    # 3 nodes only

└── routers/```- **Liquidity modeling** with scenario analysis

    └── orders.py          # 1 endpoint

server/1. 📦 Order comes in via API- **Counterparty exposure** management

└── app.py                 # FastAPI server

```2. 🤖 Order Manager Agent receives it- **RAG-powered** policy search



## Quick Start 🚀3. 📊 Inventory Checker Agent validates stock- **Narrative reporting** with automated insights



```bash4. 💳 Payment Processor Agent handles payment

# 1. Run the demo

python demo.py5. ✅ Order fulfilled automatically## 🎯 **Modern Frontend**



# 2. Start server  ```- **Next.js Dashboard** (React, TypeScript, Tailwind CSS)

python server/app.py

- **Role-based authentication** and authorization

# 3. Test flow

curl -X POST "http://localhost:8000/order" \## Architecture 🏗️- **Real-time updates** and responsive design

  -H "Content-Type: application/json" \

  -d '{"item": "laptop", "amount": 1000}'

```

```## Quickstart

## You'll Understand Exactly 📖

├── agents/           # 3 specialized agents

✅ **Where agents are created** (services/simple_service/agents/)

✅ **Where graphs are defined** (services/simple_service/graph/)  │   ├── base_agent.py        # Simple base class### Prerequisites

✅ **How agents call graphs** (agent → graph.invoke())

✅ **Where model calls happen** (inside graph nodes)│   ├── order_manager.py     # Receives & coordinates orders```bash

✅ **How FastAPI triggers everything** (server → agents → graphs)

│   ├── inventory_checker.py # Validates product availability  poetry install

**No complexity, just pure learning!** 🎓
│   └── payment_processor.py # Handles paymentscp .env.example .env

├── graph/            # LangGraph workflow# Edit .env and add your OPENAI_API_KEY

│   ├── nodes.py             # 4 workflow nodes

│   └── workflow.py          # Graph orchestration# Frontend dependencies

├── api/              # FastAPI endpointscd apps/treasury-dashboard && npm install

│   ├── main.py              # API server```

│   └── routes.py            # Order endpoints

└── demo.py           # Complete demo script### One-Command Setup (Recommended)

``````bash

poetry run python scripts/setup.py

## Quick Start 🚀```



```bash### Manual Setup (Alternative)

# 1. Install dependencies```bash

poetry install# Run these setup scripts only ONCE (first time or when files are missing)

poetry run python scripts/generate_mock_data.py

# 2. Run the demo (shows everything working)poetry run python scripts/build_vectorstore.py

python demo.py```



# 3. Run the API server### Start Services

uvicorn api.main:app --reload

**✅ Simple Commands**

# 4. Test an order```bash

curl -X POST "http://localhost:8000/orders" \# Start treasury service (kills any process on port 8000 first)

  -H "Content-Type: application/json" \./start.sh

  -d '{"product_id": "laptop-001", "quantity": 1, "customer_id": "cust-123"}'

```# Start frontend dashboard (in another terminal)

cd apps/treasury-dashboard && npm run dev

## What You'll Learn 📚```



### ✅ **Agent Communication****Alternative: Manual Command**

- How agents send messages to each other```bash

- REQUEST/RESPONSE patterns# Manual startup (from project root)

- Broadcasting updates.venv/bin/python -m uvicorn services.treasury_service.enhanced_app:app --port 8000 --reload

```

### ✅ **LangGraph Workflows** 

- How agents connect to graph nodes**Access the backend at:** `http://localhost:8000`  

- Sequential workflow execution**Access the frontend at:** `http://localhost:3000`

- State management between nodes

### 🔐 **Demo Login Credentials**

### ✅ **FastAPI Integration**Use these credentials to login to the frontend:

- How web requests trigger agent workflows- **CFO**: `cfo` / `demo123` (Full access)

- API → Agents → Graph → Response flow- **Manager**: `manager` / `demo123` (Management access)  

- Enterprise API patterns- **Analyst**: `analyst` / `demo123` (View access)

- **Admin**: `admin` / `demo123` (Admin access)

### ✅ **Enterprise Architecture**

- Clean separation of concerns## Data Generation

- Domain-driven design principles

- Scalable agent patternsThe mock data script generates realistic treasury datasets:

- **Accounts:** 50 accounts across 10 entities

## Example Output 📊- **Transactions:** ~12k transactions over 6 months

- **Payments:** 2k payment records

```- **AR/AP:** 15k receivables/payables entries

🛒 NEW ORDER: laptop-001 x1 for cust-123- **Counterparties:** 700 business partners

📦 Order Manager: Processing order ord-001

🔍 Inventory Checker: Checking stock for laptop-001**Performance:** Completes in ~5 seconds (optimized from original 900-day dataset)

✅ Inventory: 5 units available

💳 Payment Processor: Processing $1299.99 payment## Enterprise Architecture

✅ Payment successful: txn-abc123

🎉 Order ord-001 fulfilled successfully!### 🏗️ **Workspace Structure**

``````

treasury_agent/                    # Enterprise workspace root

## Why This Approach? 🤔├── services/                      # Domain-bounded microservices

│   └── treasury_service/          # Core treasury management service

Unlike complex production systems, this demo:│       ├── routers/              # FastAPI HTTP controllers

- **Focuses on core concepts** without overwhelming complexity│       ├── domain/               # Business logic and entities

- **Shows clear agent boundaries** and responsibilities  │       ├── infrastructure/       # External concerns (DB, cache, etc.)

- **Demonstrates real workflows** you can see in action│       └── tools/                # Service-specific utilities

- **Uses enterprise patterns** but keeps them simple├── apps/                         # Frontend applications

- **Provides instant feedback** so you understand the flow│   └── treasury-dashboard/       # Next.js React dashboard

├── shared/                       # Cross-cutting concerns

Perfect for learning how multi-agent systems work in practice! 🎯│   ├── types/                    # Common type definitions
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