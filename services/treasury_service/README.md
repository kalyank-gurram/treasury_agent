Simple E-commerce Learning System
================================

SIMPLIFIED Treasury Agent Architecture - Easy to Understand!

📁 Folder Structure (Same as Treasury Agent):
```
services/treasury_service/
├── agents/
│   ├── base_agent.py      # Base agent class
│   ├── order_agent.py     # Handles orders
│   └── payment_agent.py   # Handles payments

└── demo.py               # Demo script
```

🤖 2 AGENTS ONLY:

1. OrderAgent - 2 operations:
   - receive_order: Gets order from API
   - start_workflow: Initiates processing

2. PaymentAgent - 2 operations:  
   - validate_payment: Checks payment
   - search_knowledge: Simple RAG search

💬 MESSAGING (Like Treasury Agent):
- Agents send messages to each other
- 3 message types: REQUEST, RESPONSE, BROADCAST  
- Direct peer registration (like Treasury Agent)

🔍 RAG SYSTEM:
- Simple string matching in knowledge base
- No vector database needed
- Easy to understand

📊 MEMORY:
- JSON file storage
- Chat sessions persist
- Simple and clear

🔄 WORKFLOW:
- Order → Payment validation
- Agent-to-agent messaging
- Broadcasting system updates

🚀 TO RUN:
```
cd services/treasury_service
python3 demo.py
```

✅ WORKING FEATURES:
- Agent creation and registration
- Message passing between agents
- RAG knowledge search
- Broadcasting
- Clean error-free code

This shows exactly how Treasury Agent works but MUCH simpler!
No complex graphs, no heavy dependencies, just pure agent messaging.