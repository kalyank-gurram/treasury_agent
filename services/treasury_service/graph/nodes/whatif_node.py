"""Enhanced what-if scenario analysis node for Treasury Agent."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..types import AgentState
from .utils import api
from ...infrastructure.observability import trace_operation, monitor_performance


class TreasuryScenarioEngine:
    """Comprehensive scenario planning engine for treasury operations."""
    
    def __init__(self):
        self.scenarios = {
            "ap_delay": self._scenario_ap_delay,
            "fx_stress": self._scenario_fx_stress, 
            "collection_delay": self._scenario_collection_delay,
            "payment_acceleration": self._scenario_payment_acceleration,
            "seasonal_impact": self._scenario_seasonal_impact,
            "liquidity_stress": self._scenario_liquidity_stress,
            "monte_carlo": self._scenario_monte_carlo
        }
        
    def run_scenario(self, scenario_name: str, parameters: Dict, entity: str) -> Dict:
        """Run a specific scenario with given parameters."""
        if scenario_name not in self.scenarios:
            available = ", ".join(self.scenarios.keys())
            return {"error": f"Unknown scenario '{scenario_name}'. Available: {available}"}
            
        return self.scenarios[scenario_name](parameters, entity)
        
    def _get_base_data(self, entity: str) -> Dict:
        """Get baseline data for scenario analysis."""
        from ...tools.mock_bank_api import MockBankAPI
        bank_api = MockBankAPI()
        
        transactions = bank_api.transactions.copy()
        if entity and entity != "ALL":
            transactions = transactions[transactions["entity"] == entity]
            
        balances = api.get_account_balances(entity)
        ledger = api.get_ledger(entity)
        
        return {
            "transactions": transactions,
            "balances": balances, 
            "ledger": ledger
        }
        
    def _scenario_ap_delay(self, parameters: Dict, entity: str) -> Dict:
        """Scenario: What if AP payments are delayed?"""
        delay_days = parameters.get("delay_days", 7)
        impact_percentage = parameters.get("impact_percentage", 100)  # % of AP affected
        
        data = self._get_base_data(entity)
        tx = data["transactions"].copy()
        tx["date"] = pd.to_datetime(tx["date"])
        
        # Identify AP transactions
        ap_mask = tx["category"] == "AP"
        ap_transactions = tx[ap_mask].copy()
        
        # Apply delay to percentage of AP transactions
        if impact_percentage < 100:
            sample_size = int(len(ap_transactions) * (impact_percentage / 100))
            rng = np.random.default_rng(42)  # Use new generator with seed for reproducibility
            delay_indices = rng.choice(ap_transactions.index, size=sample_size, replace=False)
            tx.loc[delay_indices, "date"] = tx.loc[delay_indices, "date"] + pd.Timedelta(days=delay_days)
        else:
            tx.loc[ap_mask, "date"] = tx.loc[ap_mask, "date"] + pd.Timedelta(days=delay_days)
        
        # Calculate impact
        original_daily = data["transactions"].groupby(pd.to_datetime(data["transactions"]["date"]).dt.date)["amount"].sum()
        new_daily = tx.groupby(tx["date"].dt.date)["amount"].sum()
        
        # Calculate cumulative cash position
        baseline_cumulative = original_daily.cumsum()
        scenario_cumulative = new_daily.cumsum()
        
        # Find minimum cash position (liquidity risk)
        min_baseline = baseline_cumulative.min()
        min_scenario = scenario_cumulative.min()
        liquidity_impact = min_scenario - min_baseline
        
        return {
            "scenario": "AP Payment Delay",
            "parameters": {"delay_days": delay_days, "impact_percentage": impact_percentage},
            "results": {
                "liquidity_impact": float(liquidity_impact),
                "min_cash_baseline": float(min_baseline),
                "min_cash_scenario": float(min_scenario), 
                "affected_transactions": int(ap_transactions.shape[0] * (impact_percentage / 100)),
                "daily_flows": new_daily.tail(30).to_dict(),
                "cumulative_position": scenario_cumulative.tail(30).to_dict()
            },
            "risk_assessment": self._assess_liquidity_risk(liquidity_impact, min_scenario)
        }
        
    def _scenario_fx_stress(self, parameters: Dict, entity: str) -> Dict:
        """Scenario: FX rate stress testing."""
        currency_shocks = parameters.get("currency_shocks", {"EUR": -0.1, "GBP": -0.15})  # 10% EUR decline, 15% GBP decline
        
        data = self._get_base_data(entity)
        balances = data["balances"].copy()
        
        # Apply FX shocks
        fx_impact = {}
        total_impact = 0
        
        for currency, shock in currency_shocks.items():
            currency_balances = balances[balances["currency"] == currency]
            if len(currency_balances) > 0:
                current_value = currency_balances["balance"].sum()
                shocked_value = current_value * (1 + shock)
                impact = shocked_value - current_value
                
                fx_impact[currency] = {
                    "current_balance": float(current_value),
                    "shocked_balance": float(shocked_value),
                    "impact": float(impact),
                    "shock_percentage": shock * 100
                }
                total_impact += impact
        
        # Calculate USD-equivalent impact (simplified)
        usd_balances = balances[balances["currency"] == "USD"]["balance"].sum()
        total_portfolio_value = usd_balances + sum([fx_impact[curr]["current_balance"] for curr in fx_impact])
        impact_percentage = (total_impact / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        return {
            "scenario": "FX Stress Test",
            "parameters": {"currency_shocks": currency_shocks},
            "results": {
                "fx_impact_by_currency": fx_impact,
                "total_fx_impact": float(total_impact),
                "portfolio_impact_percentage": float(impact_percentage),
                "total_portfolio_value": float(total_portfolio_value)
            },
            "risk_assessment": self._assess_fx_risk(impact_percentage)
        }
        
    def _scenario_collection_delay(self, parameters: Dict, entity: str) -> Dict:
        """Scenario: What if AR collections are delayed?"""
        delay_days = parameters.get("delay_days", 14)
        impact_percentage = parameters.get("impact_percentage", 50)  # % of AR affected
        
        data = self._get_base_data(entity)
        ledger = data["ledger"].copy()
        
        # Focus on unpaid AR
        ar_unpaid = ledger[(ledger["type"] == "AR") & (ledger["paid_date"] == "")].copy()
        
        if len(ar_unpaid) == 0:
            return {
                "scenario": "AR Collection Delay",
                "results": {"message": "No unpaid AR found"},
                "risk_assessment": {"level": "low", "message": "No collection risk"}
            }
        
        # Calculate expected collection dates
        ar_unpaid["due_date"] = pd.to_datetime(ar_unpaid["due_date"])
        ar_unpaid["expected_collection"] = ar_unpaid["due_date"] + pd.Timedelta(days=delay_days)
        
        # Calculate cash flow impact
        affected_amount = ar_unpaid["amount"].sum() * (impact_percentage / 100)
        total_ar = ar_unpaid["amount"].sum()
        
        # Aging impact
        ar_unpaid["new_aging"] = (pd.Timestamp.now() - ar_unpaid["expected_collection"]).dt.days
        aging_buckets = {
            "30+": ar_unpaid[ar_unpaid["new_aging"] > 30]["amount"].sum(),
            "60+": ar_unpaid[ar_unpaid["new_aging"] > 60]["amount"].sum(),
            "90+": ar_unpaid[ar_unpaid["new_aging"] > 90]["amount"].sum()
        }
        
        return {
            "scenario": "AR Collection Delay", 
            "parameters": {"delay_days": delay_days, "impact_percentage": impact_percentage},
            "results": {
                "affected_ar_amount": float(affected_amount),
                "total_ar_outstanding": float(total_ar),
                "new_aging_buckets": {k: float(v) for k, v in aging_buckets.items()},
                "cash_flow_delay": float(affected_amount)
            },
            "risk_assessment": self._assess_collection_risk(affected_amount, total_ar)
        }
        
    def _scenario_monte_carlo(self, parameters: Dict, entity: str) -> Dict:
        """Monte Carlo simulation for cash flow projections."""
        days_ahead = parameters.get("days_ahead", 30)
        simulations = parameters.get("simulations", 1000)
        volatility_factor = parameters.get("volatility_factor", 1.0)
        
        data = self._get_base_data(entity)
        transactions = data["transactions"].copy()
        transactions["date"] = pd.to_datetime(transactions["date"])
        
        # Calculate historical statistics
        daily_flows = transactions.groupby(transactions["date"].dt.date)["amount"].sum()
        mean_daily_flow = daily_flows.mean()
        std_daily_flow = daily_flows.std() * volatility_factor
        
        # Run Monte Carlo simulation
        simulation_results = []
        rng = np.random.default_rng(42)  # Use new generator
        for _ in range(simulations):
            # Generate random daily flows
            random_flows = rng.normal(mean_daily_flow, std_daily_flow, days_ahead)
            
            # Calculate cumulative position
            current_balance = data["balances"]["balance"].sum()
            cumulative_position = current_balance + np.cumsum(random_flows)
            
            # Track key metrics
            min_position = cumulative_position.min()
            final_position = cumulative_position[-1]
            days_negative = (cumulative_position < 0).sum()
            
            simulation_results.append({
                "min_position": min_position,
                "final_position": final_position,
                "days_negative": days_negative
            })
        
        # Calculate statistics
        results_df = pd.DataFrame(simulation_results)
        
        return {
            "scenario": "Monte Carlo Simulation",
            "parameters": {"days_ahead": days_ahead, "simulations": simulations, "volatility_factor": volatility_factor},
            "results": {
                "percentiles": {
                    "5th": float(results_df["final_position"].quantile(0.05)),
                    "25th": float(results_df["final_position"].quantile(0.25)), 
                    "50th": float(results_df["final_position"].quantile(0.50)),
                    "75th": float(results_df["final_position"].quantile(0.75)),
                    "95th": float(results_df["final_position"].quantile(0.95))
                },
                "risk_metrics": {
                    "probability_negative": float((results_df["min_position"] < 0).mean() * 100),
                    "expected_min_position": float(results_df["min_position"].mean()),
                    "worst_case_5pct": float(results_df["min_position"].quantile(0.05))
                },
                "summary_stats": {
                    "mean_final_position": float(results_df["final_position"].mean()),
                    "std_final_position": float(results_df["final_position"].std()),
                    "current_balance": float(data["balances"]["balance"].sum())
                }
            }
        }
        
    def _scenario_payment_acceleration(self, parameters: Dict, entity: str) -> Dict:
        """Scenario: Accelerate supplier payments for discounts."""
        acceleration_days = parameters.get("acceleration_days", 10)
        discount_rate = parameters.get("discount_rate", 0.02)  # 2% discount
        participation_rate = parameters.get("participation_rate", 0.3)  # 30% of suppliers participate
        
        data = self._get_base_data(entity)
        ledger = data["ledger"].copy()
        
        # Focus on unpaid AP
        ap_unpaid = ledger[(ledger["type"] == "AP") & (ledger["paid_date"] == "")].copy()
        
        if len(ap_unpaid) == 0:
            return {"scenario": "Payment Acceleration", "results": {"message": "No unpaid AP found"}}
        
        # Calculate eligible amounts
        eligible_ap = ap_unpaid.sample(frac=participation_rate) if len(ap_unpaid) > 0 else ap_unpaid
        total_eligible = eligible_ap["amount"].sum()
        discount_savings = total_eligible * discount_rate
        
        # Cash flow impact (earlier payment but with savings)
        net_cash_impact = total_eligible - discount_savings
        
        return {
            "scenario": "Payment Acceleration",
            "parameters": {
                "acceleration_days": acceleration_days,
                "discount_rate": discount_rate * 100,
                "participation_rate": participation_rate * 100
            },
            "results": {
                "eligible_ap_amount": float(total_eligible),
                "discount_savings": float(discount_savings),
                "net_cash_impact": float(net_cash_impact),
                "roi_percentage": float(discount_savings / total_eligible * 100) if total_eligible > 0 else 0
            }
        }
        
    def _scenario_seasonal_impact(self, parameters: Dict, entity: str) -> Dict:
        """Scenario: Seasonal cash flow variations."""
        seasonal_factor = parameters.get("seasonal_factor", {"Q4": 1.2, "Q1": 0.8})  # 20% increase in Q4, 20% decrease in Q1
        
        data = self._get_base_data(entity)
        transactions = data["transactions"].copy()
        transactions["date"] = pd.to_datetime(transactions["date"])
        transactions["quarter"] = transactions["date"].dt.quarter
        
        # Apply seasonal adjustments
        adjusted_transactions = transactions.copy()
        for quarter, factor in seasonal_factor.items():
            if quarter.startswith("Q"):
                q_num = int(quarter[1])
                mask = adjusted_transactions["quarter"] == q_num
                adjusted_transactions.loc[mask, "amount"] = adjusted_transactions.loc[mask, "amount"] * factor
        
        # Calculate impact
        original_total = transactions["amount"].sum()
        adjusted_total = adjusted_transactions["amount"].sum()
        seasonal_impact = adjusted_total - original_total
        
        quarterly_impact = {}
        for q in [1, 2, 3, 4]:
            orig_q = transactions[transactions["quarter"] == q]["amount"].sum()
            adj_q = adjusted_transactions[adjusted_transactions["quarter"] == q]["amount"].sum()
            quarterly_impact[f"Q{q}"] = float(adj_q - orig_q)
        
        return {
            "scenario": "Seasonal Impact Analysis",
            "parameters": {"seasonal_factors": seasonal_factor},
            "results": {
                "total_seasonal_impact": float(seasonal_impact),
                "quarterly_impacts": quarterly_impact,
                "baseline_annual_flow": float(original_total),
                "adjusted_annual_flow": float(adjusted_total)
            }
        }
        
    def _scenario_liquidity_stress(self, parameters: Dict, entity: str) -> Dict:
        """Scenario: Liquidity stress test."""
        stress_scenarios = parameters.get("stress_scenarios", [
            {"name": "Market Disruption", "cash_outflow_increase": 0.5, "inflow_decrease": 0.3},
            {"name": "Credit Crunch", "cash_outflow_increase": 0.3, "inflow_decrease": 0.5},
            {"name": "Operational Crisis", "cash_outflow_increase": 0.7, "inflow_decrease": 0.2}
        ])
        
        data = self._get_base_data(entity)
        current_balance = data["balances"]["balance"].sum()
        transactions = data["transactions"].copy()
        
        # Calculate baseline daily flows
        daily_inflows = transactions[transactions["amount"] > 0].groupby("date")["amount"].sum().mean()
        daily_outflows = abs(transactions[transactions["amount"] < 0].groupby("date")["amount"].sum().mean())
        
        stress_results = {}
        
        for scenario in stress_scenarios:
            name = scenario["name"]
            outflow_increase = scenario["cash_outflow_increase"]
            inflow_decrease = scenario["inflow_decrease"]
            
            # Stressed flows
            stressed_daily_inflow = daily_inflows * (1 - inflow_decrease)
            stressed_daily_outflow = daily_outflows * (1 + outflow_increase)
            stressed_net_daily = stressed_daily_inflow - stressed_daily_outflow
            
            # Days until liquidity exhaustion
            if stressed_net_daily < 0:
                days_to_exhaustion = current_balance / abs(stressed_net_daily)
            else:
                days_to_exhaustion = float('inf')
                
            stress_results[name] = {
                "stressed_daily_net": float(stressed_net_daily),
                "days_to_exhaustion": float(days_to_exhaustion) if days_to_exhaustion != float('inf') else 999,
                "stressed_inflow": float(stressed_daily_inflow),
                "stressed_outflow": float(stressed_daily_outflow)
            }
        
        return {
            "scenario": "Liquidity Stress Test",
            "parameters": {"current_balance": float(current_balance)},
            "results": {
                "baseline_flows": {
                    "daily_inflow": float(daily_inflows),
                    "daily_outflow": float(daily_outflows),
                    "net_daily": float(daily_inflows - daily_outflows)
                },
                "stress_scenarios": stress_results
            }
        }
        
    def _assess_liquidity_risk(self, liquidity_impact: float, min_scenario: float) -> Dict:
        """Assess liquidity risk level."""
        if min_scenario < 0:
            risk_level = "critical"
            message = f"Scenario results in negative cash position: ${min_scenario:,.0f}"
        elif liquidity_impact < -1000000:  # -$1M impact
            risk_level = "high" 
            message = f"Significant liquidity impact: ${liquidity_impact:,.0f}"
        elif liquidity_impact < -100000:  # -$100K impact
            risk_level = "medium"
            message = f"Moderate liquidity impact: ${liquidity_impact:,.0f}"
        else:
            risk_level = "low"
            message = f"Limited liquidity impact: ${liquidity_impact:,.0f}"
            
        return {"level": risk_level, "message": message}
        
    def _assess_fx_risk(self, impact_percentage: float) -> Dict:
        """Assess FX risk level."""
        if abs(impact_percentage) > 10:
            risk_level = "critical"
            message = f"Severe FX impact: {impact_percentage:.1f}% portfolio impact"
        elif abs(impact_percentage) > 5:
            risk_level = "high"
            message = f"High FX impact: {impact_percentage:.1f}% portfolio impact"
        elif abs(impact_percentage) > 2:
            risk_level = "medium" 
            message = f"Moderate FX impact: {impact_percentage:.1f}% portfolio impact"
        else:
            risk_level = "low"
            message = f"Low FX impact: {impact_percentage:.1f}% portfolio impact"
            
        return {"level": risk_level, "message": message}
        
    def _assess_collection_risk(self, affected_amount: float, total_ar: float) -> Dict:
        """Assess collection risk level."""
        impact_ratio = affected_amount / total_ar if total_ar > 0 else 0
        
        if impact_ratio > 0.5:
            risk_level = "high"
            message = f"High collection risk: ${affected_amount:,.0f} ({impact_ratio:.1%} of AR)"
        elif impact_ratio > 0.25:
            risk_level = "medium"
            message = f"Moderate collection risk: ${affected_amount:,.0f} ({impact_ratio:.1%} of AR)"
        else:
            risk_level = "low"
            message = f"Low collection risk: ${affected_amount:,.0f} ({impact_ratio:.1%} of AR)"
            
        return {"level": risk_level, "message": message}


@trace_operation("scenario_analysis")
@monitor_performance("whatif_node")
def node_whatifs(state: AgentState):
    """Enhanced what-if scenario analysis with multiple scenario types."""
    from ...infrastructure.observability import get_observability_manager
    
    observability = get_observability_manager()
    logger = observability.get_logger("graph.whatifs")
    
    entity = state.get("entity")
    question = state.get("question", "").lower()
    
    logger.info("Starting scenario analysis", entity=entity, question_preview=question[:100])
    
    try:
        engine = TreasuryScenarioEngine()
        
        # Intelligent scenario selection based on question content
        scenario_name, parameters = _parse_scenario_request(question)
        
        if not scenario_name:
            # Default comprehensive scenario
            scenario_name = "ap_delay"
            parameters = {"delay_days": 7, "impact_percentage": 100}
        
        # Run the scenario
        result = engine.run_scenario(scenario_name, parameters, entity)
        
        state["result"] = result
        
        logger.info("Scenario analysis completed", 
                   entity=entity, 
                   scenario=scenario_name,
                   risk_level=result.get("risk_assessment", {}).get("level", "unknown"))
        
        # Record success metric
        observability.record_metric(
            "counter", "scenario_analyses_total", 1,
            {"entity": entity or "all", "scenario": scenario_name, "status": "success"}
        )
        
        return state
        
    except Exception as e:
        logger.error("Scenario analysis failed", 
                    entity=entity, 
                    error=str(e), 
                    error_type=type(e).__name__)
        
        # Record error metric
        observability.record_metric(
            "counter", "scenario_analyses_total", 1,
            {"entity": entity or "all", "status": "failed"}
        )
        
        # Fallback to simple scenario
        try:
            from ...tools.mock_bank_api import MockBankAPI
            bank_api = MockBankAPI()
            tx = bank_api.transactions.copy()
            tx["date"] = pd.to_datetime(tx["date"])
            ap = tx[tx["category"] == "AP"].copy()
            ap["date"] = ap["date"] + pd.Timedelta(days=7)
            others = tx[tx["category"] != "AP"]
            new = pd.concat([others, ap])
            daily = new.groupby(new["date"].dt.date)["amount"].sum()
            
            state["result"] = {
                "scenario": "Simple AP Delay (Fallback)",
                "results": {"what_if_daily": daily.tail(60).to_dict()},
                "error": f"Advanced scenario analysis failed: {str(e)}"
            }
        except Exception as fallback_error:
            state["result"] = {
                "error": f"Scenario analysis failed: {str(e)}. Fallback failed: {str(fallback_error)}"
            }
        
        return state


def _parse_scenario_request(question: str) -> tuple:
    """Parse user question to determine appropriate scenario and parameters."""
    question = question.lower()
    
    # AP delay scenarios
    if any(term in question for term in ["ap delay", "payment delay", "supplier delay"]):
        days = 7  # default
        if "14 days" in question or "two weeks" in question:
            days = 14
        elif "30 days" in question or "month" in question:
            days = 30
        return "ap_delay", {"delay_days": days, "impact_percentage": 100}
    
    # FX stress scenarios  
    elif any(term in question for term in ["fx", "currency", "exchange rate", "dollar"]):
        return "fx_stress", {"currency_shocks": {"EUR": -0.1, "GBP": -0.15}}
    
    # Collection delay scenarios
    elif any(term in question for term in ["collection", "receivables", "ar delay"]):
        return "collection_delay", {"delay_days": 14, "impact_percentage": 50}
    
    # Monte Carlo scenarios
    elif any(term in question for term in ["monte carlo", "simulation", "probability"]):
        return "monte_carlo", {"days_ahead": 30, "simulations": 1000}
    
    # Liquidity stress
    elif any(term in question for term in ["liquidity", "stress", "crisis"]):
        return "liquidity_stress", {}
    
    # Seasonal scenarios
    elif any(term in question for term in ["seasonal", "quarterly", "q1", "q2", "q3", "q4"]):
        return "seasonal_impact", {"seasonal_factor": {"Q4": 1.2, "Q1": 0.8}}
    
    # Payment acceleration
    elif any(term in question for term in ["acceleration", "early payment", "discount"]):
        return "payment_acceleration", {"acceleration_days": 10, "discount_rate": 0.02}
    
    # Default
    return None, {}