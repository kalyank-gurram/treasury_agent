"""
Test script for persistent chat functionality.

Demonstrates how to use the new memory-aware chat system
with conversation persistence and context management.
"""

import asyncio
from pathlib import Path
import sys

# Add service to path
service_path = Path(__file__).parent.parent
sys.path.insert(0, str(service_path))

from services.persistent_chat import PersistentChatService, create_persistent_chat_service
from infrastructure.persistence.memory_store import create_memory_store
from domain.services.treasury_services import TreasuryDomainService
from infrastructure.di.config import get_configured_container


async def test_memory_functionality():
    """Test conversation memory and persistence."""
    print("🧪 Testing Treasury Agent Memory & Persistence")
    print("=" * 50)
    
    # Setup
    memory_store = create_memory_store("test_conversations.db")
    container = get_configured_container()
    treasury_service = container.get(TreasuryDomainService) 
    chat_service = create_persistent_chat_service(treasury_service, container)
    
    # Test 1: Start conversation
    print("\n1️⃣ Starting new conversation...")
    context = await chat_service.start_conversation(
        user_id="test_cfo",
        role="cfo", 
        entities=["ACME-CORP", "GLOBAL-INC"],
        session_id=None  # Auto-generate
    )
    print(f"   ✅ Session started: {context.session_id}")
    print(f"   👤 User: {context.user_id} ({context.role})")
    print(f"   🏢 Entities: {', '.join(context.entities)}")
    
    # Test 2: Memory-aware chat interactions
    print("\n2️⃣ Testing conversation memory...")
    
    questions = [
        "What's the cash position for ACME-CORP?",
        "Show me the liquidity analysis", 
        "Based on what we discussed, what's the risk level?",
        "Can you approve payment PAY-001?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n   💬 Question {i}: {question}")
        result = await chat_service.process_chat_with_memory(
            question=question,
            context=context
        )
        
        print(f"   🎯 Intent: {result['intent']}")
        print(f"   💭 Response: {result['formatted_response'][:100]}...")
        print(f"   📊 Conversation #{result['conversation_count']}")
    
    # Test 3: Conversation history
    print("\n3️⃣ Testing conversation history...")
    history = await chat_service.get_conversation_history("test_cfo")
    print(f"   📚 Found {len(history)} past conversations")
    
    # Test 4: End conversation with summary
    print("\n4️⃣ Ending conversation...")
    summary = await chat_service.end_conversation(context.session_id)
    if summary:
        print(f"   📝 Summary: {summary['summary']}")
        print(f"   💬 Messages: {summary['message_count']}")
        print(f"   🏷️ Topics: {', '.join(summary['key_topics'])}")
    
    # Test 5: Resume conversation (new session)
    print("\n5️⃣ Testing session resumption...")
    new_context = await chat_service.start_conversation(
        user_id="test_cfo",
        role="cfo",
        entities=["ACME-CORP", "GLOBAL-INC"]
    )
    
    resume_result = await chat_service.process_chat_with_memory(
        question="What did we discuss in our previous session?",
        context=new_context
    )
    print(f"   🔄 New session: {new_context.session_id}")
    print(f"   💭 Response: {resume_result['formatted_response'][:100]}...")
    
    print("\n✅ Memory functionality test completed!")
    print(f"🗃️ Database: test_conversations.db")


async def test_thread_continuity():
    """Test LangGraph thread continuity."""
    print("\n🧵 Testing LangGraph Thread Continuity")
    print("=" * 40)
    
    # This test would show how conversation context is maintained
    # across multiple interactions within the same thread
    
    from graph.memory_graph import build_graph_with_memory
    
    # Build graph with memory
    graph = build_graph_with_memory()
    thread_id = "test_thread_001"
    
    # Series of related questions in same thread
    questions = [
        "Show me account balances",
        "What about forecasts?", 
        "Any payment approvals needed?",
        "Summarize what we covered"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n   🔗 Thread message {i}: {question}")
        
        state = {"question": question, "entity": "ACME-CORP"}
        config = {"configurable": {"thread_id": thread_id}}
        
        result = await graph.ainvoke(state, config=config)
        print(f"   🎯 Intent: {result.get('intent', 'unknown')}")
        print(f"   📊 Has context from previous: {bool(result.get('messages'))}")
    
    print("\n✅ Thread continuity test completed!")


if __name__ == "__main__":
    print("🚀 Treasury Agent Memory & Persistence Tests")
    
    try:
        # Run async tests
        asyncio.run(test_memory_functionality())
        asyncio.run(test_thread_continuity())
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 All tests completed!")