from ..graph.graph import build_graph
from ..infrastructure.di.container import Container
from ..infrastructure.events.event_bus import get_event_bus
from ..infrastructure.observability import (
    get_observability_manager,
    trace_operation,
    monitor_performance
)
from ..domain.services.treasury_services import TreasuryDomainService
from ..domain.events.payment_events import ChatRequestedEvent
from ..models.llm_router import LLMRouter


class ChatService:
    """Enhanced chat service with DI, events, and observability."""
    
    def __init__(
        self,
        treasury_service: TreasuryDomainService,
        container: Container
    ):
        self.treasury_service = treasury_service
        self.container = container
        self.graph = build_graph()
        self.event_bus = get_event_bus()
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("services.chat")
    
    def _format_response_to_natural_language(self, result_data: any, intent: str, question: str) -> str:
        """Format raw data into natural language response using LLM."""
        try:
            llm = LLMRouter().cheap()
            
            # Create a prompt to convert data to natural language
            if intent == "balances" and isinstance(result_data, list) and len(result_data) > 0:
                # Format balance data
                balance_info = []
                total_balance = 0
                for account in result_data:
                    balance = account.get('balance', 0)
                    account_type = account.get('account_type', 'Account')
                    currency = account.get('currency', 'USD')
                    
                    balance_info.append(f"- {account_type}: ${balance:,.2f} {currency}")
                    total_balance += balance
                
                balance_summary = "\n".join(balance_info)
                
                prompt = f"""
                The user asked: "{question}"
                
                Here are the account balances:
                {balance_summary}
                
                Total cash position: ${total_balance:,.2f}
                
                Please provide a clear, professional summary of the cash position in natural language. 
                Be concise but informative. Format currency amounts nicely.
                """
                
                response = llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            
            elif isinstance(result_data, dict) and "error" in result_data:
                return f"I encountered an issue retrieving that information: {result_data['error']}"
            
            elif result_data is None or (isinstance(result_data, list) and len(result_data) == 0):
                return "I don't have any data available for that request at the moment."
            
            elif intent == "kpis" and isinstance(result_data, dict):
                # Special handling for KPI results
                return self._format_kpi_response(result_data)
            
            elif intent == "whatifs" and isinstance(result_data, dict):
                # Special handling for what-if scenario results
                return self._format_scenario_response(result_data)
            
            else:
                # Generic formatting for other intents
                prompt = f"""
                The user asked: "{question}"
                
                Here is the data I retrieved:
                {str(result_data)[:1000]}  
                
                Please provide a clear, professional summary of this information in natural language.
                Be concise but informative.
                """
                
                response = llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
                
        except Exception as e:
            self.logger.warning(f"Failed to format response to natural language: {str(e)}")
            # Fallback to basic formatting
            if intent == "balances" and isinstance(result_data, list):
                if len(result_data) == 0:
                    return "No account balances found."
                
                total = sum(account.get('balance', 0) for account in result_data)
                account_count = len(result_data)
                return f"I found {account_count} account(s) with a total balance of ${total:,.2f}."
            
            return "I retrieved some information but had trouble formatting it. Please try asking again."
            
    def _format_kpi_response(self, kpi_data: dict) -> str:
        """Format KPI results into a concise natural language response."""
        try:
            if "kpis" not in kpi_data:
                return "KPI data is not available in the expected format."
                
            kpis = kpi_data["kpis"]
            
            # Extract key metrics for summary
            summary_items = []
            
            # DSO/DPO
            if "dso" in kpis and "dpo" in kpis:
                summary_items.append(f"Days Sales Outstanding (DSO): {kpis['dso']:.1f} days")
                summary_items.append(f"Days Payable Outstanding (DPO): {kpis['dpo']:.1f} days")
            
            # Cash flow metrics (last 30 days)
            if "cash_flow" in kpis and "30_days" in kpis["cash_flow"]:
                cf_30 = kpis["cash_flow"]["30_days"]
                net_flow = cf_30.get("net_flow", 0)
                summary_items.append(f"30-day Net Cash Flow: ${net_flow:,.2f}")
                
            # Liquidity
            if "liquidity" in kpis:
                liq = kpis["liquidity"]
                total_liq = liq.get("total_liquidity", 0)
                days_liq = liq.get("days_of_liquidity", 0)
                summary_items.append(f"Total Liquidity: ${total_liq:,.2f}")
                if days_liq < 999:
                    summary_items.append(f"Days of Liquidity: {days_liq:.0f} days")
                    
            # Working capital
            if "working_capital" in kpis:
                wc = kpis["working_capital"]
                if "net_working_capital" in wc:
                    net_wc = wc["net_working_capital"]
                    summary_items.append(f"Net Working Capital: ${net_wc:,.2f}")
            
            if summary_items:
                response = "Here are your key treasury performance indicators:\n\n"
                response += "\n".join([f"• {item}" for item in summary_items])
                
                # Add calculation timestamp
                if "calculation_timestamp" in kpi_data:
                    calc_time = kpi_data["calculation_timestamp"][:10]  # Just the date
                    response += f"\n\n*Calculated as of {calc_time}*"
                    
                return response
            else:
                return "KPI calculations completed but no standard metrics were found."
                
        except Exception as e:
            self.logger.warning(f"Failed to format KPI response: {str(e)}")
            return "KPI calculations completed. Please check the detailed results in your dashboard."
            
    def _format_scenario_response(self, scenario_data: dict) -> str:
        """Format what-if scenario results into natural language."""
        try:
            if "scenario" not in scenario_data:
                return "Scenario analysis completed but results are not in expected format."
                
            scenario_name = scenario_data["scenario"]
            results = scenario_data.get("results", {})
            risk_assessment = scenario_data.get("risk_assessment", {})
            
            response = f"**{scenario_name} Analysis Results:**\n\n"
            
            # Handle different scenario types
            if "AP" in scenario_name and "Delay" in scenario_name:
                liquidity_impact = results.get("liquidity_impact", 0)
                min_cash = results.get("min_cash_scenario", 0)
                response += f"• **Liquidity Impact:** ${liquidity_impact:,.0f}\n"
                response += f"• **Minimum Cash Position:** ${min_cash:,.0f}\n"
                response += f"• **Affected Transactions:** {results.get('affected_transactions', 0)}\n"
                
            elif "FX Stress" in scenario_name:
                total_impact = results.get("total_fx_impact", 0)
                portfolio_impact = results.get("portfolio_impact_percentage", 0)
                response += f"• **Total FX Impact:** ${total_impact:,.0f}\n"
                response += f"• **Portfolio Impact:** {portfolio_impact:.1f}%\n"
                
                fx_impact = results.get("fx_impact_by_currency", {})
                if fx_impact:
                    response += "• **Currency Breakdown:**\n"
                    for currency, impact in fx_impact.items():
                        response += f"  - {currency}: ${impact['impact']:,.0f} ({impact['shock_percentage']:.0f}% shock)\n"
                        
            elif "Monte Carlo" in scenario_name:
                percentiles = results.get("percentiles", {})
                risk_metrics = results.get("risk_metrics", {})
                response += f"• **Expected Range (30 days):**\n"
                response += f"  - 5th percentile: ${percentiles.get('5th', 0):,.0f}\n"
                response += f"  - Median (50th): ${percentiles.get('50th', 0):,.0f}\n"
                response += f"  - 95th percentile: ${percentiles.get('95th', 0):,.0f}\n"
                response += f"• **Risk Probability:** {risk_metrics.get('probability_negative', 0):.1f}% chance of negative cash\n"
                
            elif "Liquidity Stress" in scenario_name:
                stress_scenarios = results.get("stress_scenarios", {})
                response += "• **Stress Test Results:**\n"
                for scenario, metrics in stress_scenarios.items():
                    days_exhaustion = metrics.get("days_to_exhaustion", 999)
                    if days_exhaustion < 999:
                        response += f"  - {scenario}: {days_exhaustion:.0f} days until liquidity exhaustion\n"
                    else:
                        response += f"  - {scenario}: Positive cash flow maintained\n"
                        
            elif "Collection Delay" in scenario_name:
                affected_amount = results.get("affected_ar_amount", 0)
                total_ar = results.get("total_ar_outstanding", 0)
                response += f"• **Affected AR:** ${affected_amount:,.0f}\n"
                response += f"• **Total AR Outstanding:** ${total_ar:,.0f}\n"
                
            else:
                # Generic handling
                response += "• **Key Metrics:**\n"
                for key, value in results.items():
                    if isinstance(value, (int, float)) and key != "daily_flows":
                        response += f"  - {key.replace('_', ' ').title()}: "
                        if abs(value) > 1000:
                            response += f"${value:,.0f}\n"
                        else:
                            response += f"{value:.2f}\n"
            
            # Add risk assessment
            if risk_assessment:
                risk_level = risk_assessment.get("level", "unknown")
                risk_message = risk_assessment.get("message", "")
                response += f"\n**Risk Assessment:** {risk_level.upper()}\n"
                response += f"{risk_message}"
                
            return response
            
        except Exception as e:
            self.logger.warning(f"Failed to format scenario response: {str(e)}")
            return "Scenario analysis completed. The results show various impacts on cash flow and liquidity."

    @trace_operation("chat_processing")
    @monitor_performance("chat_service")
    async def process_chat(self, question: str, entity: str = None) -> dict:
        """Process chat request with full observability."""
        
        # Emit domain event
        chat_event = ChatRequestedEvent(
            question=question,
            entity=entity
        )
        try:
            await self.event_bus.publish(chat_event)
        except Exception as e:
            self.logger.warning("Failed to publish chat event", error=str(e))
        
        # Log processing start
        self.logger.info(
            "Starting chat processing",
            entity=entity,
            question_preview=question[:100] if question else None
        )
        
        try:
            # Process with graph
            state = {"question": question or "", "entity": entity or ""}
            final_state = self.graph.invoke(state)
            
            result = {
                "intent": final_state.get("intent", ""),
                "result": final_state.get("result"),
                "notes": final_state.get("notes", ""),
                "formatted_response": self._format_response_to_natural_language(
                    final_state.get("result"), 
                    final_state.get("intent", ""), 
                    question
                )
            }
            
            # Log success
            self.logger.info(
                "Chat processing completed",
                intent=result["intent"],
                entity=entity,
                has_result=bool(result["result"])
            )
            
            return result
            
        except Exception as e:
            # Log error
            self.logger.error(
                "Chat processing failed",
                entity=entity,
                error=str(e),
                error_type=type(e).__name__
            )
            raise


# Legacy function for backward compatibility
def run_chat(question: str, entity: str | None = None):
    """Legacy function - will be deprecated."""
    from ..infrastructure.di.config import get_configured_container
    
    container = get_configured_container()
    chat_service = container.get(ChatService)
    
    # Convert to sync call (not recommended for production)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(chat_service.process_chat(question, entity))