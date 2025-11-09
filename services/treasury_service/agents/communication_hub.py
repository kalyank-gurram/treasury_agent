"""Communication hub and consensus engine for multi-agent coordination."""

import asyncio
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Callable
from .infrastructure.observability import get_observability_manager
from .base_agent import BaseAgent, AgentMessage, MessageType, MessagePriority, AgentCapability, AgentDecision


class ConsensusMethod(Enum):
    """Methods for reaching consensus."""
    UNANIMOUS = "unanimous"          # All agents must agree
    MAJORITY = "majority"            # More than 50% agreement
    SUPERMAJORITY = "supermajority"  # 2/3 or more agreement
    WEIGHTED = "weighted"            # Weighted by agent expertise/confidence
    QUORUM = "quorum"               # Minimum number of participants


@dataclass
class ConsensusProposal:
    """Proposal for consensus decision-making."""
    proposal_id: str
    initiator_id: str
    proposal_type: str
    content: Dict[str, Any]
    required_capabilities: List[AgentCapability]
    consensus_method: ConsensusMethod
    timeout: timedelta
    created_at: datetime
    votes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    status: str = "pending"  # pending, approved, rejected, timeout
    

@dataclass
class AgentRegistration:
    """Agent registration information."""
    agent: BaseAgent
    registered_at: datetime
    last_heartbeat: datetime
    message_count: int = 0
    capabilities: List[AgentCapability] = field(default_factory=list)
    

