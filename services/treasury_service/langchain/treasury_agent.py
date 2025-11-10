"""LangChain Treasury Agent - simplified implementation."""

from typing import Dict, Any, List, Optional, Union
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from ..models.llm_router import LLMRouter
from ..infrastructure.observability import trace_operation, monitor_performance, get_observability_manager

from .tools import (
    BalanceTool,
    ForecastTool, 
    KpiTool,
    AnomalyTool,
    PaymentTool,
    WhatIfTool,
    ExposureTool,
    RagTool,
    NarrativeTool
)


class TreasuryLangChainAgent:
    """Simplified LangChain-based Treasury Agent with tool integration."""
    
    def __init__(self, container=None):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("langchain.agent")
        self.container = container
        
        # Initialize LLM
        self.llm = LLMRouter().primary()  # Use primary LLM for agent reasoning
        
        # Initialize tools
        self.tools = self._create_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Simple conversation memory
        self.conversation_history: List[Dict[str, str]] = []
        
        self.logger.info("Treasury LangChain Agent initialized", 
                        tools_count=len(self.tools))
    
    def _create_tools(self) -> List[Any]:
        """Create all treasury tools for the agent."""
        tools = [
            BalanceTool(),
            ForecastTool(),
            KpiTool(),
            AnomalyTool(),
            PaymentTool(),
            WhatIfTool(),
            ExposureTool(),
            RagTool(),
            NarrativeTool()
        ]
        
        self.logger.info("Created treasury tools", count=len(tools))
        return tools
    
    def _select_and_execute_tool(self, question: str, entity: str = None) -> Dict[str, Any]:
        """Select and execute appropriate tool based on question."""
        
        # Simple tool selection logic (can be enhanced with LLM-based selection)
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['balance', 'cash', 'account', 'funds']):
            tool = self.tool_map.get('get_account_balances')
            if tool:
                return tool._run(entity=entity or "")
        
        elif any(word in question_lower for word in ['forecast', 'predict', 'future', 'projection']):
            tool = self.tool_map.get('generate_cash_forecast')
            if tool:
                return tool._run(entity=entity or "", days=30)
        
        elif any(word in question_lower for word in ['kpi', 'metric', 'performance', 'ratio']):
            tool = self.tool_map.get('calculate_treasury_kpis')
            if tool:
                return tool._run(entity=entity or "")
        
        elif any(word in question_lower for word in ['anomaly', 'unusual', 'outlier', 'suspicious']):
            tool = self.tool_map.get('detect_treasury_anomalies')
            if tool:
                return tool._run(entity=entity or "")
        
        elif any(word in question_lower for word in ['payment', 'approve', 'pay']):
            tool = self.tool_map.get('manage_payments')
            if tool:
                return tool._run(entity=entity or "", action="list")
        
        elif any(word in question_lower for word in ['scenario', 'what if', 'stress']):
            tool = self.tool_map.get('analyze_whatif_scenario')
            if tool:
                return tool._run(entity=entity or "", scenario=question)
        
        elif any(word in question_lower for word in ['exposure', 'risk', 'currency']):
            tool = self.tool_map.get('analyze_treasury_exposure')
            if tool:
                return tool._run(entity=entity or "", exposure_type="currency")
        
        elif any(word in question_lower for word in ['document', 'policy', 'search']):
            tool = self.tool_map.get('search_treasury_documents')
            if tool:
                return tool._run(query=question, entity=entity or "")
        
        elif any(word in question_lower for word in ['report', 'summary', 'narrative']):
            tool = self.tool_map.get('generate_treasury_narrative')
            if tool:
                return tool._run(entity=entity or "", report_type="summary")
        
        # Default: provide general information about available capabilities
        return {
            "success": True,
            "data": {
                "message": "I'm a Treasury Agent with access to various financial tools and data.",
                "available_capabilities": [
                    "Account balance inquiries",
                    "Cash flow forecasting", 
                    "Treasury KPI calculations",
                    "Anomaly detection",
                    "Payment management",
                    "Risk exposure analysis",
                    "Document search",
                    "Report generation"
                ]
            }
        }
    
    @trace_operation("langchain_agent_execution")
    @monitor_performance("langchain_agent")
    def invoke(self, question: str, entity: str = None, **kwargs) -> Dict[str, Any]:
        """Execute the agent with a question using simplified tool selection."""
        
        self.logger.info("Executing LangChain agent", 
                        question=question[:100], entity=entity)
        
        try:
            # Execute tool selection and get result
            tool_result = self._select_and_execute_tool(question, entity)
            
            # Generate natural language response using LLM
            if tool_result.get("success"):
                tool_data = tool_result.get("data", {})
                
                # Create prompt for natural language response
                prompt = f"""
                Based on the following treasury data, provide a clear, professional response to the user's question.
                
                User Question: {question}
                Entity: {entity or "Not specified"}
                Tool Result: {json.dumps(tool_data, indent=2)}
                
                Provide a concise, actionable response that directly addresses the user's question.
                """
                
                llm_response = self.llm.invoke(prompt)
                response_text = getattr(llm_response, 'content', str(llm_response))
                
            else:
                response_text = f"I encountered an issue: {tool_result.get('error', 'Unknown error')}"
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": question,
                "entity": entity or ""
            })
            
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_text,
                "tool_used": tool_result.get("tool_name", "unknown")
            })
            
            # Keep only last 20 messages
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            response = {
                "result": response_text,
                "tool_result": tool_result,
                "entity": entity,
                "question": question
            }
            
            self.logger.info("LangChain agent execution completed", 
                           entity=entity, has_output=bool(response_text))
            
            # Record success metric
            self.observability.record_metric(
                "counter", "langchain_agent_executions_total", 1,
                {"status": "success", "entity": entity or "none"}
            )
            
            return response
            
        except Exception as e:
            self.logger.error("LangChain agent execution failed",
                            question=question[:100], entity=entity,
                            error=str(e), error_type=type(e).__name__)
            
            # Record error metric
            self.observability.record_metric(
                "counter", "langchain_agent_executions_total", 1,
                {"status": "error", "error_type": type(e).__name__}
            )
            
            return {
                "result": f"I encountered an error processing your request: {str(e)}",
                "error": str(e),
                "entity": entity,
                "question": question
            }
    
    async def ainvoke(self, question: str, entity: str = None, **kwargs) -> Dict[str, Any]:
        """Async execution - delegate to sync for now."""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self.invoke, question, entity)
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.conversation_history.clear()
        self.logger.info("Conversation memory cleared")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current memory state."""
        try:
            return {
                "message_count": len(self.conversation_history),
                "memory_buffer_size": 20,  # Max messages we keep
                "last_messages": [
                    {"role": msg["role"], "content": str(msg["content"])[:100]}
                    for msg in self.conversation_history[-3:]  # Show last 3 messages
                ],
                "available_tools": len(self.tools)
            }
        except Exception as e:
            return {"error": str(e), "message_count": 0}