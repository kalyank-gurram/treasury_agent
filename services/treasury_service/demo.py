import asyncio
from agents.base_agent import AgentMessage
from agents.order_agent import OrderAgent
from agents.payment_agent import PaymentAgent


async def demo():
    print("Simple Learning System - Treasury Agent Pattern")
    print("==============================================")
    
    order_agent = OrderAgent()
    payment_agent = PaymentAgent()
    
    print(f"\n✅ Agents Created:")
    print(f"   Order Agent: {order_agent.get_status()}")
    print(f"   Payment Agent: {payment_agent.get_status()}")
    
    print(f"\n📋 Agent Capabilities:")
    print(f"   Order Agent: {order_agent.get_capabilities()}")
    print(f"   Payment Agent: {payment_agent.get_capabilities()}")
    
    print("\n1. Creating order via process_request...")
    order_request = {
        "type": "create_order",
        "customer": "John Doe",
        "items": ["laptop", "mouse"],
        "total": 1200
    }
    
    order_result = await order_agent.process_request(order_request)
    print(f"Order result: {order_result}")
    
    print("\n2. Validating payment via process_request...")
    payment_request = {
        "type": "validate_payment",
        "amount": 1200,
        "order_id": order_result.get("order_id")
    }
    
    payment_result = await payment_agent.process_request(payment_request)
    print(f"Payment result: {payment_result}")
    
    print("\n3. Testing agent-to-agent messaging...")
    message = AgentMessage(
        sender_id="order_agent",
        content={
            "action": "validate_payment",
            "order_id": order_result.get("order_id"),
            "amount": 1200
        }
    )
    
    response = await payment_agent.handle_message(message)
    print(f"Message response: {response}")
    
    print("\n4. Testing knowledge search...")
    knowledge_request = {
        "type": "search_knowledge",
        "query": "refund"
    }
    
    knowledge_result = await payment_agent.process_request(knowledge_request)
    print(f"Knowledge result: {knowledge_result}")
    
    print("\n✅ Demo Complete - This is how Treasury Agent works!")


if __name__ == "__main__":
    asyncio.run(demo())