class CommunicationHub:
    """Central communication hub for agent coordination."""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("agents.communication_hub")
        
        # Agent registry
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.capability_index: Dict[AgentCapability, Set[str]] = defaultdict(set)
        
        # Message routing
        self.message_history: deque = deque(maxlen=1000)  # Keep last 1000 messages
        self.pending_responses: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.messages_processed = 0
        self.average_routing_time = timedelta(seconds=0)
        
    async def register_agent(self, agent: BaseAgent):
        """Register an agent with the communication hub."""
        self.logger.info(f"Registering agent {agent.agent_id} ({agent.role.value})")
        
        registration = AgentRegistration(
            agent=agent,
            registered_at=datetime.now(),
            last_heartbeat=datetime.now(),
            capabilities=agent.capabilities.copy()
        )
        
        self.registered_agents[agent.agent_id] = registration
        
        # Update capability index
        for capability in agent.capabilities:
            self.capability_index[capability].add(agent.agent_id)
            
        # Set communication hub reference in agent
        agent.communication_hub = self
        
        self.logger.info(f"Agent {agent.agent_id} registered successfully")
        
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the communication hub."""
        if agent_id in self.registered_agents:
            registration = self.registered_agents[agent_id]
            
            # Remove from capability index
            for capability in registration.capabilities:
                self.capability_index[capability].discard(agent_id)
                
            del self.registered_agents[agent_id]
            
            self.logger.info(f"Agent {agent_id} unregistered")
            
    async def send_message(self, message: AgentMessage):
        """Send a message to target agent(s)."""
        start_time = datetime.now()
        
        try:
            # Add to message history
            self.message_history.append({
                "message": message,
                "timestamp": datetime.now()
            })
            
            if message.receiver_id is None:
                # Broadcast to all agents
                await self._broadcast_message(message)
            else:
                # Send to specific agent
                await self._route_message(message)
                
            # Update metrics
            self.messages_processed += 1
            routing_time = datetime.now() - start_time
            self._update_routing_time(routing_time)
            
            # Record observability metrics
            self.observability.record_metric(
                "counter", "hub_messages_processed_total", 1,
                {"message_type": message.message_type.value, "priority": message.priority.value}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send message {message.message_id}: {e}")
            raise
            
    async def _route_message(self, message: AgentMessage):
        """Route message to a specific agent."""
        if message.receiver_id not in self.registered_agents:
            self.logger.warning(f"Agent {message.receiver_id} not found for message {message.message_id}")
            return
            
        registration = self.registered_agents[message.receiver_id]
        
        # Check if agent is subscribed to this message type
        if hasattr(registration.agent, 'subscriptions'):
            if message.message_type not in registration.agent.subscriptions and message.message_type != MessageType.RESPONSE:
                return
                
        # Add to agent's message queue
        await registration.agent.message_queue.put(message)
        registration.message_count += 1
        registration.last_heartbeat = datetime.now()
        
        self.logger.debug(f"Routed message {message.message_id} to agent {message.receiver_id}")
        
    async def _broadcast_message(self, message: AgentMessage):
        """Broadcast message to all registered agents."""
        broadcast_count = 0
        
        for agent_id, registration in self.registered_agents.items():
            # Skip sender
            if agent_id == message.sender_id:
                continue
                
            # Check subscriptions
            if hasattr(registration.agent, 'subscriptions'):
                if message.message_type not in registration.agent.subscriptions:
                    continue
                    
            # Send to agent
            targeted_message = AgentMessage(
                message_id=message.message_id,
                sender_id=message.sender_id,
                receiver_id=agent_id,
                message_type=message.message_type,
                priority=message.priority,
                content=message.content,
                timestamp=message.timestamp,
                requires_response=message.requires_response,
                response_timeout=message.response_timeout,
                correlation_id=message.correlation_id
            )
            
            await registration.agent.message_queue.put(targeted_message)
            registration.message_count += 1
            registration.last_heartbeat = datetime.now()
            broadcast_count += 1
            
        self.logger.debug(f"Broadcast message {message.message_id} to {broadcast_count} agents")
        
    async def request_capability(self, requester_id: str, capability: AgentCapability, 
                               parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Request a specific capability from available agents."""
        # Find agents with the requested capability
        capable_agents = self.capability_index.get(capability, set())
        
        if not capable_agents:
            self.logger.warning(f"No agents available for capability {capability.value}")
            return None
            
        # Select the best agent for this capability
        best_agent_id = await self._select_best_agent(capability, capable_agents, parameters)
        
        if not best_agent_id:
            return None
            
        # Send request
        request_id = str(uuid.uuid4())
        request_message = AgentMessage(
            message_id=request_id,
            sender_id=requester_id,
            receiver_id=best_agent_id,
            message_type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
            content={
                "capability": capability.value,
                "parameters": parameters,
                "request_id": request_id
            },
            timestamp=datetime.now(),
            requires_response=True,
            response_timeout=timedelta(minutes=5)
        )
        
        # Track pending response
        self.pending_responses[request_id] = {
            "requester_id": requester_id,
            "capability": capability,
            "sent_at": datetime.now(),
            "timeout_at": datetime.now() + request_message.response_timeout
        }
        
        await self.send_message(request_message)
        
        # Wait for response (simplified - in production would use async patterns)
        response = await self._wait_for_response(request_id, request_message.response_timeout)
        
        return response
        
    async def _select_best_agent(self, capability: AgentCapability, 
                               capable_agents: Set[str], parameters: Dict[str, Any]) -> Optional[str]:
        """Select the best agent for a capability request."""
        best_agent_id = None
        best_score = 0.0
        
        for agent_id in capable_agents:
            if agent_id not in self.registered_agents:
                continue
                
            registration = self.registered_agents[agent_id]
            agent = registration.agent
            
            # Get capability info
            capability_info = agent.get_capability_info(capability)
            if not capability_info:
                continue
                
            # Calculate selection score based on multiple factors
            score = capability_info.confidence_level
            
            # Factor in agent performance
            if agent.decisions_made > 0:
                success_rate = agent.successful_decisions / agent.decisions_made
                score *= (0.5 + 0.5 * success_rate)  # Boost score based on success rate
                
            # Factor in current load (queue size)
            queue_load_factor = max(0.1, 1.0 - (agent.message_queue.qsize() / 100))
            score *= queue_load_factor
            
            # Factor in response time
            avg_response_seconds = agent.average_response_time.total_seconds()
            if avg_response_seconds > 0:
                response_time_factor = max(0.1, 1.0 - (avg_response_seconds / 60))  # Penalize slow agents
                score *= response_time_factor
                
            if score > best_score:
                best_score = score
                best_agent_id = agent_id
                
        self.logger.debug(f"Selected agent {best_agent_id} for capability {capability.value} with score {best_score:.3f}")
        
        return best_agent_id
        
    async def _wait_for_response(self, request_id: str, timeout: timedelta) -> Optional[Dict[str, Any]]:
        """Wait for a response to a request."""
        # Simplified implementation - in production would use proper async/await patterns
        # For now, we'll simulate a response
        
        await asyncio.sleep(min(1.0, timeout.total_seconds() / 10))  # Simulate processing time
        
        # Clean up pending response
        if request_id in self.pending_responses:
            del self.pending_responses[request_id]
            
        # Return simulated response
        return {
            "status": "completed",
            "result": {"message": "Capability request processed successfully"},
            "agent_id": "simulated_agent",
            "processing_time": 1.0
        }
        
    def _update_routing_time(self, routing_time: timedelta):
        """Update average message routing time."""
        alpha = 0.1  # Smoothing factor
        if self.average_routing_time.total_seconds() == 0:
            self.average_routing_time = routing_time
        else:
            current_avg = self.average_routing_time.total_seconds()
            new_avg = (1 - alpha) * current_avg + alpha * routing_time.total_seconds()
            self.average_routing_time = timedelta(seconds=new_avg)
            
    def get_hub_statistics(self) -> Dict[str, Any]:
        """Get communication hub statistics."""
        return {
            "registered_agents": len(self.registered_agents),
            "messages_processed": self.messages_processed,
            "average_routing_time_ms": self.average_routing_time.total_seconds() * 1000,
            "pending_responses": len(self.pending_responses),
            "message_history_size": len(self.message_history),
            "capabilities_available": {
                cap.value: len(agents) for cap, agents in self.capability_index.items()
            }
        }
        
    async def health_check_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all registered agents."""
        health_results = {}
        
        for agent_id, registration in self.registered_agents.items():
            try:
                health_result = await registration.agent.health_check()
                health_results[agent_id] = health_result
            except Exception as e:
                health_results[agent_id] = {
                    "agent_id": agent_id,
                    "health_status": "error",
                    "issues": [f"Health check failed: {e}"],
                    "last_check": datetime.now().isoformat()
                }
                
        return health_results


class ConsensusEngine:
    """Engine for managing consensus-based decision making among agents."""
    
    def __init__(self, communication_hub: CommunicationHub):
        self.communication_hub = communication_hub
        self.observability = get_observability_manager()
        self.logger = self.observability.get_logger("agents.consensus_engine")
        
        # Active consensus processes
        self.active_proposals: Dict[str, ConsensusProposal] = {}
        
    async def initiate_consensus(self, initiator_id: str, proposal_type: str,
                               content: Dict[str, Any], required_capabilities: List[AgentCapability],
                               consensus_method: ConsensusMethod = ConsensusMethod.MAJORITY,
                               timeout: timedelta = timedelta(minutes=10)) -> str:
        """Initiate a consensus decision-making process."""
        proposal_id = str(uuid.uuid4())
        
        proposal = ConsensusProposal(
            proposal_id=proposal_id,
            initiator_id=initiator_id,
            proposal_type=proposal_type,
            content=content,
            required_capabilities=required_capabilities,
            consensus_method=consensus_method,
            timeout=timeout,
            created_at=datetime.now()
        )
        
        self.active_proposals[proposal_id] = proposal
        
        self.logger.info(f"Initiated consensus proposal {proposal_id} of type {proposal_type}")
        
        # Send proposal to all eligible agents
        await self._send_consensus_proposal(proposal)
        
        # Schedule timeout handling
        asyncio.create_task(self._handle_consensus_timeout(proposal_id, timeout))
        
        return proposal_id
        
    async def _send_consensus_proposal(self, proposal: ConsensusProposal):
        """Send consensus proposal to eligible agents."""
        # Find agents with required capabilities
        eligible_agents = set()
        
        for capability in proposal.required_capabilities:
            agents_with_capability = self.communication_hub.capability_index.get(capability, set())
            eligible_agents.update(agents_with_capability)
            
        # Send proposal to eligible agents
        for agent_id in eligible_agents:
            if agent_id == proposal.initiator_id:
                continue  # Skip initiator
                
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id="consensus_engine",
                receiver_id=agent_id,
                message_type=MessageType.CONSENSUS_PROPOSAL,
                priority=MessagePriority.HIGH,
                content={
                    "proposal_id": proposal.proposal_id,
                    "proposal_type": proposal.proposal_type,
                    "content": proposal.content,
                    "consensus_method": proposal.consensus_method.value,
                    "timeout": proposal.timeout.total_seconds()
                },
                timestamp=datetime.now(),
                requires_response=True,
                response_timeout=proposal.timeout
            )
            
            await self.communication_hub.send_message(message)
            
        self.logger.info(f"Sent consensus proposal {proposal.proposal_id} to {len(eligible_agents)} agents")
        
    async def submit_vote(self, proposal_id: str, agent_id: str, vote_data: Dict[str, Any]):
        """Submit a vote for a consensus proposal."""
        if proposal_id not in self.active_proposals:
            self.logger.warning(f"Vote received for unknown proposal {proposal_id}")
            return
            
        proposal = self.active_proposals[proposal_id]
        proposal.votes[agent_id] = vote_data
        
        self.logger.info(f"Vote received from {agent_id} for proposal {proposal_id}: {vote_data.get('vote', 'unknown')}")
        
        # Check if we have enough votes to make a decision
        await self._check_consensus_completion(proposal)
        
    async def _check_consensus_completion(self, proposal: ConsensusProposal):
        """Check if consensus has been reached."""
        votes = proposal.votes
        
        if not votes:
            return
            
        # Count votes by type
        approve_votes = [v for v in votes.values() if v.get('vote') == 'approve']
        reject_votes = [v for v in votes.values() if v.get('vote') == 'reject']
        abstain_votes = [v for v in votes.values() if v.get('vote') == 'abstain']
        
        total_votes = len(approve_votes) + len(reject_votes) + len(abstain_votes)
        
        # Check consensus based on method
        consensus_reached = False
        approved = False
        
        if proposal.consensus_method == ConsensusMethod.UNANIMOUS:
            if total_votes > 0 and len(reject_votes) == 0 and len(approve_votes) > 0:
                consensus_reached = True
                approved = True
            elif len(reject_votes) > 0:
                consensus_reached = True
                approved = False
                
        elif proposal.consensus_method == ConsensusMethod.MAJORITY:
            if total_votes >= 3:  # Minimum quorum
                if len(approve_votes) > len(reject_votes):
                    consensus_reached = True
                    approved = True
                elif len(reject_votes) > len(approve_votes):
                    consensus_reached = True
                    approved = False
                    
        elif proposal.consensus_method == ConsensusMethod.SUPERMAJORITY:
            if total_votes >= 3:
                approval_rate = len(approve_votes) / (len(approve_votes) + len(reject_votes)) if (len(approve_votes) + len(reject_votes)) > 0 else 0
                if approval_rate >= 0.67:  # 2/3 majority
                    consensus_reached = True
                    approved = True
                elif approval_rate < 0.34:  # Less than 1/3
                    consensus_reached = True
                    approved = False
                    
        elif proposal.consensus_method == ConsensusMethod.WEIGHTED:
            # Weight votes by agent confidence scores
            weighted_approve = sum(v.get('confidence', 0.5) for v in approve_votes)
            weighted_reject = sum(v.get('confidence', 0.5) for v in reject_votes)
            
            if weighted_approve + weighted_reject > 0:
                if weighted_approve > weighted_reject:
                    consensus_reached = True
                    approved = True
                else:
                    consensus_reached = True
                    approved = False
                    
        if consensus_reached:
            await self._finalize_consensus(proposal, approved)
            
    async def _finalize_consensus(self, proposal: ConsensusProposal, approved: bool):
        """Finalize a consensus decision."""
        proposal.status = "approved" if approved else "rejected"
        
        self.logger.info(f"Consensus reached for proposal {proposal.proposal_id}: {proposal.status}")
        
        # Notify initiator of result
        result_message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id="consensus_engine",
            receiver_id=proposal.initiator_id,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
            content={
                "proposal_id": proposal.proposal_id,
                "status": proposal.status,
                "votes": proposal.votes,
                "decision_summary": self._generate_decision_summary(proposal)
            },
            timestamp=datetime.now()
        )
        
        await self.communication_hub.send_message(result_message)
        
        # Record metrics
        self.observability.record_metric(
            "counter", "consensus_decisions_total", 1,
            {"proposal_type": proposal.proposal_type, "status": proposal.status, "method": proposal.consensus_method.value}
        )
        
        # Clean up
        del self.active_proposals[proposal.proposal_id]
        
    async def _handle_consensus_timeout(self, proposal_id: str, timeout: timedelta):
        """Handle consensus timeout."""
        await asyncio.sleep(timeout.total_seconds())
        
        if proposal_id in self.active_proposals:
            proposal = self.active_proposals[proposal_id]
            proposal.status = "timeout"
            
            self.logger.warning(f"Consensus proposal {proposal_id} timed out")
            
            # Notify initiator
            timeout_message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id="consensus_engine",
                receiver_id=proposal.initiator_id,
                message_type=MessageType.NOTIFICATION,
                priority=MessagePriority.MEDIUM,
                content={
                    "proposal_id": proposal_id,
                    "status": "timeout",
                    "message": "Consensus proposal timed out",
                    "partial_votes": proposal.votes
                },
                timestamp=datetime.now()
            )
            
            await self.communication_hub.send_message(timeout_message)
            
            # Clean up
            del self.active_proposals[proposal_id]
            
    def _generate_decision_summary(self, proposal: ConsensusProposal) -> Dict[str, Any]:
        """Generate summary of consensus decision."""
        votes = proposal.votes
        
        approve_count = len([v for v in votes.values() if v.get('vote') == 'approve'])
        reject_count = len([v for v in votes.values() if v.get('vote') == 'reject'])
        abstain_count = len([v for v in votes.values() if v.get('vote') == 'abstain'])
        
        # Collect rationales
        rationales = []
        for agent_id, vote_data in votes.items():
            if 'rationale' in vote_data:
                rationales.append({
                    "agent_id": agent_id,
                    "vote": vote_data.get('vote'),
                    "rationale": vote_data['rationale']
                })
                
        return {
            "vote_counts": {
                "approve": approve_count,
                "reject": reject_count,
                "abstain": abstain_count
            },
            "total_participants": len(votes),
            "consensus_method": proposal.consensus_method.value,
            "rationales": rationales,
            "decision_time": (datetime.now() - proposal.created_at).total_seconds()
        }