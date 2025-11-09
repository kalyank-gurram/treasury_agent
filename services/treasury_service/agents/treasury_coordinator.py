"""Treasury Coordinator Agent for orchestrating multi-agent workflows."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from .base_agent import (
    BaseAgent, AgentRole, AgentCapability, AgentMessage, AgentDecision,
    MessageType, MessagePriority
)
from .communication_hub import CommunicationHub, ConsensusEngine, ConsensusMethod
from .infrastructure.observability import get_observability_manager


class WorkflowType:
    """Types of treasury workflows."""
    DAILY_CASH_MANAGEMENT = "daily_cash_management"
    PAYMENT_OPTIMIZATION = "payment_optimization"
    INVESTMENT_PLANNING = "investment_planning"
    RISK_ASSESSMENT = "risk_assessment"
    COLLECTIONS_CAMPAIGN = "collections_campaign"
    COMPLIANCE_REVIEW = "compliance_review"
    CRISIS_RESPONSE = "crisis_response"


class WorkflowStatus:
    """Workflow execution statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TreasuryCoordinatorAgent(BaseAgent):
    """Coordinator agent for orchestrating complex treasury workflows."""
    
    def __init__(self, agent_id: str = "treasury_coordinator_001"):
        capabilities = [
            AgentCapability.CASH_FORECASTING,
            AgentCapability.SCENARIO_ANALYSIS,
            AgentCapability.REPORTING,
            AgentCapability.LIQUIDITY_MANAGEMENT
        ]
        
        super().__init__(agent_id, AgentRole.TREASURY_COORDINATOR, capabilities)
        
        # Workflow management
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Coordination state
        self.agent_availability: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.coordination_metrics = {
            "workflows_completed": 0,
            "average_execution_time": timedelta(seconds=0),
            "success_rate": 0.0,
            "agent_utilization": {}
        }
        
        # Subscribe to all message types for coordination
        for msg_type in MessageType:
            self.subscribe_to_message_type(msg_type)
            
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize treasury coordinator configuration."""
        return {
            "coordination_style": "collaborative",  # directive, collaborative, consultative
            "decision_authority": "consensus_preferred",  # autonomous, consensus_preferred, consensus_required
            "escalation_threshold": timedelta(hours=4),
            "workflow_timeout": timedelta(hours=24),
            "parallel_workflow_limit": 5,
            "agent_health_check_frequency": timedelta(minutes=15),
            "performance_monitoring": True
        }
        
    def _initialize_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined workflow templates."""
        return {
            WorkflowType.DAILY_CASH_MANAGEMENT: {
                "name": "Daily Cash Management",
                "description": "Comprehensive daily cash position management",
                "steps": [
                    {"step": "cash_position_analysis", "agent_capability": AgentCapability.CASH_FORECASTING},
                    {"step": "risk_assessment", "agent_capability": AgentCapability.RISK_ASSESSMENT},
                    {"step": "liquidity_optimization", "agent_capability": AgentCapability.LIQUIDITY_MANAGEMENT},
                    {"step": "compliance_check", "agent_capability": AgentCapability.COMPLIANCE_CHECK},
                    {"step": "reporting", "agent_capability": AgentCapability.REPORTING}
                ],
                "parallel_steps": ["cash_position_analysis", "risk_assessment"],
                "estimated_duration": timedelta(hours=2),
                "priority": MessagePriority.HIGH
            },
            
            WorkflowType.PAYMENT_OPTIMIZATION: {
                "name": "Payment Optimization",
                "description": "Optimize payment scheduling and cash flow",
                "steps": [
                    {"step": "payment_analysis", "agent_capability": AgentCapability.PAYMENT_PRIORITIZATION},
                    {"step": "liquidity_impact", "agent_capability": AgentCapability.LIQUIDITY_MANAGEMENT},
                    {"step": "risk_assessment", "agent_capability": AgentCapability.RISK_ASSESSMENT},
                    {"step": "compliance_approval", "agent_capability": AgentCapability.COMPLIANCE_CHECK},
                    {"step": "execution_planning", "agent_capability": AgentCapability.CASH_FORECASTING}
                ],
                "parallel_steps": ["payment_analysis", "liquidity_impact"],
                "estimated_duration": timedelta(hours=1.5),
                "priority": MessagePriority.MEDIUM
            },
            
            WorkflowType.INVESTMENT_PLANNING: {
                "name": "Investment Planning",
                "description": "Strategic investment allocation and optimization",
                "steps": [
                    {"step": "cash_forecast", "agent_capability": AgentCapability.CASH_FORECASTING},
                    {"step": "investment_analysis", "agent_capability": AgentCapability.INVESTMENT_ANALYSIS},
                    {"step": "risk_assessment", "agent_capability": AgentCapability.RISK_ASSESSMENT},
                    {"step": "compliance_review", "agent_capability": AgentCapability.COMPLIANCE_CHECK},
                    {"step": "consensus_decision", "requires_consensus": True}
                ],
                "parallel_steps": ["investment_analysis", "risk_assessment"],
                "estimated_duration": timedelta(hours=3),
                "priority": MessagePriority.MEDIUM
            },
            
            WorkflowType.COLLECTIONS_CAMPAIGN: {
                "name": "Collections Campaign",
                "description": "Optimize collections strategy and execution",
                "steps": [
                    {"step": "collections_analysis", "agent_capability": AgentCapability.COLLECTIONS_OPTIMIZATION},
                    {"step": "risk_profiling", "agent_capability": AgentCapability.RISK_ASSESSMENT},
                    {"step": "cash_impact_forecast", "agent_capability": AgentCapability.CASH_FORECASTING},
                    {"step": "compliance_review", "agent_capability": AgentCapability.COMPLIANCE_CHECK},
                    {"step": "execution_coordination", "agent_capability": AgentCapability.COLLECTIONS_OPTIMIZATION}
                ],
                "parallel_steps": [],
                "estimated_duration": timedelta(hours=2),
                "priority": MessagePriority.MEDIUM
            },
            
            WorkflowType.CRISIS_RESPONSE: {
                "name": "Crisis Response",
                "description": "Emergency treasury crisis management",
                "steps": [
                    {"step": "situation_assessment", "agent_capability": AgentCapability.RISK_ASSESSMENT},
                    {"step": "liquidity_analysis", "agent_capability": AgentCapability.LIQUIDITY_MANAGEMENT},
                    {"step": "scenario_planning", "agent_capability": AgentCapability.SCENARIO_ANALYSIS},
                    {"step": "emergency_consensus", "requires_consensus": True, "consensus_method": ConsensusMethod.SUPERMAJORITY},
                    {"step": "crisis_execution", "agent_capability": AgentCapability.LIQUIDITY_MANAGEMENT}
                ],
                "parallel_steps": ["situation_assessment", "liquidity_analysis"],
                "estimated_duration": timedelta(hours=1),
                "priority": MessagePriority.CRITICAL
            }
        }
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages for workflow coordination."""
        try:
            if message.message_type == MessageType.REQUEST:
                return await self._handle_coordination_request(message)
            elif message.message_type == MessageType.RESPONSE:
                return await self._handle_workflow_response(message)
            elif message.message_type == MessageType.NOTIFICATION:
                return await self._handle_workflow_notification(message)
            elif message.message_type == MessageType.STATUS_UPDATE:
                return await self._handle_agent_status_update(message)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing coordination message: {e}",
                            message_id=message.message_id, error_type=type(e).__name__)
            return None
            
    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make coordination decision based on context."""
        decision_type = context.get("decision_type", "workflow_coordination")
        
        if decision_type == "workflow_initiation":
            return await self._decide_workflow_initiation(context)
        elif decision_type == "agent_selection":
            return await self._decide_agent_selection(context)
        elif decision_type == "workflow_prioritization":
            return await self._decide_workflow_prioritization(context)
        elif decision_type == "escalation_handling":
            return await self._decide_escalation_handling(context)
        else:
            return await self._general_coordination_decision(context)
            
    async def initiate_workflow(self, workflow_type: str, parameters: Dict[str, Any],
                              initiator: str = "system") -> str:
        """Initiate a new treasury workflow."""
        workflow_id = f"{workflow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if workflow_type not in self.workflow_templates:
            self.logger.error(f"Unknown workflow type: {workflow_type}")
            return None
            
        template = self.workflow_templates[workflow_type]
        
        workflow = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "template": template,
            "parameters": parameters,
            "initiator": initiator,
            "status": WorkflowStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "current_step": 0,
            "completed_steps": [],
            "step_results": {},
            "assigned_agents": {},
            "consensus_proposals": {},
            "estimated_completion": datetime.now() + template["estimated_duration"]
        }
        
        self.active_workflows[workflow_id] = workflow
        
        self.logger.info(f"Initiated workflow {workflow_id} of type {workflow_type}")
        
        # Start workflow execution
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        return workflow_id
        
    async def _execute_workflow(self, workflow_id: str):
        """Execute a workflow step by step."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
            
        workflow["status"] = WorkflowStatus.IN_PROGRESS
        workflow["updated_at"] = datetime.now()
        
        try:
            steps = workflow["template"]["steps"]
            parallel_steps = workflow["template"].get("parallel_steps", [])
            
            for i, step in enumerate(steps):
                workflow["current_step"] = i
                
                # Check if this step can run in parallel with others
                if step["step"] in parallel_steps:
                    # Find all parallel steps and execute them together
                    parallel_step_group = [s for s in steps if s["step"] in parallel_steps]
                    if i == 0 or steps[i-1]["step"] not in parallel_steps:
                        # This is the start of a parallel group
                        await self._execute_parallel_steps(workflow_id, parallel_step_group)
                        # Skip the individual execution of parallel steps
                        continue
                    elif steps[i-1]["step"] in parallel_steps:
                        # This step was already executed in parallel
                        continue
                        
                # Execute single step
                success = await self._execute_workflow_step(workflow_id, step)
                
                if not success:
                    workflow["status"] = WorkflowStatus.FAILED
                    self.logger.error(f"Workflow {workflow_id} failed at step {step['step']}")
                    return
                    
                workflow["completed_steps"].append(step["step"])
                
            # Workflow completed successfully
            workflow["status"] = WorkflowStatus.COMPLETED
            workflow["completed_at"] = datetime.now()
            
            # Update metrics
            self._update_workflow_metrics(workflow)
            
            self.logger.info(f"Workflow {workflow_id} completed successfully")
            
        except Exception as e:
            workflow["status"] = WorkflowStatus.FAILED
            workflow["error"] = str(e)
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
            
        finally:
            workflow["updated_at"] = datetime.now()
            
    async def _execute_parallel_steps(self, workflow_id: str, parallel_steps: List[Dict[str, Any]]):
        """Execute multiple steps in parallel."""
        workflow = self.active_workflows[workflow_id]
        
        # Create tasks for all parallel steps
        tasks = []
        for step in parallel_steps:
            task = asyncio.create_task(self._execute_workflow_step(workflow_id, step))
            tasks.append((step["step"], task))
            
        # Wait for all parallel steps to complete
        results = {}
        for step_name, task in tasks:
            try:
                success = await task
                results[step_name] = success
                if success:
                    workflow["completed_steps"].append(step_name)
            except Exception as e:
                self.logger.error(f"Parallel step {step_name} failed: {e}")
                results[step_name] = False
                
        # Check if any parallel step failed
        if not all(results.values()):
            failed_steps = [step for step, success in results.items() if not success]
            raise Exception(f"Parallel steps failed: {', '.join(failed_steps)}")
            
    async def _execute_workflow_step(self, workflow_id: str, step: Dict[str, Any]) -> bool:
        """Execute a single workflow step."""
        workflow = self.active_workflows[workflow_id]
        step_name = step["step"]
        
        self.logger.info(f"Executing workflow step: {step_name} for workflow {workflow_id}")
        
        try:
            if step.get("requires_consensus", False):
                # Handle consensus step
                return await self._handle_consensus_step(workflow_id, step)
            else:
                # Handle capability-based step
                return await self._handle_capability_step(workflow_id, step)
                
        except Exception as e:
            self.logger.error(f"Step {step_name} execution failed: {e}")
            return False
            
    async def _handle_capability_step(self, workflow_id: str, step: Dict[str, Any]) -> bool:
        """Handle a step that requires a specific agent capability."""
        capability = step["agent_capability"]
        workflow = self.active_workflows[workflow_id]
        
        # Request the capability from the communication hub
        if hasattr(self, 'communication_hub'):
            result = await self.communication_hub.request_capability(
                self.agent_id, capability, workflow["parameters"]
            )
            
            if result:
                workflow["step_results"][step["step"]] = result
                return True
            else:
                self.logger.warning(f"No agent available for capability {capability.value}")
                return False
        else:
            # Simulate successful execution for demo
            workflow["step_results"][step["step"]] = {
                "status": "completed",
                "result": f"Simulated result for {step['step']}",
                "timestamp": datetime.now().isoformat()
            }
            return True
            
    async def _handle_consensus_step(self, workflow_id: str, step: Dict[str, Any]) -> bool:
        """Handle a step that requires consensus decision-making."""
        workflow = self.active_workflows[workflow_id]
        
        # Prepare consensus proposal
        consensus_method = step.get("consensus_method", ConsensusMethod.MAJORITY)
        required_capabilities = step.get("required_capabilities", [
            AgentCapability.RISK_ASSESSMENT,
            AgentCapability.INVESTMENT_ANALYSIS,
            AgentCapability.COMPLIANCE_CHECK
        ])
        
        proposal_content = {
            "workflow_id": workflow_id,
            "step_name": step["step"],
            "workflow_parameters": workflow["parameters"],
            "previous_results": workflow["step_results"]
        }
        
        if hasattr(self, 'consensus_engine'):
            proposal_id = await self.consensus_engine.initiate_consensus(
                initiator_id=self.agent_id,
                proposal_type=f"workflow_{step['step']}",
                content=proposal_content,
                required_capabilities=required_capabilities,
                consensus_method=consensus_method,
                timeout=timedelta(minutes=30)
            )
            
            workflow["consensus_proposals"][step["step"]] = proposal_id
            
            # Wait for consensus result (simplified - in production would be event-driven)
            await asyncio.sleep(5)  # Simulate consensus time
            
            workflow["step_results"][step["step"]] = {
                "consensus_proposal_id": proposal_id,
                "result": "consensus_reached",
                "timestamp": datetime.now().isoformat()
            }
            
            return True
        else:
            # Simulate consensus for demo
            workflow["step_results"][step["step"]] = {
                "result": "simulated_consensus",
                "timestamp": datetime.now().isoformat()
            }
            return True
            
    async def _decide_workflow_initiation(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide whether to initiate a new workflow."""
        trigger_event = context.get("trigger_event")
        priority_level = context.get("priority_level", "medium")
        available_resources = context.get("available_resources", {})
        
        # Check current workload
        active_count = len([w for w in self.active_workflows.values() if w["status"] == WorkflowStatus.IN_PROGRESS])
        max_parallel = self.config["parallel_workflow_limit"]
        
        if active_count >= max_parallel and priority_level != "critical":
            recommendation = f"DEFER: Maximum parallel workflows ({max_parallel}) reached, defer non-critical workflows"
            confidence = 0.85
            initiate = False
        elif trigger_event == "liquidity_crisis":
            recommendation = "IMMEDIATE: Initiate crisis response workflow immediately"
            confidence = 0.95
            initiate = True
        elif trigger_event == "daily_schedule":
            recommendation = "SCHEDULE: Initiate daily cash management workflow"
            confidence = 0.90
            initiate = True
        else:
            recommendation = f"EVALUATE: Assess workflow necessity for {trigger_event}"
            confidence = 0.70
            initiate = True
            
        decision = AgentDecision(
            decision_id=f"workflow_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=self.agent_id,
            decision_type="workflow_initiation",
            recommendation=recommendation,
            confidence_score=confidence,
            supporting_data={
                "trigger_event": trigger_event,
                "priority_level": priority_level,
                "active_workflows": active_count,
                "max_parallel": max_parallel,
                "initiate_workflow": initiate
            }
        )
        
        self.record_decision(decision, success=True)
        return decision
        
    def _update_workflow_metrics(self, workflow: Dict[str, Any]):
        """Update workflow performance metrics."""
        self.coordination_metrics["workflows_completed"] += 1
        
        if "completed_at" in workflow:
            execution_time = workflow["completed_at"] - workflow["created_at"]
            
            # Update average execution time using exponential moving average
            alpha = 0.1
            current_avg = self.coordination_metrics["average_execution_time"]
            if current_avg.total_seconds() == 0:
                self.coordination_metrics["average_execution_time"] = execution_time
            else:
                new_avg_seconds = (1 - alpha) * current_avg.total_seconds() + alpha * execution_time.total_seconds()
                self.coordination_metrics["average_execution_time"] = timedelta(seconds=new_avg_seconds)
                
        # Update success rate
        successful_workflows = len([w for w in self.workflow_history if w.get("status") == WorkflowStatus.COMPLETED])
        total_workflows = len(self.workflow_history) + 1
        self.coordination_metrics["success_rate"] = successful_workflows / total_workflows
        
        # Move completed workflow to history
        self.workflow_history.append(workflow.copy())
        
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            # Check history
            for hist_workflow in self.workflow_history:
                if hist_workflow["workflow_id"] == workflow_id:
                    return hist_workflow
            return None
            
        return {
            "workflow_id": workflow["workflow_id"],
            "workflow_type": workflow["workflow_type"],
            "status": workflow["status"],
            "current_step": workflow["current_step"],
            "completed_steps": workflow["completed_steps"],
            "progress_percentage": len(workflow["completed_steps"]) / len(workflow["template"]["steps"]) * 100,
            "estimated_completion": workflow["estimated_completion"],
            "created_at": workflow["created_at"],
            "updated_at": workflow["updated_at"]
        }
        
    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination performance metrics."""
        return {
            "active_workflows": len(self.active_workflows),
            "completed_workflows": self.coordination_metrics["workflows_completed"],
            "average_execution_time_minutes": self.coordination_metrics["average_execution_time"].total_seconds() / 60,
            "success_rate_percentage": self.coordination_metrics["success_rate"] * 100,
            "workflow_types_distribution": self._calculate_workflow_distribution(),
            "agent_utilization": self.coordination_metrics["agent_utilization"]
        }
        
    def _calculate_workflow_distribution(self) -> Dict[str, int]:
        """Calculate distribution of workflow types."""
        distribution = {}
        all_workflows = list(self.active_workflows.values()) + self.workflow_history
        
        for workflow in all_workflows:
            workflow_type = workflow["workflow_type"]
            distribution[workflow_type] = distribution.get(workflow_type, 0) + 1
            
        return distribution
        
    async def _analyze_consensus_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a consensus proposal from the coordinator perspective."""
        proposal_type = proposal.get("proposal_type", "unknown")
        proposal_content = proposal.get("content", {})
        
        # Coordinator analysis focuses on workflow impact and resource allocation
        analysis = {
            "analysis_type": "coordination_impact",
            "analyst": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "proposal_assessment": {}
        }
        
        if proposal_type.startswith("workflow_"):
            # Workflow-related proposals
            workflow_id = proposal_content.get("workflow_id")
            current_workload = len(self.active_workflows)
            
            analysis["proposal_assessment"] = {
                "impact_on_coordination": "medium" if current_workload < 3 else "high",
                "resource_availability": "available" if current_workload < 5 else "constrained",
                "workflow_priority": proposal_content.get("priority", "medium"),
                "estimated_coordination_effort": "low",
                "recommendation": "approve" if current_workload < 5 else "defer"
            }
            
        elif proposal_type == "investment_approval":
            # Investment-related proposals require coordination assessment
            investment_amount = proposal_content.get("investment_amount", 0)
            
            analysis["proposal_assessment"] = {
                "coordination_complexity": "high" if investment_amount > 5000000 else "medium",
                "multi_agent_required": True,
                "consensus_importance": "critical" if investment_amount > 10000000 else "high",
                "coordination_timeline": "extended" if investment_amount > 5000000 else "standard",
                "recommendation": "approve_with_oversight" if investment_amount > 1000000 else "approve"
            }
            
        elif proposal_type == "crisis_response":
            # Crisis response requires immediate coordination
            severity = proposal_content.get("severity", "medium")
            
            analysis["proposal_assessment"] = {
                "coordination_urgency": "critical" if severity == "high" else "high",
                "resource_priority": "maximum",
                "consensus_method_recommendation": "supermajority" if severity == "high" else "majority",
                "escalation_required": severity == "critical",
                "recommendation": "immediate_approval"
            }
            
        else:
            # General proposal analysis
            analysis["proposal_assessment"] = {
                "coordination_impact": "low",
                "resource_requirement": "minimal",
                "consensus_complexity": "standard",
                "recommendation": "approve"
            }
        
        # Add coordinator-specific considerations
        analysis["coordinator_considerations"] = {
            "current_workflow_load": len(self.active_workflows),
            "agent_availability": len(getattr(self, 'communication_hub', {}).get_available_agents() or []),
            "system_performance": self.coordination_metrics.get("success_rate", 0.0),
            "coordination_confidence": 0.85
        }
        
        return analysis