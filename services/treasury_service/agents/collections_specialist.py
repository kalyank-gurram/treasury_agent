"""Collections Specialist Agent for AR management and optimization."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_agent import (
    BaseAgent, AgentRole, AgentCapability, AgentMessage, AgentDecision,
    MessageType, MessagePriority
)
from ..domain.cash_management import CollectionsOptimizer, CollectionPriority, CollectionAction
from ..infrastructure.observability import get_observability_manager


class CollectionsSpecialistAgent(BaseAgent):
    """Specialized agent for accounts receivable management and collections optimization."""
    
    def __init__(self, agent_id: str = "collections_specialist_001"):
        capabilities = [
            AgentCapability.COLLECTIONS_OPTIMIZATION,
            AgentCapability.CASH_FORECASTING,
            AgentCapability.RISK_ASSESSMENT,
            AgentCapability.REPORTING
        ]
        
        super().__init__(agent_id, AgentRole.COLLECTIONS_SPECIALIST, capabilities)
        
        # Initialize collections optimizer
        self.collections_optimizer = CollectionsOptimizer()
        
        # Collections performance tracking
        self.performance_metrics = {
            "total_collections_managed": 0,
            "successful_collections": 0,
            "average_collection_time": 0.0,
            "collection_rate": 0.0,
            "dispute_resolution_rate": 0.0
        }
        
        # Subscribe to relevant message types
        self.subscribe_to_message_type(MessageType.REQUEST)
        self.subscribe_to_message_type(MessageType.NOTIFICATION)
        self.subscribe_to_message_type(MessageType.CONSENSUS_PROPOSAL)
        
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize collections specialist configuration."""
        return {
            "collection_strategy": "balanced",  # aggressive, balanced, conservative
            "communication_preferences": {
                "email_frequency": "daily",
                "phone_call_threshold": 10000,  # $10K+ gets phone calls
                "formal_notice_threshold": 50000,  # $50K+ gets formal notices
                "legal_action_threshold": 100000  # $100K+ considers legal action
            },
            "customer_relationship_weight": 0.3,  # How much to weight relationships vs. collections
            "discount_negotiation_authority": 0.05,  # Up to 5% settlement discounts
            "payment_plan_authority": 90,  # Up to 90 days payment plans
            "reporting_frequency": "weekly"
        }
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages for collections management."""
        try:
            if message.message_type == MessageType.REQUEST:
                return await self._handle_collections_request(message)
            elif message.message_type == MessageType.NOTIFICATION:
                return await self._handle_collections_notification(message)
            elif message.message_type == MessageType.CONSENSUS_PROPOSAL:
                return await self._handle_consensus_proposal(message)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}",
                            message_id=message.message_id, error_type=type(e).__name__)
            return None
            
    async def _handle_collections_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle collections optimization requests."""
        content = message.content
        capability = content.get("capability")
        parameters = content.get("parameters", {})
        
        result = None
        
        if capability == AgentCapability.COLLECTIONS_OPTIMIZATION.value:
            result = await self._optimize_collections_strategy(parameters)
        elif capability == AgentCapability.CASH_FORECASTING.value:
            result = await self._forecast_collections(parameters)
        elif capability == AgentCapability.RISK_ASSESSMENT.value:
            result = await self._assess_collection_risk(parameters)
        elif capability == AgentCapability.REPORTING.value:
            result = await self._generate_collections_report(parameters)
            
        if result:
            return AgentMessage(
                message_id=f"resp_{message.message_id}",
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                priority=message.priority,
                content={
                    "request_id": content.get("request_id"),
                    "capability": capability,
                    "result": result,
                    "agent_id": self.agent_id,
                    "processing_time": 1.0
                },
                timestamp=datetime.now(),
                correlation_id=message.correlation_id
            )
            
        return None
        
    async def _handle_collections_notification(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle notifications about collection events."""
        notification_type = message.content.get("type")
        
        if notification_type == "payment_received":
            await self._process_payment_received(message.content)
        elif notification_type == "customer_dispute":
            await self._process_customer_dispute(message.content)
        elif notification_type == "collection_deadline":
            return await self._handle_collection_deadline(message.content)
            
        return None
        
    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make collections management decision based on context."""
        decision_type = context.get("decision_type", "collection_strategy")
        
        if decision_type == "collection_action":
            return await self._decide_collection_action(context)
        elif decision_type == "payment_plan":
            return await self._decide_payment_plan(context)
        elif decision_type == "settlement_offer":
            return await self._decide_settlement_offer(context)
        elif decision_type == "legal_action":
            return await self._decide_legal_action(context)
        else:
            return await self._general_collections_decision(context)
            
    async def _optimize_collections_strategy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize collections strategy for given parameters."""
        entity = parameters.get("entity", "ALL")
        focus_area = parameters.get("focus_area", "overall")  # overall, high_value, aging, relationships
        
        self.logger.info(f"Optimizing collections strategy for {entity}, focus: {focus_area}")
        
        # Get collections report
        collections_report = await self.collections_optimizer.optimize_collections(entity)
        
        # Analyze current performance
        current_performance = self._analyze_collections_performance(collections_report)
        
        # Generate optimization strategies
        optimization_strategy = {
            "current_performance": current_performance,
            "priority_actions": self._generate_priority_actions(collections_report, focus_area),
            "resource_allocation": self._optimize_resource_allocation(collections_report),
            "customer_segmentation": self._segment_customers_by_risk(collections_report),
            "automation_opportunities": self._identify_automation_opportunities(collections_report),
            "expected_improvements": self._calculate_expected_improvements(collections_report, focus_area)
        }
        
        return optimization_strategy
        
    async def _forecast_collections(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast collection amounts and timing."""
        entity = parameters.get("entity", "ALL")
        forecast_days = parameters.get("forecast_days", 30)
        confidence_level = parameters.get("confidence_level", 0.8)
        
        # Get collections data
        collections_report = await self.collections_optimizer.optimize_collections(entity)
        
        # Generate forecast
        collections_forecast = {
            "forecast_period_days": forecast_days,
            "confidence_level": confidence_level,
            "total_ar": collections_report.total_ar,
            "expected_collections": {},
            "collection_probability": {},
            "risk_adjusted_forecast": {},
            "weekly_breakdown": {}
        }
        
        # Calculate expected collections by week
        for i in range(0, forecast_days, 7):
            week_start = datetime.now() + timedelta(days=i)
            week_end = week_start + timedelta(days=6)
            week_key = f"week_{i//7 + 1}"
            
            week_collections = self._calculate_weekly_collections(
                collections_report.recommendations, week_start, week_end, confidence_level
            )
            
            collections_forecast["weekly_breakdown"][week_key] = week_collections
            
        # Calculate total expected collections
        collections_forecast["expected_collections"] = {
            "optimistic": sum(week["optimistic"] for week in collections_forecast["weekly_breakdown"].values()),
            "realistic": sum(week["realistic"] for week in collections_forecast["weekly_breakdown"].values()),
            "conservative": sum(week["conservative"] for week in collections_forecast["weekly_breakdown"].values())
        }
        
        return collections_forecast
        
    async def _assess_collection_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess collection risk for specific customers or overall portfolio."""
        entity = parameters.get("entity", "ALL")
        customer_id = parameters.get("customer_id")
        assessment_type = parameters.get("type", "portfolio")
        
        collections_report = await self.collections_optimizer.optimize_collections(entity)
        
        if customer_id:
            # Customer-specific risk assessment
            customer_recommendations = [
                rec for rec in collections_report.recommendations
                if rec.customer_id == customer_id
            ]
            
            if not customer_recommendations:
                return {"error": f"Customer {customer_id} not found"}
                
            risk_assessment = self._assess_customer_risk(customer_recommendations[0])
        else:
            # Portfolio risk assessment
            risk_assessment = self._assess_portfolio_risk(collections_report)
            
        return risk_assessment
        
    def _analyze_collections_performance(self, report) -> Dict[str, Any]:
        """Analyze current collections performance."""
        total_recommendations = len(report.recommendations)
        
        if total_recommendations == 0:
            return {"error": "No collections data available"}
            
        # Calculate performance metrics
        priority_breakdown = {}
        for priority in CollectionPriority:
            count = len([rec for rec in report.recommendations if rec.priority == priority])
            priority_breakdown[priority.value] = {
                "count": count,
                "percentage": (count / total_recommendations) * 100 if total_recommendations > 0 else 0
            }
            
        # Calculate expected recovery
        total_potential_recovery = sum(rec.potential_recovery for rec in report.recommendations)
        
        # Aging analysis
        aging_analysis = {
            "0-30_days": {"count": 0, "amount": 0},
            "31-60_days": {"count": 0, "amount": 0},
            "61-90_days": {"count": 0, "amount": 0},
            "over_90_days": {"count": 0, "amount": 0}
        }
        
        for rec in report.recommendations:
            if rec.days_outstanding <= 30:
                aging_analysis["0-30_days"]["count"] += 1
                aging_analysis["0-30_days"]["amount"] += rec.invoice_amount
            elif rec.days_outstanding <= 60:
                aging_analysis["31-60_days"]["count"] += 1
                aging_analysis["31-60_days"]["amount"] += rec.invoice_amount
            elif rec.days_outstanding <= 90:
                aging_analysis["61-90_days"]["count"] += 1
                aging_analysis["61-90_days"]["amount"] += rec.invoice_amount
            else:
                aging_analysis["over_90_days"]["count"] += 1
                aging_analysis["over_90_days"]["amount"] += rec.invoice_amount
                
        return {
            "total_ar": report.total_ar,
            "total_items": total_recommendations,
            "priority_breakdown": priority_breakdown,
            "expected_recovery_rate": (total_potential_recovery / report.total_ar) * 100 if report.total_ar > 0 else 0,
            "aging_analysis": aging_analysis,
            "average_days_outstanding": sum(rec.days_outstanding for rec in report.recommendations) / total_recommendations if total_recommendations > 0 else 0
        }
        
    def _generate_priority_actions(self, report, focus_area: str) -> List[Dict[str, Any]]:
        """Generate priority actions based on collections analysis."""
        actions = []
        
        # Get high-priority recommendations
        high_priority_recs = [
            rec for rec in report.recommendations
            if rec.priority in [CollectionPriority.CRITICAL, CollectionPriority.HIGH]
        ]
        
        if focus_area == "high_value":
            # Focus on high-value items
            high_value_recs = sorted(
                [rec for rec in high_priority_recs if rec.invoice_amount > 25000],
                key=lambda x: x.invoice_amount, reverse=True
            )[:10]
            
            for rec in high_value_recs:
                actions.append({
                    "type": "immediate_action",
                    "priority": "critical",
                    "customer": rec.customer_name,
                    "amount": rec.invoice_amount,
                    "action": rec.recommended_action.value,
                    "expected_date": rec.expected_collection_date.isoformat(),
                    "rationale": f"High-value invoice ${rec.invoice_amount:,.0f} requires immediate attention"
                })
                
        elif focus_area == "aging":
            # Focus on aging items
            aging_recs = sorted(
                high_priority_recs,
                key=lambda x: x.days_outstanding, reverse=True
            )[:15]
            
            for rec in aging_recs:
                actions.append({
                    "type": "aging_management",
                    "priority": "high",
                    "customer": rec.customer_name,
                    "days_outstanding": rec.days_outstanding,
                    "amount": rec.invoice_amount,
                    "action": rec.recommended_action.value,
                    "rationale": f"Invoice aged {rec.days_outstanding} days requires escalation"
                })
                
        elif focus_area == "relationships":
            # Focus on relationship management
            relationship_recs = [
                rec for rec in report.recommendations
                if rec.priority == CollectionPriority.CRITICAL and
                rec.recommended_action in [CollectionAction.PAYMENT_PLAN, CollectionAction.IMMEDIATE_CALL]
            ]
            
            for rec in relationship_recs:
                actions.append({
                    "type": "relationship_management",
                    "priority": "medium",
                    "customer": rec.customer_name,
                    "amount": rec.invoice_amount,
                    "action": "relationship_call",
                    "rationale": "Balance collection needs with relationship preservation"
                })
                
        else:  # overall
            # Balanced approach
            top_actions = sorted(
                high_priority_recs,
                key=lambda x: (x.priority.value, -x.invoice_amount)
            )[:20]
            
            for rec in top_actions:
                actions.append({
                    "type": "balanced_action",
                    "priority": rec.priority.value,
                    "customer": rec.customer_name,
                    "amount": rec.invoice_amount,
                    "days_outstanding": rec.days_outstanding,
                    "action": rec.recommended_action.value,
                    "probability": rec.collection_probability,
                    "expected_date": rec.expected_collection_date.isoformat()
                })
                
        return actions
        
    def _calculate_weekly_collections(self, recommendations, week_start: datetime,
                                    week_end: datetime, confidence_level: float) -> Dict[str, float]:
        """Calculate expected collections for a specific week."""
        week_recs = [
            rec for rec in recommendations
            if week_start <= rec.expected_collection_date <= week_end
        ]
        
        if not week_recs:
            return {"optimistic": 0, "realistic": 0, "conservative": 0}
            
        # Calculate scenarios
        optimistic = sum(rec.potential_recovery * 1.1 for rec in week_recs)  # 10% upside
        realistic = sum(rec.potential_recovery for rec in week_recs)
        conservative = sum(rec.potential_recovery * 0.8 for rec in week_recs)  # 20% haircut
        
        return {
            "optimistic": optimistic,
            "realistic": realistic,
            "conservative": conservative,
            "item_count": len(week_recs),
            "average_probability": sum(rec.collection_probability for rec in week_recs) / len(week_recs)
        }
        
    async def _decide_collection_action(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on collection action for a specific customer/invoice."""
        customer_data = context.get("customer_data", {})
        invoice_data = context.get("invoice_data", {})
        
        customer_name = customer_data.get("name", "Unknown")
        invoice_amount = invoice_data.get("amount", 0)
        days_outstanding = invoice_data.get("days_outstanding", 0)
        payment_history = customer_data.get("payment_history_score", 70)
        relationship_value = customer_data.get("relationship_score", 0.5)
        
        # Decision logic
        if days_outstanding > 120 and invoice_amount > 50000:
            if payment_history < 40:
                recommendation = f"ESCALATE: Initiate legal proceedings for {customer_name}"
                confidence = 0.85
            else:
                recommendation = f"NEGOTIATE: Offer structured payment plan to {customer_name}"
                confidence = 0.75
        elif days_outstanding > 90:
            if relationship_value > 0.8:
                recommendation = f"RELATIONSHIP: Executive call to {customer_name} to preserve partnership"
                confidence = 0.80
            else:
                recommendation = f"FORMAL: Send formal demand notice to {customer_name}"
                confidence = 0.85
        elif days_outstanding > 60:
            recommendation = f"ACCELERATE: Daily follow-up calls to {customer_name}"
            confidence = 0.80
        else:
            recommendation = f"STANDARD: Email reminder series to {customer_name}"
            confidence = 0.75
            
        decision = AgentDecision(
            decision_id=f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=self.agent_id,
            decision_type="collection_action",
            recommendation=recommendation,
            confidence_score=confidence,
            supporting_data={
                "customer": customer_name,
                "amount": invoice_amount,
                "days_outstanding": days_outstanding,
                "payment_history": payment_history,
                "relationship_value": relationship_value,
                "strategy": self.config["collection_strategy"]
            }
        )
        
        self.record_decision(decision, success=True)
        return decision
        
    async def _analyze_consensus_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus proposal from collections perspective."""
        proposal_content = proposal.get("content", {})
        proposal_type = proposal.get("proposal_type", "")
        
        if "collection" in proposal_type.lower():
            return await self._analyze_collection_policy_proposal(proposal_content)
        elif "customer" in proposal_type.lower():
            return await self._analyze_customer_proposal(proposal_content)
        elif "payment" in proposal_type.lower():
            return await self._analyze_payment_terms_proposal(proposal_content)
        else:
            return await self._analyze_general_proposal(proposal_content)
            
    async def _analyze_collection_policy_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze collection policy changes."""
        policy_changes = proposal.get("policy_changes", {})
        
        # Assess impact on collections
        collection_cycle_impact = policy_changes.get("collection_cycle_days")
        escalation_threshold = policy_changes.get("escalation_threshold")
        
        if collection_cycle_impact and collection_cycle_impact > 45:
            vote = "reject"
            rationale = "Extended collection cycle will negatively impact cash flow"
            confidence = 0.85
        elif escalation_threshold and escalation_threshold > 150000:
            vote = "abstain"
            rationale = "High escalation threshold may delay critical collection actions"
            confidence = 0.7
        else:
            vote = "approve"
            rationale = "Policy changes align with effective collection practices"
            confidence = 0.8
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale,
            "collections_impact": "negative" if collection_cycle_impact and collection_cycle_impact > 45 else "neutral"
        }
        
    async def _analyze_general_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze general proposal for collections impact."""
        cash_flow_impact = proposal.get("cash_flow_impact", 0)
        
        if cash_flow_impact < -2000000:  # Negative $2M+ impact
            vote = "reject"
            rationale = "Negative cash flow impact will strain collections resources"
            confidence = 0.8
        elif cash_flow_impact > 1000000:  # Positive $1M+ impact
            vote = "approve"
            rationale = "Positive cash flow impact supports collections objectives"
            confidence = 0.75
        else:
            vote = "abstain"
            rationale = "Minimal collections impact, defer to other specialists"
            confidence = 0.6
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale
        }