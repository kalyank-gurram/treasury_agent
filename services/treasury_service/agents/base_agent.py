"""Base agent class for multi-agent treasury management system."""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from .infrastructure.observability import get_observability_manager


class AgentRole(Enum):
    """Roles that agents can assume in the treasury management system."""
    RISK_MANAGER = "risk_manager"
    COLLECTIONS_SPECIALIST = "collections_specialist"
    INVESTMENT_ADVISOR = "investment_advisor"
    COMPLIANCE_OFFICER = "compliance_officer"
    TREASURY_COORDINATOR = "treasury_coordinator"
    PAYMENT_OPTIMIZER = "payment_optimizer"
    CASH_ANALYST = "cash_analyst"


class AgentCapability(Enum):
    """Capabilities that agents can provide."""
    RISK_ASSESSMENT = "risk_assessment"
    LIQUIDITY_MANAGEMENT = "liquidity_management"
    COLLECTIONS_OPTIMIZATION = "collections_optimization"
    INVESTMENT_ANALYSIS = "investment_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    PAYMENT_PRIORITIZATION = "payment_prioritization"
    CASH_FORECASTING = "cash_forecasting"
    SCENARIO_ANALYSIS = "scenario_analysis"
    RECONCILIATION = "reconciliation"
    REPORTING = "reporting"


class MessageType(Enum):
    """Types of messages that agents can exchange."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ALERT = "alert"
    CONSENSUS_PROPOSAL = "consensus_proposal"
    CONSENSUS_VOTE = "consensus_vote"
    STATUS_UPDATE = "status_update"


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    message_id: str
    sender_id: str
    receiver_id: Optional[str]  # None for broadcast messages
    message_type: MessageType
    priority: MessagePriority
    content: Dict[str, Any]
    timestamp: datetime
    requires_response: bool = False
    response_timeout: Optional[timedelta] = None
    correlation_id: Optional[str] = None
    

@dataclass
class AgentDecision:
    """Structure for agent decisions and recommendations."""
    decision_id: str
    agent_id: str
    decision_type: str
    recommendation: str
    confidence_score: float  # 0-1
    supporting_data: Dict[str, Any]
    risk_assessment: Optional[str] = None
    financial_impact: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    

@dataclass
class AgentCapabilityInfo:
    """Information about an agent's capabilities."""
    capability: AgentCapability
    confidence_level: float  # 0-1, how confident the agent is in this capability
    processing_time_estimate: timedelta
    dependencies: List[AgentCapability] = field(default_factory=list)
    

