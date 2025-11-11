"""
Order Agent - Processes Orders (Like Treasury Coordinator)

ONLY 2 OPERATIONS:
1. process_order - receives order from API
2. call_graph - triggers the workflow graph
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentRole, AgentMessage


class OrderAgent(BaseAgent):
    """Simplified Order Agent following Treasury Agent pattern"""
    
    def __init__(self):
        super().__init__("order_agent", AgentRole.ORDER_MANAGER)
        self.orders = {}
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process order requests - Treasury Agent pattern"""
        request_type = request.get("type")
        
        if request_type == "create_order":
            return await self._create_order(request)
        elif request_type == "get_order_status":
            return await self._get_order_status(request)
        else:
            return {"error": "Unknown request type"}
            
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle messages from other agents - Treasury Agent pattern"""
        action = message.content.get("action")
        
        if action == "payment_validated":
            print(f"✅ Order Agent: Payment validated for order {message.content.get('order_id')}")
        else:
            print(f"📦 Order Agent received: {action}")
            
        return {"status": "acknowledged"}
    
    async def _create_order(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order"""
        order_id = f"ord_{len(self.orders) + 1}"
        
        order_data = {
            "order_id": order_id,
            "customer": request.get("customer"),
            "items": request.get("items", []),
            "total": request.get("total", 0),
            "status": "created"
        }
        
        self.orders[order_id] = order_data
        
        print(f"📦 Created order: {order_id}")
        print(f"   Customer: {order_data['customer']}")
        print(f"   Total: ${order_data['total']}")
        
        return order_data
    
    async def _get_order_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get order status"""
        order_id = request.get("order_id")
        
        if order_id in self.orders:
            return self.orders[order_id]
        else:
            return {"error": "Order not found"}
            
    def get_capabilities(self) -> list[str]:
        """Return capabilities - Treasury Agent pattern"""
        return ["create_order", "get_order_status", "order_management"]