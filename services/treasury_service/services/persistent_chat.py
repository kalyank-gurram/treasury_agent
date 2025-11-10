"""
Enhanced ChatService with memory and conversation persistence.

Extends the existing ChatService to support conversation continuity,
user context, and session management using LangGraph checkpointers.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

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
from ..infrastructure.persistence.memory_store import get_memory_store, ConversationContext


class PersistentChatService:
    """Enhanced chat service with conversation memory and persistence."""
    
    def __init__(
        self,
        treasury_service: TreasuryDomainService,
        container: Container
    ):
        self.treasury_service = treasury_service
        self.container = container
        self.event_bus = get_event_bus()
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("services.persistent_chat")
        
        # Memory management
        self.memory_store = get_memory_store()
        
        # Build graph with memory checkpointer
        self.graph = build_graph(checkpointer=self.memory_store.get_checkpointer())
        
        # Track conversation state
        self._conversation_intents: Dict[str, List[str]] = {}
        self._conversation_messages: Dict[str, List[Dict]] = {}
    
    async def start_conversation(self, user_id: str, role: str, entities: List[str], 
                               session_id: Optional[str] = None) -> ConversationContext:
        """Start new conversation or resume existing session."""
        context = self.memory_store.get_or_create_context(
            user_id=user_id,
            role=role, 
            entities=entities,
            session_id=session_id
        )
        
        # Initialize conversation tracking
        if context.session_id not in self._conversation_intents:
            self._conversation_intents[context.session_id] = []
            self._conversation_messages[context.session_id] = []
        
        self.logger.info(
            "Conversation started",
            session_id=context.session_id,
            user_id=user_id,
            role=role,
            conversation_count=context.conversation_count
        )
        
        return context
    
    async def process_chat_with_memory(
        self, 
        question: str,
        context: ConversationContext,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process chat with conversation memory and context."""
        
        # Use session_id as thread_id if not provided
        if not thread_id:
            thread_id = context.session_id
        
        # Update activity tracking
        self.memory_store.update_context_activity(context.session_id)
        
        # Emit domain event
        chat_event = ChatRequestedEvent(
            question=question,
            entity=context.entities[0] if context.entities else None
        )
        try:
            await self.event_bus.publish(chat_event)
        except Exception as e:
            self.logger.warning("Failed to publish chat event", error=str(e))
        
        # Log processing start
        self.logger.info(
            "Processing chat with memory",
            session_id=context.session_id,
            thread_id=thread_id,
            user_id=context.user_id,
            question_preview=question[:100] if question else None
        )
        
        try:
            # Prepare state with user context
            state = {
                "question": question or "",
                "entity": context.entities[0] if context.entities else "",
                "user_context": {
                    "user_id": context.user_id,
                    "role": context.role,
                    "entities": context.entities,
                    "session_id": context.session_id,
                    "conversation_count": context.conversation_count,
                    "preferences": context.preferences
                },
                "messages": []  # Will be populated by checkpointer
            }
            
            # Process with graph using memory checkpointer
            # The thread_id enables conversation continuity
            config = {"configurable": {"thread_id": thread_id}}
            final_state = await self.graph.ainvoke(state, config=config)
            
            # Track conversation history
            intent = final_state.get("intent", "")
            if intent:
                self._conversation_intents.setdefault(context.session_id, []).append(intent)
            
            # Track messages
            message_entry = {
                "timestamp": datetime.now().isoformat(),
                "role": "user", 
                "content": question,
                "intent": intent
            }
            self._conversation_messages.setdefault(context.session_id, []).append(message_entry)
            
            # Add assistant response
            response_content = self._format_response_to_natural_language(
                final_state.get("result"), 
                intent, 
                question,
                context
            )
            
            assistant_entry = {
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": response_content,
                "intent": intent
            }
            self._conversation_messages[context.session_id].append(assistant_entry)
            
            result = {
                "intent": intent,
                "result": final_state.get("result"),
                "notes": final_state.get("notes", ""),
                "formatted_response": response_content,
                "session_id": context.session_id,
                "thread_id": thread_id,
                "conversation_count": context.conversation_count + 1,
                "user_context": context
            }
            
            # Log success
            self.logger.info(
                "Chat processing with memory completed",
                session_id=context.session_id,
                intent=intent,
                has_result=bool(result["result"])
            )
            
            return result
            
        except Exception as e:
            # Log error
            self.logger.error(
                "Chat processing with memory failed",
                session_id=context.session_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for user."""
        summaries = self.memory_store.get_conversation_history(user_id, limit=20)
        
        history = []
        for summary in summaries:
            history.append({
                "session_id": summary.session_id,
                "start_time": summary.start_time.isoformat(),
                "end_time": summary.end_time.isoformat() if summary.end_time else None,
                "message_count": summary.message_count,
                "key_topics": summary.key_topics,
                "entities_discussed": summary.entities_discussed,
                "summary": summary.summary_text
            })
        
        return history
    
    async def end_conversation(self, session_id: str) -> Optional[Dict]:
        """End conversation and create summary."""
        if session_id not in self._conversation_messages:
            return None
        
        messages = self._conversation_messages[session_id]
        intents = self._conversation_intents.get(session_id, [])
        
        try:
            summary = self.memory_store.create_conversation_summary(
                session_id, messages, intents
            )
            
            # Clean up tracking
            del self._conversation_messages[session_id]
            del self._conversation_intents[session_id]
            
            self.logger.info(
                "Conversation ended and summarized",
                session_id=session_id,
                message_count=len(messages)
            )
            
            return {
                "session_id": session_id,
                "summary": summary.summary_text,
                "message_count": len(messages),
                "key_topics": summary.key_topics
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to end conversation",
                session_id=session_id,
                error=str(e)
            )
            return None
    
    def _format_response_to_natural_language(
        self, 
        result_data: Any, 
        intent: str, 
        question: str,
        context: ConversationContext
    ) -> str:
        """Enhanced response formatting with user context."""
        try:
            llm = LLMRouter().cheap()
            
            # Add user context to prompt
            user_context_prompt = f"""
            User Context:
            - Role: {context.role}
            - Accessible Entities: {', '.join(context.entities)}
            - Conversation #{context.conversation_count + 1} in this session
            """
            
            if intent == "balances" and isinstance(result_data, list) and len(result_data) > 0:
                # Format balance data with user context
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
                {user_context_prompt}
                
                The user asked: "{question}"
                
                Here are the account balances:
                {balance_summary}
                
                Total cash position: ${total_balance:,.2f}
                
                Please provide a clear, professional summary tailored to a {context.role} role.
                Be concise but informative. Format currency amounts nicely.
                Consider this is conversation #{context.conversation_count + 1} in this session.
                """
                
                response = llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            
            elif isinstance(result_data, dict) and "error" in result_data:
                return f"I encountered an issue retrieving that information: {result_data['error']}"
            
            elif result_data is None or (isinstance(result_data, list) and len(result_data) == 0):
                return f"I don't have any data available for that request at the moment. As a {context.role}, you might want to check if you have access to the relevant entities."
            
            else:
                # Generic formatting with context
                prompt = f"""
                {user_context_prompt}
                
                The user asked: "{question}"
                
                Here is the data I retrieved:
                {str(result_data)[:1000]}  
                
                Please provide a clear, professional summary tailored to a {context.role} role.
                Be concise but informative. This is conversation #{context.conversation_count + 1} in this session.
                """
                
                response = llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
                
        except Exception as e:
            self.logger.warning(f"Failed to format response with context: {str(e)}")
            
            # Fallback formatting
            if intent == "balances" and isinstance(result_data, list):
                if len(result_data) == 0:
                    return f"No account balances found for your accessible entities: {', '.join(context.entities)}"
                
                total = sum(account.get('balance', 0) for account in result_data)
                account_count = len(result_data)
                return f"Found {account_count} account(s) with total balance of ${total:,.2f} across your entities."
            
            return f"I retrieved some information but had trouble formatting it for your {context.role} role. Please try asking again."


# Factory function for dependency injection
def create_persistent_chat_service(
    treasury_service: TreasuryDomainService,
    container: Container
) -> PersistentChatService:
    """Create persistent chat service instance."""
    return PersistentChatService(treasury_service, container)