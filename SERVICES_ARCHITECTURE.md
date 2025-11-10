# Treasury Agent Services Architecture Documentation

## Overview

The `services/` folder contains the core Treasury Agent microservice implementation using FastAPI and clean architecture principles. It's organized into distinct layers with clear separation between external client APIs, internal agent communication, and domain logic.

## 📁 Folder Structure

```
services/
├── __init__.py
└── treasury_service/                    # Main microservice
    ├── app.py                          # 🌐 FastAPI application entry point
    ├── enhanced_app.py                 # 🔧 Enhanced app with additional features
    ├── simple_app.py                   # 🎯 Simplified app for testing
    ├── config.py                       # ⚙️ Configuration settings
    ├── 
    ├── routers/                        # 🌐 API Route Handlers (External APIs)
    │   ├── auth.py                     # 👤 Authentication endpoints
    │   ├── analytics.py                # 📊 Analytics & reporting endpoints  
    │   ├── chat.py                     # 💬 Chat interface endpoints
    │   ├── payments.py                 # 💰 Payment management endpoints
    │   ├── rag.py                      # 📚 Document search endpoints
    │   └── persistent_chat.py          # 💾 Persistent chat endpoints
    │
    ├── domain/                         # 🏛️ Domain Layer (Business Logic)
    │   ├── entities/                   # Core business entities
    │   ├── services/                   # Domain services
    │   ├── repositories/               # Repository interfaces  
    │   ├── events/                     # Domain events
    │   ├── cash_management/           # Cash management logic
    │   └── value_objects/             # Value objects
    │
    ├── infrastructure/                 # 🔧 Infrastructure Layer
    │   ├── di/                        # Dependency injection
    │   ├── security/                  # Authentication & authorization
    │   ├── observability/            # Logging, metrics, tracing
    │   ├── events/                   # Event bus implementation
    │   ├── persistence/              # Database persistence
    │   └── repositories/             # Repository implementations
    │
    ├── graph/                         # 🤖 LangGraph Agent Implementation
    │   ├── graph.py                   # Agent workflow definition
    │   ├── memory_graph.py           # Memory-enhanced agent
    │   ├── nodes/                    # Individual processing nodes
    │   └── types.py                  # Graph type definitions
    │
    ├── langchain/                     # 🦜 LangChain Agent Implementation  
    │   ├── treasury_agent.py         # LangChain agent
    │   ├── chat_service.py          # LangChain chat service
    │   ├── memory.py                # Memory management
    │   └── tools/                   # LangChain tools
    │
    ├── services/                      # 🔄 Application Services
    │   ├── chat.py                   # Chat orchestration
    │   └── persistent_chat.py       # Memory-aware chat
    │
    ├── agents/                       # 🤖 Specialized AI Agents
    │   ├── treasury_coordinator.py   # Main coordinator
    │   ├── compliance_officer.py    # Compliance checks
    │   ├── investment_advisor.py    # Investment recommendations
    │   └── collections_specialist.py # Collections management
    │
    ├── forecasting/                  # 📈 Forecasting Models
    │   ├── arima_forecaster.py      # ARIMA time series
    │   └── gbr_forecaster.py        # Gradient boosting
    │
    ├── detectors/                    # 🔍 Anomaly Detection
    │   └── anomaly.py               # Anomaly detection logic
    │
    ├── kpis/                         # 📊 KPI Calculations
    │   └── working_capital.py       # Working capital metrics
    │
    ├── reports/                      # 📋 Report Generation
    │   └── narrative.py             # Narrative report generator
    │
    ├── tools/                        # 🛠️ Utility Tools
    │   └── mock_bank_api.py         # Mock banking API for testing
    │
    ├── schemas/                      # 📝 API Schemas (Pydantic Models)
    │   ├── auth.py                  # Authentication schemas
    │   └── chat.py                  # Chat message schemas
    │
    ├── models/                       # 🧠 AI/ML Models
    │   └── llm_router.py            # LLM routing logic
    │
    ├── plugins/                      # 🔌 Plugin System
    │   ├── base.py                  # Base plugin interface
    │   ├── enhanced_arima_forecaster.py
    │   └── ml_anomaly_detector.py
    │
    └── tests/                        # 🧪 Testing & Demos
        ├── demo_*.py                # Various demonstration scripts
        └── test_*.py               # Test files
```

---

## 🌐 External APIs (Client-Facing)

These APIs are exposed to frontend clients (web dashboard, mobile apps, etc.) and external systems.

### 📍 **Authentication APIs** (`routers/auth.py`)
**Endpoint Prefix:** `/auth`

| Endpoint | Method | Purpose | Client Usage |
|----------|---------|---------|-------------|
| `/auth/login` | POST | User authentication | Login form submission |
| `/auth/logout` | POST | User logout | Logout functionality |  
| `/auth/me` | GET | Get current user info | Profile display |
| `/auth/change-password` | PUT | Password change | Settings page |
| `/auth/users` | GET | List users (admin) | User management |

**Example Client Call:**
```typescript
// From frontend (api.ts line 89)
async login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await this.client.post('/auth/login', credentials);
  this.setToken(response.data.access_token);
  return response.data;
}
```

### 📊 **Analytics APIs** (`routers/analytics.py`)
**Endpoint Prefix:** `/analytics`

| Endpoint | Method | Purpose | Client Usage |
|----------|---------|---------|-------------|
| `/analytics/summary` | GET | Dashboard summary | Main dashboard |
| `/analytics/forecast` | GET | Cash flow forecasts | Forecast charts |
| `/analytics/balances` | GET | Account balances | Balance displays |
| `/analytics/anomalies` | GET | Anomaly detection | Risk alerts |

