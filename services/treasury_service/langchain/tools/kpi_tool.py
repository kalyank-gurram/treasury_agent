"""KPI calculation tool for LangChain Treasury Agent."""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ...kpis.working_capital import TreasuryKPICalculator
from ...infrastructure.observability import trace_operation, monitor_performance, get_observability_manager


class KpiInput(BaseModel):
    """Input for KPI calculation tool."""
    entity: str = Field(description="Entity ID to calculate KPIs for", default="")


class KpiTool(BaseTool):
    """Tool to calculate treasury KPIs for Treasury Agent."""
    
    name: str = "calculate_treasury_kpis"
    description: str = "Calculate key treasury performance indicators including working capital, liquidity ratios, and cash flow metrics. Use when users ask about KPIs, performance metrics, or financial ratios."
    args_schema: type[BaseModel] = KpiInput
    
    @trace_operation("kpi_calculation_langchain")
    @monitor_performance("kpi_tool")
    def _run(self, entity: str = "") -> Dict[str, Any]:
        """Execute KPI calculation."""
        observability = get_observability_manager()
        logger = observability.get_logger("langchain.tools.kpi")
        
        logger.info("Calculating KPIs via LangChain tool", entity=entity)
        
        try:
            # Use the same KPI calculation as LangGraph version
            # Create mock data for demonstration
            import pandas as pd
            import numpy as np
            from datetime import datetime, timedelta
            
            # Generate sample ledger data
            rng = np.random.default_rng(42)
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            sample_data = []
            
            for _ in range(100):
                date = rng.choice(dates)
                sample_data.append({
                    'type': rng.choice(['AR', 'AP']),
                    'amount': rng.uniform(1000, 50000),
                    'invoice_date': date,
                    'due_date': date + timedelta(days=rng.integers(15, 60)),
                    'paid_date': date + timedelta(days=rng.integers(10, 90)) if rng.random() > 0.3 else None
                })
            
            ledger = pd.DataFrame(sample_data)
            
            # Generate sample transactions
            tx_data = []
            for _ in range(200):
                tx_data.append({
                    'date': rng.choice(dates),
                    'amount': rng.uniform(-10000, 15000),
                    'type': rng.choice(['payment', 'receipt', 'fee'])
                })
            
            transactions = pd.DataFrame(tx_data)
            
            # Generate sample balances
            balances = pd.DataFrame({
                'currency': ['USD', 'EUR', 'GBP'],
                'balance': [rng.uniform(100000, 1000000) for _ in range(3)]
            })
            
            calculator = TreasuryKPICalculator()
            result = calculator.calculate_all_kpis(ledger, transactions, balances)
            
            logger.info("KPIs calculated successfully", 
                       entity=entity, kpi_count=len(result.get("kpis", {})))
            
            # Record success metric
            observability.record_metric(
                "counter", "kpi_calculations_total", 1,
                {"source": "langchain_tool", "status": "success"}
            )
            
            return {
                "success": True,
                "data": result,
                "entity": entity
            }
            
        except Exception as e:
            logger.error("KPI calculation failed", 
                        entity=entity, error=str(e), error_type=type(e).__name__)
            
            # Record error metric
            observability.record_metric(
                "counter", "kpi_calculations_total", 1,
                {"source": "langchain_tool", "status": "failed"}
            )
            
            return {
                "success": False,
                "error": f"Failed to calculate KPIs: {str(e)}",
                "entity": entity
            }
    
    async def _arun(self, entity: str = "") -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        return self._run(entity)