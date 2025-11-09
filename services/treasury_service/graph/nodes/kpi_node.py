"""Enhanced KPI calculation node for Treasury Agent."""

from ...kpis.working_capital import TreasuryKPICalculator
from ..types import AgentState
from .utils import api
from ...infrastructure.observability import trace_operation, monitor_performance


@trace_operation("kpi_calculation")
@monitor_performance("kpi_node")
def node_kpis(state: AgentState):
    """Calculate comprehensive treasury KPIs including working capital, cash flow, and risk metrics."""
    from ...infrastructure.observability import get_observability_manager
    
    observability = get_observability_manager()
    logger = observability.get_logger("graph.kpis")
    
    entity = state.get("entity")
    logger.info("Starting KPI calculations", entity=entity)
    
    try:
        # Get required data
        ledger = api.get_ledger(entity)
        
        # Access transactions from the api instance directly
        from ...tools.mock_bank_api import MockBankAPI
        bank_api = MockBankAPI()
        transactions = bank_api.transactions.copy()
        
        # Filter transactions by entity if needed
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
            
        balances = api.get_account_balances(entity)
        
        # Initialize KPI calculator
        calculator = TreasuryKPICalculator()
        
        # Calculate all KPIs
        all_kpis = calculator.calculate_all_kpis(ledger, transactions, balances)
        
        # Format result with metadata
        state["result"] = {
            "kpis": all_kpis,
            "calculation_timestamp": calculator.today.isoformat(),
            "entity": entity,
            "data_summary": {
                "ledger_entries": len(ledger),
                "transactions": len(transactions),
                "accounts": len(balances)
            }
        }
        
        logger.info("KPI calculations completed successfully", 
                   entity=entity,
                   kpi_categories=len(all_kpis))
        
        # Record success metric
        observability.record_metric(
            "counter", "kpi_calculations_total", 1,
            {"entity": entity or "all", "status": "success"}
        )
        
        return state
        
    except Exception as e:
        logger.error("KPI calculation failed", 
                    entity=entity, 
                    error=str(e), 
                    error_type=type(e).__name__)
        
        # Record error metric
        observability.record_metric(
            "counter", "kpi_calculations_total", 1,
            {"entity": entity or "all", "status": "failed"}
        )
        
        # Fallback to basic KPIs
        try:
            ledger = api.get_ledger(entity)
            calculator = TreasuryKPICalculator()
            dso, dpo = calculator.calculate_dso_dpo(ledger)
            
            state["result"] = {
                "kpis": {
                    "basic": {"DSO": dso, "DPO": dpo}
                },
                "error": f"Full KPI calculation failed, showing basic metrics: {str(e)}",
                "calculation_timestamp": calculator.today.isoformat()
            }
        except Exception as fallback_error:
            state["result"] = {
                "error": f"KPI calculation failed: {str(e)}. Fallback failed: {str(fallback_error)}"
            }
        
        return state