class BaseAgent(ABC):
    """Base class for all treasury management agents."""
    
    def __init__(self, agent_id: str, role: AgentRole, capabilities: List[AgentCapability]):
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities
        self.status = "active"
        
        # Communication
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.response_handlers: Dict[str, Callable] = {}
        self.subscriptions: Set[MessageType] = set()
        
        # Performance tracking
        self.decisions_made = 0
        self.successful_decisions = 0
        self.average_response_time = timedelta(seconds=0)
        self.last_activity = datetime.now()
        
        # Observability
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger(f"agents.{role.value}")
        
        # Agent-specific configuration
        self.config = self._initialize_config()
        
        self.logger.info(f"Agent {agent_id} ({role.value}) initialized with capabilities: {[cap.value for cap in capabilities]}")
        
    @abstractmethod
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize agent-specific configuration."""
        pass
        
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message and optionally return a response."""
        pass
        
    @abstractmethod
    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a decision based on provided context."""
        pass
        
    async def start(self):
        """Start the agent's message processing loop."""
        self.logger.info(f"Starting agent {self.agent_id}")
        self.status = "active"
        
        # Start message processing task
        asyncio.create_task(self._message_processing_loop())
        
    async def stop(self):
        """Stop the agent gracefully."""
        self.logger.info(f"Stopping agent {self.agent_id}")
        self.status = "stopping"
        
        # Allow current operations to complete
        await asyncio.sleep(1)
        self.status = "stopped"
        
    async def _message_processing_loop(self):
        """Main message processing loop."""
        while self.status == "active":
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Process the message
                start_time = datetime.now()
                response = await self.process_message(message)
                processing_time = datetime.now() - start_time
                
                # Update performance metrics
                self._update_performance_metrics(processing_time)
                
                # Send response if required
                if response and hasattr(self, 'communication_hub'):
                    await self.communication_hub.send_message(response)
                    
                # Mark message as processed
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                # No messages, continue loop
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}", error_type=type(e).__name__)
                
    async def send_message(self, receiver_id: str, message_type: MessageType, 
                          content: Dict[str, Any], priority: MessagePriority = MessagePriority.MEDIUM,
                          requires_response: bool = False) -> str:
        """Send a message to another agent."""
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            message_id=message_id,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            priority=priority,
            content=content,
            timestamp=datetime.now(),
            requires_response=requires_response
        )
        
        if hasattr(self, 'communication_hub'):
            await self.communication_hub.send_message(message)
            
        return message_id
        
    async def broadcast_message(self, message_type: MessageType, content: Dict[str, Any],
                              priority: MessagePriority = MessagePriority.MEDIUM) -> str:
        """Broadcast a message to all agents."""
        return await self.send_message(None, message_type, content, priority)
        
    async def request_capability(self, capability: AgentCapability, 
                               parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Request a specific capability from the agent network."""
        if hasattr(self, 'communication_hub'):
            return await self.communication_hub.request_capability(
                self.agent_id, capability, parameters
            )
        return None
        
    def subscribe_to_message_type(self, message_type: MessageType):
        """Subscribe to a specific type of message."""
        self.subscriptions.add(message_type)
        
    def unsubscribe_from_message_type(self, message_type: MessageType):
        """Unsubscribe from a specific type of message."""
        self.subscriptions.discard(message_type)
        
    def can_handle_capability(self, capability: AgentCapability) -> bool:
        """Check if this agent can handle a specific capability."""
        return capability in self.capabilities
        
    def get_capability_info(self, capability: AgentCapability) -> Optional[AgentCapabilityInfo]:
        """Get information about a specific capability."""
        if not self.can_handle_capability(capability):
            return None
            
        # Default implementation - should be overridden by subclasses
        return AgentCapabilityInfo(
            capability=capability,
            confidence_level=0.7,
            processing_time_estimate=timedelta(seconds=5)
        )
        
    def _update_performance_metrics(self, processing_time: timedelta):
        """Update agent performance metrics."""
        self.last_activity = datetime.now()
        
        # Update average response time using exponential moving average
        alpha = 0.1  # Smoothing factor
        if self.average_response_time.total_seconds() == 0:
            self.average_response_time = processing_time
        else:
            current_avg = self.average_response_time.total_seconds()
            new_avg = (1 - alpha) * current_avg + alpha * processing_time.total_seconds()
            self.average_response_time = timedelta(seconds=new_avg)
            
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self.status,
            "capabilities": [cap.value for cap in self.capabilities],
            "decisions_made": self.decisions_made,
            "success_rate": self.successful_decisions / max(1, self.decisions_made),
            "average_response_time": self.average_response_time.total_seconds(),
            "last_activity": self.last_activity.isoformat(),
            "queue_size": self.message_queue.qsize()
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform agent health check."""
        health_status = "healthy"
        issues = []
        
        # Check if agent is responsive
        time_since_activity = datetime.now() - self.last_activity
        if time_since_activity > timedelta(minutes=5):
            health_status = "degraded"
            issues.append("No recent activity detected")
            
        # Check queue size
        if self.message_queue.qsize() > 100:
            health_status = "degraded"
            issues.append("Message queue backlog detected")
            
        # Check success rate
        if self.decisions_made > 10:
            success_rate = self.successful_decisions / self.decisions_made
            if success_rate < 0.8:
                health_status = "degraded"
                issues.append(f"Low success rate: {success_rate:.2%}")
                
        return {
            "agent_id": self.agent_id,
            "health_status": health_status,
            "issues": issues,
            "last_check": datetime.now().isoformat()
        }
        
    def record_decision(self, decision: AgentDecision, success: bool = True):
        """Record a decision made by this agent."""
        self.decisions_made += 1
        if success:
            self.successful_decisions += 1
            
        # Record metrics
        self.observability.record_metric(
            "counter", f"agent_decisions_total", 1,
            {"agent_id": self.agent_id, "role": self.role.value, "success": str(success)}
        )
        
        self.observability.record_metric(
            "gauge", f"agent_confidence_score", decision.confidence_score,
            {"agent_id": self.agent_id, "role": self.role.value, "decision_type": decision.decision_type}
        )
        
    async def collaborate_on_decision(self, decision_context: Dict[str, Any], 
                                    required_capabilities: List[AgentCapability]) -> List[AgentDecision]:
        """Collaborate with other agents to make a complex decision."""
        collaboration_id = str(uuid.uuid4())
        
        self.logger.info(f"Starting collaboration {collaboration_id} for decision requiring: {[cap.value for cap in required_capabilities]}")
        
        # Request input from agents with required capabilities
        collaboration_responses = []
        
        for capability in required_capabilities:
            if hasattr(self, 'communication_hub'):
                response = await self.communication_hub.request_capability(
                    self.agent_id, capability, decision_context
                )
                if response:
                    collaboration_responses.append(response)
                    
        return collaboration_responses
        
    async def participate_in_consensus(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Participate in a consensus decision-making process."""
        # Analyze the proposal
        analysis = await self._analyze_consensus_proposal(proposal)
        
        # Return vote with rationale
        return {
            "agent_id": self.agent_id,
            "vote": analysis["vote"],  # "approve", "reject", "abstain"
            "confidence": analysis["confidence"],
            "rationale": analysis["rationale"],
            "suggested_modifications": analysis.get("modifications", [])
        }
        
    @abstractmethod
    async def _analyze_consensus_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a consensus proposal - must be implemented by subclasses."""
        pass