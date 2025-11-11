from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging


class AgentRole(Enum):
    ORDER_MANAGER = "order_manager"
    PAYMENT_PROCESSOR = "payment_processor"


class AgentMessage:
    def __init__(self, sender_id: str, content: Dict[str, Any]):
        self.sender_id = sender_id
        self.content = content
        self.timestamp = datetime.now()


class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: AgentRole):
        self.agent_id = agent_id
        self.role = role
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.status = "initialized"
        
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests - must be implemented by subclasses"""
        pass
        
    @abstractmethod 
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle messages from other agents"""
        pass
        
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return []
        
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self.status
        }



