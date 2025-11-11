from typing import Dict, Any, Optional, Type, Callable, TYPE_CHECKING
from abc import ABC
import asyncio

if TYPE_CHECKING:
    from ...agents.base_agent import BaseAgent


class Container:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register_singleton(self, service_name: str, instance: Any):
        self._singletons[service_name] = instance
        
    def register_factory(self, service_name: str, factory: Callable):
        self._factories[service_name] = factory
        
    def get_service(self, service_name: str) -> Optional[Any]:
        if service_name in self._singletons:
            return self._singletons[service_name]
        elif service_name in self._factories:
            return self._factories[service_name]()
        return None
        
    def register_agent(self, agent: 'BaseAgent'):
        self.register_singleton(f"agent_{agent.agent_id}", agent)
        
    def get_agent(self, agent_id: str) -> Optional['BaseAgent']:
        return self.get_service(f"agent_{agent_id}")
        
    def get_all_agents(self) -> Dict[str, Any]:
        agents = {}
        for key, service in self._singletons.items():
            if key.startswith("agent_") and hasattr(service, 'agent_id'):
                agents[service.agent_id] = service
        return agents
        
    def connect_all_agents(self):
        agents = self.get_all_agents()
        for agent1 in agents.values():
            for agent2 in agents.values():
                if agent1.agent_id != agent2.agent_id:
                    agent1.register_peer(agent2)


container = Container()