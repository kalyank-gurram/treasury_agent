# Treasury Agent

Architected LangGraph-based agent for treasury & cash management with:
- Modular **routers/services/schemas** (FastAPI)
- **LangGraph** intent router + subgraphs (9 use cases)
- Large **mock datasets** (optimized ~30k transactions)
- Forecasting (ARIMA + GradientBoost)
- Anomaly detection (outflows vs 90d)
- Working-capital KPIs (DSO/DPO)
- Liquidity what-ifs
- Counterparty exposure
- **RAG** policies
- **Narrative** reporting
- **Gradio UI** (decoupled; calls REST)

## Quickstart

### Prerequisites
```bash
poetry install
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
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
```bash
# Start backend and UI
poetry run uvicorn server.app:app --reload --port 8000
poetry run python ui/gradio_app.py
```

**Access the app at:** `http://127.0.0.1:7861`

## Data Generation

The mock data script generates realistic treasury datasets:
- **Accounts:** 50 accounts across 10 entities
- **Transactions:** ~12k transactions over 6 months
- **Payments:** 2k payment records
- **AR/AP:** 15k receivables/payables entries
- **Counterparties:** 700 business partners

**Performance:** Completes in ~5 seconds (optimized from original 900-day dataset)

## Architecture

- **`server/routers/*`**: FastAPI HTTP controllers
- **`server/services/*`**: Domain logic using treasury_agent modules  
- **`treasury_agent/*`**: Core agent libraries (LangGraph, forecasting, RAG, KPIs)
- **`ui/`**: Gradio frontend (decoupled, can swap with Next.js/React)
- **`scripts/`**: Data generation and vector store build utilities

## API Endpoints

- **`/chat`**: Main agent interaction endpoint
- **`/analytics`**: Treasury analytics and KPIs
- **`/payments`**: Payment processing operations
- **`/rag/search`**: Policy document search

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
poetry run uvicorn server.app:app --reload --port 8000
poetry run python ui/gradio_app.py
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

**Option 1:** Single container with both backend and UI
**Option 2:** Separate backend deployment with UI pointing to remote server

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