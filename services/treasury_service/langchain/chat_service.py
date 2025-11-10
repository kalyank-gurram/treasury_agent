"""LangChain-based Treasury Chat Service."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from .treasury_agent import TreasuryLangChainAgent
from .memory import get_langchain_memory, TreasuryConversationMemory
from ..infrastructure.observability import trace_operation, monitor_performance, get_observability_manager
from ..infrastructure.events.event_bus import get_event_bus
from ..domain.events.payment_events import ChatRequestedEvent
from ..domain.services.treasury_services import TreasuryDomainService
from ..infrastructure.di.container import Container


class LangChainChatService:
    """LangChain-based chat service with enhanced memory and agent capabilities."""
    
    def __init__(self, treasury_service: TreasuryDomainService, container: Container):
        self.treasury_service = treasury_service
        self.container = container
        self.event_bus = get_event_bus()
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("langchain.chat_service")
        
        # Initialize LangChain agent and memory
        self.agent = TreasuryLangChainAgent()
        self.memory_manager = get_langchain_memory()
        
        self.logger.info("LangChain Chat Service initialized")
    
    @trace_operation("langchain_chat_processing")
    @monitor_performance("langchain_chat_service")
    async def process_chat_with_memory(
        self, 
        question: str,
        user_id: str,
        entity: str = None,
        user_role: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process chat with LangChain agent and persistent memory."""
        
        # Emit domain event
        chat_event = ChatRequestedEvent(question=question, entity=entity)
        try:
            await self.event_bus.publish(chat_event)
        except Exception as e:
            self.logger.warning("Failed to publish chat event", error=str(e))
        
        # Log processing start
        self.logger.info(
            "Starting LangChain chat processing",
            user_id=user_id,
            entity=entity,
            session_id=session_id,
            question_preview=question[:100] if question else None
        )
        
        try:
            # Get or create memory for this session (initializes if needed)
            self.memory_manager.get_or_create_memory(
                user_id=user_id,
                session_id=session_id,
                entity=entity,
                role=user_role
            )
            
            # Save user message to persistent storage
            user_message = HumanMessage(content=question)
            self.memory_manager.save_message(
                session_id=session_id or f"{user_id}_current",
                user_id=user_id,
                message=user_message,
                entity=entity
            )
            
            # Process with LangChain agent
            agent_result = await self.agent.ainvoke(
                question=question,
                entity=entity
            )
            
            # Extract response
            response_content = agent_result.get("result", "I'm sorry, I couldn't process that request.")
            
            # Save AI response to persistent storage
            ai_message = AIMessage(content=response_content)
            self.memory_manager.save_message(
                session_id=session_id or f"{user_id}_current",
                user_id=user_id,
                message=ai_message,
                entity=entity
            )
            
            # Format response similar to LangGraph version for compatibility
            result = {
                "intent": "langchain_processed",  # LangChain doesn't separate intent classification
                "result": response_content,
                "formatted_response": response_content,
                "notes": "Processed via LangChain agent",
                "session_id": session_id,
                "agent_type": "langchain",
                "intermediate_steps": agent_result.get("intermediate_steps", [])
            }
            
            # Log success
            self.logger.info(
                "LangChain chat processing completed",
                user_id=user_id,
                entity=entity,
                session_id=session_id,
                has_result=bool(response_content)
            )
            
            # Record success metric
            self.observability.record_metric(
                "counter", "langchain_chat_requests_total", 1,
                {"status": "success", "entity": entity or "none"}
            )
            
            return result
            
        except Exception as e:
            # Log error
            self.logger.error(
                "LangChain chat processing failed",
                user_id=user_id,
                entity=entity,
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Record error metric
            self.observability.record_metric(
                "counter", "langchain_chat_requests_total", 1,
                {"status": "error", "error_type": type(e).__name__}
            )
            
            # Return error response
            return {
                "intent": "error",
                "result": f"I encountered an error: {str(e)}",
                "formatted_response": "I'm sorry, I encountered an error processing your request. Please try again.",
                "notes": f"Error: {str(e)}",
                "session_id": session_id,
                "agent_type": "langchain",
                "error": str(e)
            }
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        self.logger.info("Retrieving LangChain conversation history", user_id=user_id, limit=limit)
        
        try:
            # Get history from memory manager
            history = self.memory_manager.get_conversation_history(user_id, limit)
            
            # Convert to expected format for compatibility with existing API
            formatted_history = []
            for entry in history:
                formatted_entry = {
                    "session_id": entry["session_id"],
                    "entity": entry["entity"],
                    "user_message": entry["content"] if entry["message_type"] == "human" else None,
                    "ai_response": entry["content"] if entry["message_type"] == "ai" else None,
                    "created_at": datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")),
                    "agent_type": "langchain"
                }
                formatted_history.append(formatted_entry)
            
            self.logger.info("LangChain conversation history retrieved", 
                           user_id=user_id, entries_count=len(formatted_history))
            
            return formatted_history
            
        except Exception as e:
            self.logger.error("Failed to retrieve LangChain conversation history", 
                            user_id=user_id, error=str(e))
            return []
    
    def get_agent_summary(self) -> Dict[str, Any]:
        """Get summary of the LangChain agent capabilities."""
        try:
            memory_summary = self.agent.get_memory_summary()
            
            return {
                "agent_type": "langchain",
                "tools_available": len(self.agent.tools),
                "tool_names": [tool.name for tool in self.agent.tools],
                "memory": memory_summary,
                "llm_model": getattr(self.agent.llm, 'model_name', 'unknown'),
                "status": "active"
            }
        except Exception as e:
            self.logger.error("Failed to get agent summary", error=str(e))
            return {"agent_type": "langchain", "status": "error", "error": str(e)}
    
    def clear_user_memory(self, user_id: str, session_id: str = None):
        """Clear memory for a user session."""
        try:
            if session_id:
                self.memory_manager.clear_session_memory(session_id)
            else:
                # Clear all sessions for user (would need implementation)
                sessions = self.memory_manager.get_active_sessions(user_id)
                for session in sessions:
                    self.memory_manager.clear_session_memory(session["session_id"])
            
            self.logger.info("User memory cleared", user_id=user_id, session_id=session_id)
            
        except Exception as e:
            self.logger.error("Failed to clear user memory", 
                            user_id=user_id, session_id=session_id, error=str(e))


def create_langchain_chat_service(
    treasury_service: TreasuryDomainService,
    container: Container
) -> LangChainChatService:
    """Factory function to create LangChain chat service."""
    return LangChainChatService(treasury_service, container)