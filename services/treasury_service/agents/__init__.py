"""Multi-agent collaboration framework for treasury management."""

from .base_agent import (
    BaseAgent, AgentRole, AgentMessage, AgentCapability, AgentDecision,
    MessageType, MessagePriority
)
from .risk_manager import RiskManagerAgent
from .collections_specialist import CollectionsSpecialistAgent  
from .investment_advisor import InvestmentAdvisorAgent
from .compliance_officer import ComplianceOfficerAgent
from .treasury_coordinator import TreasuryCoordinatorAgent, WorkflowType, WorkflowStatus
from .communication_hub import CommunicationHub, ConsensusEngine, ConsensusMethod

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentRole", 
    "AgentMessage",
    "AgentCapability",
    "AgentDecision",
    "MessageType",
    "MessagePriority",
    
    # Specialized agents
    "RiskManagerAgent",
    "CollectionsSpecialistAgent",
    "InvestmentAdvisorAgent", 
    "ComplianceOfficerAgent",
    "TreasuryCoordinatorAgent",
    
    # Workflow types
    "WorkflowType",
    "WorkflowStatus",
    
    # Communication infrastructure
    "CommunicationHub",
    "ConsensusEngine",
    "ConsensusMethod"
]