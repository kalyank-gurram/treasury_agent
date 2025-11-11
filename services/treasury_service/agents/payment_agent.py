from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentRole, AgentMessage


class PaymentAgent(BaseAgent):
    
    def __init__(self):
        super().__init__("payment_agent", AgentRole.PAYMENT_PROCESSOR)
        self.knowledge_base = [
            "Payments are processed within 24 hours",
            "Refunds take 3-5 business days", 
            "Credit card payments are secure",
            "We accept Visa, MasterCard, and PayPal"
        ]
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment requests - Treasury Agent pattern"""
        request_type = request.get("type")
        
        if request_type == "validate_payment":
            return await self._validate_payment(request)
        elif request_type == "search_knowledge":
            return await self._search_knowledge(request)
        else:
            return {"error": "Unknown request type"}
            
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle messages from other agents - Treasury Agent pattern"""
        action = message.content.get("action")
        
        if action == "validate_payment":
            print(f"� Payment validation requested for order {message.content.get('order_id')}")
            return {"status": "payment_validated", "approved": True}
        else:
            print(f"💳 Payment Agent received: {action}")
            
        return {"status": "acknowledged"}
    
    async def _validate_payment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payment request"""
        amount = request.get("amount", 0)
        print(f"💳 Validating payment for amount: ${amount}")
        
        if 0 < amount < 10000:
            return {"status": "approved", "message": "Payment validated successfully"}
        else:
            return {"status": "rejected", "message": "Payment amount invalid"}
    
    async def _search_knowledge(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Search payment knowledge base"""
        query = request.get("query", "").lower()
        print(f"🔍 Searching knowledge for: {query}")
        
        results = []
        for item in self.knowledge_base:
            if query in item.lower():
                results.append(item)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    def get_capabilities(self) -> list[str]:
        """Return capabilities - Treasury Agent pattern"""
        return ["validate_payment", "search_knowledge", "payment_processing"]