**Example Client Call:**
```typescript
async getAnalytics(): Promise<AnalyticsData> {
  const response = await this.client.get('/analytics/summary');
  return response.data;
}
```

### 💬 **Chat APIs** (`routers/chat.py`)
**Endpoint Prefix:** `/chat`

| Endpoint | Method | Purpose | Client Usage |
|----------|---------|---------|-------------|
| `/chat/message` | POST | Send chat message | Chat interface |
| `/chat/history` | GET | Get chat history | Chat history display |
| `/chat` | POST | Process chat request | Alternative chat endpoint |

**Example Client Call:**
```typescript
async sendMessage(message: string): Promise<ChatMessage> {
  const response = await this.client.post('/chat/message', {
    message,
    conversation_id: 'default'
  });
  return response.data;
}
```

### 💰 **Payment APIs** (`routers/payments.py`)
**Endpoint Prefix:** `/payments`

| Endpoint | Method | Purpose | Client Usage |
|----------|---------|---------|-------------|
| `/payments` | GET | List payments | Payment dashboard |
| `/payments/{id}/approve` | POST | Approve payment | Approval workflow |
| `/payments/{id}/reject` | POST | Reject payment | Rejection workflow |

### 📚 **RAG APIs** (`routers/rag.py`)  
**Endpoint Prefix:** `/rag`

| Endpoint | Method | Purpose | Client Usage |
|----------|---------|---------|-------------|
| `/rag/search` | POST | Document search | Search interface |
| `/rag/ask` | POST | Question answering | Q&A interface |

---

## 🔗 Internal APIs (Agent Communication)

These APIs facilitate communication between the FastAPI backend and AI agents, and between different internal services.

### 🤖 **Agent-to-Service Communication**

#### **Graph Processing** (`graph/`)
- **Purpose:** Internal LangGraph workflow execution
- **Communication:** Synchronous function calls
- **Usage:** Agent processes chat requests through graph nodes

```python
# Internal agent communication
from .graph.graph import create_graph

async def process_with_agent(question: str, entity: str):
    graph = create_graph()
    result = await graph.ainvoke({
        "question": question, 
        "entity": entity
    })
    return result
```

#### **LangChain Processing** (`langchain/`)
- **Purpose:** Alternative LangChain-based agent execution
- **Communication:** Tool-based architecture
- **Usage:** Simplified agent with tool selection

```python
# Internal LangChain communication
from .langchain.treasury_agent import TreasuryLangChainAgent

agent = TreasuryLangChainAgent(container)
result = agent.invoke(question, entity=entity)
```

### 🔄 **Service-to-Service Communication**

#### **Domain Services** (`domain/services/`)
- **Purpose:** Business logic execution
- **Communication:** Direct method calls via DI
- **Usage:** Complex business operations

```python
# Internal service communication
treasury_service = container.get(TreasuryDomainService)
result = treasury_service.calculate_liquidity_ratios(entity_id)
```

#### **Event Bus** (`infrastructure/events/`)
- **Purpose:** Asynchronous event-driven communication
- **Communication:** Publish/subscribe pattern
- **Usage:** Decoupled component interaction

```python
# Internal event communication
await event_bus.publish(PaymentApprovedEvent(payment_id))
```

---

## 🏗️ Architecture Layers

### 1. **Presentation Layer** (External)
- **Location:** `routers/`
- **Responsibility:** HTTP request handling, response formatting
- **Clients:** Frontend applications, external APIs

### 2. **Application Layer** (Internal)  
- **Location:** `services/`
- **Responsibility:** Use case orchestration, workflow coordination
- **Clients:** Router handlers, background tasks

### 3. **Domain Layer** (Core Business Logic)
- **Location:** `domain/`
- **Responsibility:** Business rules, entities, domain services
- **Clients:** Application services, domain events

### 4. **Infrastructure Layer** (Internal)
- **Location:** `infrastructure/`
- **Responsibility:** Technical capabilities, external integrations
- **Clients:** All other layers via dependency injection

### 5. **Agent Layer** (AI Processing)
- **Location:** `graph/`, `langchain/`, `agents/`  
- **Responsibility:** AI-powered decision making and processing
- **Clients:** Chat services, analytical workflows

---

## 🔐 Security & Authentication

### **Token-Based Authentication**
- **JWT tokens** issued by `/auth/login`
- **Bearer token** required for protected endpoints
- **Role-based access control** via user permissions

### **Authorization Flow**
1. Client logs in via `/auth/login`
2. Server returns JWT access token  
3. Client includes token in subsequent requests
4. Server validates token and permissions
5. Request processed if authorized

---

## 📊 Data Flow Examples

### **Chat Request Flow**
```
Frontend → POST /chat/message → ChatRouter → ChatService → 
Agent (LangGraph/LangChain) → Domain Services → Response
```

### **Analytics Request Flow**  
```
Frontend → GET /analytics/summary → AnalyticsRouter → 
TreasuryDomainService → Repository → Database → Response
```

### **Payment Approval Flow**
```
Frontend → POST /payments/{id}/approve → PaymentRouter →
PaymentApprovalService → Event Bus → Notification Services
```

---

## 🔧 Key Configuration Files

- **`app.py`:** Main FastAPI application setup
- **`config.py`:** Environment configuration
- **`infrastructure/di/config.py`:** Dependency injection setup
- **`infrastructure/security/`:** Authentication configuration

---

## 🚀 Getting Started

1. **External API Usage:** Use the routers endpoints for client applications
2. **Internal Development:** Extend domain services and agents for new features  
3. **Testing:** Use the demo scripts in `tests/` for examples
4. **Monitoring:** Built-in observability via `infrastructure/observability/`

This architecture provides clear separation between client-facing APIs and internal service communication, enabling scalable and maintainable treasury management operations.