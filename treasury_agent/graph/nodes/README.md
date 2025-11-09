# Treasury Agent Graph Nodes

This directory contains the modular node implementations for the Treasury Agent LangGraph workflow. Each node handles a specific Treasury management capability.

## Architecture

```
treasury_agent/graph/
├── graph.py           # Main graph builder and routing logic
├── types.py           # Shared AgentState type definition
└── nodes/
    ├── __init__.py    # Node exports
    ├── utils.py       # Shared utilities (API instance)
    ├── intent_node.py # Intent classification
    ├── balance_node.py # Account balance retrieval
    ├── forecast_node.py # Cash flow forecasting
    ├── payment_node.py # Payment approval
    ├── anomaly_node.py # Anomaly detection
    ├── kpi_node.py    # Working capital KPIs
    ├── whatif_node.py # Scenario analysis
    ├── exposure_node.py # Counterparty exposure
    ├── rag_node.py    # Policy document search
    └── narrative_node.py # Executive reporting
```

## Node Responsibilities

### Core Nodes
- **`intent_node`**: Classifies user queries into one of 9 Treasury capabilities
- **`balance_node`**: Retrieves account balances by entity
- **`forecast_node`**: Generates 30-day cash flow forecasts using ARIMA + GBR ensemble

### Risk & Analytics Nodes
- **`anomaly_node`**: Detects unusual outflow patterns in cash flow data
- **`kpi_node`**: Calculates DSO (Days Sales Outstanding) and DPO (Days Payable Outstanding)
- **`exposure_node`**: Analyzes counterparty risk concentrations

### Operations Nodes
- **`payment_node`**: Approves payments by ID or lists pending payments
- **`whatif_node`**: Runs scenarios (e.g., shifting AP payment dates)

### Intelligence Nodes
- **`rag_node`**: Searches treasury policies using vector similarity and LLM synthesis
- **`narrative_node`**: Generates executive CFO briefings combining multiple data sources

## Usage

The main graph is built in `graph.py`:

```python
from treasury_agent.graph.graph import build_graph

# Build and use the graph
agent = build_graph()
result = agent.invoke({"question": "Show me account balances for ACME Corp"})
```

## Adding New Nodes

1. Create a new file in `nodes/` following the naming pattern: `{capability}_node.py`
2. Import `AgentState` from `treasury_agent.graph.types`
3. Use the shared API instance from `treasury_agent.graph.nodes.utils`
4. Implement your node function with signature: `def node_name(state: AgentState) -> AgentState`
5. Add the import to `nodes/__init__.py`
6. Register the node in `graph.py` (`build_graph()` function)
7. Update the routing logic if needed

## Shared Resources

- **`utils.api`**: Single MockBankAPI instance shared across nodes to avoid connection overhead
- **`types.AgentState`**: TypedDict defining the workflow state schema
- **Route mapping**: Intent classification maps to specific node names in the graph

This modular structure enables:
- Easy testing of individual capabilities
- Clean separation of concerns
- Reusable components across different workflows
- Clear dependency management