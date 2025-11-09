"""Risk Manager Agent for treasury risk assessment and management."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_agent import (
    BaseAgent, AgentRole, AgentCapability, AgentMessage, AgentDecision, 
    MessageType, MessagePriority
)
from ..detectors.anomaly import TreasuryAnomalyDetector
from ..kpis.working_capital import TreasuryKPICalculator
from ..infrastructure.observability import get_observability_manager


class RiskManagerAgent(BaseAgent):
    """Specialized agent for treasury risk management and assessment."""
    
    def __init__(self, agent_id: str = "risk_manager_001"):
        capabilities = [
            AgentCapability.RISK_ASSESSMENT,
            AgentCapability.LIQUIDITY_MANAGEMENT,
            AgentCapability.SCENARIO_ANALYSIS,
            AgentCapability.COMPLIANCE_CHECK
        ]
        
        super().__init__(agent_id, AgentRole.RISK_MANAGER, capabilities)
        
        # Initialize risk assessment tools
        self.anomaly_detector = TreasuryAnomalyDetector()
        self.kpi_calculator = TreasuryKPICalculator()
        
        # Risk thresholds and parameters
        self.risk_thresholds = {
            "liquidity_critical": 0.05,  # 5% of total assets
            "concentration_limit": 0.25,  # 25% max counterparty exposure
            "volatility_threshold": 0.15,  # 15% daily volatility alert
            "anomaly_score_critical": 0.8,  # 80% anomaly confidence threshold
            "credit_limit_utilization": 0.85  # 85% credit utilization warning
        }
        
        # Subscribe to relevant message types
        self.subscribe_to_message_type(MessageType.ALERT)
        self.subscribe_to_message_type(MessageType.REQUEST)
        self.subscribe_to_message_type(MessageType.CONSENSUS_PROPOSAL)
        
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize risk manager specific configuration."""
        return {
            "risk_appetite": "moderate",  # conservative, moderate, aggressive
            "monitoring_frequency": timedelta(minutes=15),
            "alert_escalation_time": timedelta(hours=2),
            "risk_reporting_schedule": "daily",
            "stress_test_scenarios": [
                "liquidity_crisis", "market_volatility", "counterparty_default",
                "operational_disruption", "regulatory_change"
            ]
        }
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages for risk assessment."""
        try:
            if message.message_type == MessageType.REQUEST:
                return await self._handle_risk_request(message)
            elif message.message_type == MessageType.ALERT:
                return await self._handle_risk_alert(message)
            elif message.message_type == MessageType.CONSENSUS_PROPOSAL:
                return await self._handle_consensus_proposal(message)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", 
                            message_id=message.message_id, error_type=type(e).__name__)
            return None
            
    async def _handle_risk_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle risk assessment requests."""
        content = message.content
        capability = content.get("capability")
        parameters = content.get("parameters", {})
        
        result = None
        
        if capability == AgentCapability.RISK_ASSESSMENT.value:
            result = await self._perform_risk_assessment(parameters)
        elif capability == AgentCapability.LIQUIDITY_MANAGEMENT.value:
            result = await self._assess_liquidity_risk(parameters)
        elif capability == AgentCapability.SCENARIO_ANALYSIS.value:
            result = await self._perform_scenario_analysis(parameters)
        elif capability == AgentCapability.COMPLIANCE_CHECK.value:
            result = await self._check_compliance_risk(parameters)
            
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
                    "processing_time": 1.0  # Would track actual time
                },
                timestamp=datetime.now(),
                correlation_id=message.correlation_id
            )
            
        return None
        
    async def _handle_risk_alert(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle incoming risk alerts and assess severity."""
        alert_data = message.content
        
        # Assess alert severity and recommend actions
        risk_assessment = await self._assess_alert_risk(alert_data)
        
        if risk_assessment["severity"] in ["critical", "high"]:
            # Escalate critical risks
            return await self._create_escalation_message(message, risk_assessment)
            
        return None
        
    async def _handle_consensus_proposal(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle consensus proposals from risk management perspective."""
        proposal = message.content
        
        # Analyze proposal for risk implications
        risk_analysis = await self._analyze_consensus_proposal(proposal)
        
        return AgentMessage(
            message_id=f"vote_{message.message_id}",
            sender_id=self.agent_id,
            receiver_id="consensus_engine",
            message_type=MessageType.CONSENSUS_VOTE,
            priority=MessagePriority.HIGH,
            content=risk_analysis,
            timestamp=datetime.now(),
            correlation_id=message.correlation_id
        )
        
    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make risk management decision based on context."""
        decision_type = context.get("decision_type", "risk_assessment")
        
        if decision_type == "liquidity_action":
            return await self._decide_liquidity_action(context)
        elif decision_type == "credit_approval":
            return await self._decide_credit_approval(context)
        elif decision_type == "investment_risk":
            return await self._decide_investment_risk(context)
        else:
            return await self._general_risk_decision(context)
            
    async def _perform_risk_assessment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment."""
        entity = parameters.get("entity", "ALL")
        assessment_type = parameters.get("type", "comprehensive")
        
        self.logger.info(f"Performing {assessment_type} risk assessment for {entity}")
        
        # Get current data
        from ..tools.mock_bank_api import MockBankAPI
        api = MockBankAPI()
        
        balances = api.get_account_balances(entity)
        transactions = api.get_recent_transactions(entity, days=30)
        
        # Perform anomaly detection
        anomalies = self.anomaly_detector.detect_anomalies(transactions, entity)
        
        # Calculate risk KPIs
        kpis = self.kpi_calculator.calculate_kpis(transactions, entity)
        
        # Assess various risk factors
        risk_assessment = {
            "overall_risk_score": 0.0,
            "liquidity_risk": self._assess_liquidity_risk_score(balances, kpis),
            "operational_risk": self._assess_operational_risk_score(anomalies),
            "credit_risk": self._assess_credit_risk_score(transactions, kpis),
            "market_risk": self._assess_market_risk_score(transactions),
            "concentration_risk": self._assess_concentration_risk_score(transactions),
            "anomalies_detected": len(anomalies["anomalies"]),
            "risk_factors": [],
            "recommendations": []
        }
        
        # Calculate overall risk score (weighted average)
        weights = {"liquidity": 0.3, "operational": 0.25, "credit": 0.2, "market": 0.15, "concentration": 0.1}
        overall_score = (
            risk_assessment["liquidity_risk"] * weights["liquidity"] +
            risk_assessment["operational_risk"] * weights["operational"] +
            risk_assessment["credit_risk"] * weights["credit"] +
            risk_assessment["market_risk"] * weights["market"] +
            risk_assessment["concentration_risk"] * weights["concentration"]
        )
        
        risk_assessment["overall_risk_score"] = overall_score
        
        # Generate risk factors and recommendations
        risk_assessment["risk_factors"] = self._identify_risk_factors(risk_assessment, kpis)
        risk_assessment["recommendations"] = self._generate_risk_recommendations(risk_assessment)
        
        return risk_assessment
        
    async def _assess_liquidity_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess liquidity risk specifically."""
        entity = parameters.get("entity", "ALL")
        forecast_days = parameters.get("forecast_days", 7)
        
        from ..domain.cash_management import IntraDayForecaster
        forecaster = IntraDayForecaster()
        
        # Generate intraday forecast
        forecast = await forecaster.generate_intraday_forecast(entity, "primary_account")
        
        # Assess liquidity adequacy
        liquidity_assessment = {
            "current_liquidity": forecast.starting_balance,
            "minimum_projected": forecast.trough_balance,
            "liquidity_buffer": forecast.trough_balance - self.risk_thresholds["liquidity_critical"] * forecast.starting_balance,
            "days_of_coverage": self._calculate_liquidity_coverage(forecast),
            "stress_test_results": await self._perform_liquidity_stress_test(forecast),
            "risk_level": "low"
        }
        
        # Determine risk level
        if liquidity_assessment["liquidity_buffer"] < 0:
            liquidity_assessment["risk_level"] = "critical"
        elif liquidity_assessment["days_of_coverage"] < 3:
            liquidity_assessment["risk_level"] = "high"
        elif liquidity_assessment["days_of_coverage"] < 7:
            liquidity_assessment["risk_level"] = "medium"
            
        return liquidity_assessment
        
    def _assess_liquidity_risk_score(self, balances: Dict[str, float], kpis: Dict[str, Any]) -> float:
        """Calculate liquidity risk score (0-1, higher is more risky)."""
        total_balance = sum(balances.values()) if balances else 0
        
        if total_balance == 0:
            return 1.0  # Maximum risk if no liquidity
            
        # Assess based on various factors
        risk_factors = []
        
        # Current ratio assessment
        current_ratio = kpis.get("liquidity_metrics", {}).get("current_ratio", 1.0)
        if current_ratio < 1.0:
            risk_factors.append(0.8)
        elif current_ratio < 1.5:
            risk_factors.append(0.4)
        else:
            risk_factors.append(0.1)
            
        # Quick ratio assessment
        quick_ratio = kpis.get("liquidity_metrics", {}).get("quick_ratio", 1.0)
        if quick_ratio < 0.5:
            risk_factors.append(0.7)
        elif quick_ratio < 1.0:
            risk_factors.append(0.3)
        else:
            risk_factors.append(0.1)
            
        # Cash conversion cycle
        cash_cycle = kpis.get("working_capital_metrics", {}).get("cash_conversion_cycle", 30)
        if cash_cycle > 60:
            risk_factors.append(0.6)
        elif cash_cycle > 30:
            risk_factors.append(0.3)
        else:
            risk_factors.append(0.1)
            
        return min(1.0, sum(risk_factors) / len(risk_factors)) if risk_factors else 0.5
        
    def _assess_operational_risk_score(self, anomalies: Dict[str, Any]) -> float:
        """Calculate operational risk score based on anomalies."""
        anomaly_count = len(anomalies.get("anomalies", []))
        
        if anomaly_count == 0:
            return 0.1  # Low risk
        elif anomaly_count <= 5:
            return 0.3  # Medium-low risk
        elif anomaly_count <= 10:
            return 0.6  # Medium-high risk
        else:
            return 0.9  # High risk
            
    def _assess_credit_risk_score(self, transactions: List[Dict], kpis: Dict[str, Any]) -> float:
        """Calculate credit risk score."""
        # Assess based on receivables and payment patterns
        dso = kpis.get("working_capital_metrics", {}).get("days_sales_outstanding", 30)
        
        if dso > 90:
            return 0.8  # High credit risk
        elif dso > 60:
            return 0.5  # Medium credit risk
        elif dso > 45:
            return 0.3  # Low-medium credit risk
        else:
            return 0.1  # Low credit risk
            
    def _assess_market_risk_score(self, transactions: List[Dict]) -> float:
        """Calculate market risk score based on transaction volatility."""
        if not transactions:
            return 0.5
            
        # Calculate transaction amount volatility
        amounts = [t.get("amount", 0) for t in transactions]
        
        if len(amounts) < 2:
            return 0.3
            
        import numpy as np
        volatility = np.std(amounts) / np.mean(amounts) if np.mean(amounts) != 0 else 0
        
        if volatility > self.risk_thresholds["volatility_threshold"]:
            return 0.7
        elif volatility > 0.1:
            return 0.4
        else:
            return 0.2
            
    def _assess_concentration_risk_score(self, transactions: List[Dict]) -> float:
        """Calculate concentration risk score."""
        if not transactions:
            return 0.3
            
        # Analyze counterparty concentration
        counterparty_amounts = {}
        total_amount = 0
        
        for transaction in transactions:
            counterparty = transaction.get("counterparty", "Unknown")
            amount = abs(transaction.get("amount", 0))
            
            counterparty_amounts[counterparty] = counterparty_amounts.get(counterparty, 0) + amount
            total_amount += amount
            
        if total_amount == 0:
            return 0.3
            
        # Check for concentration
        max_concentration = max(counterparty_amounts.values()) / total_amount
        
        if max_concentration > self.risk_thresholds["concentration_limit"]:
            return 0.8  # High concentration risk
        elif max_concentration > 0.15:
            return 0.4  # Medium concentration risk
        else:
            return 0.1  # Low concentration risk
            
    def _identify_risk_factors(self, risk_assessment: Dict[str, Any], kpis: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors."""
        factors = []
        
        if risk_assessment["liquidity_risk"] > 0.6:
            factors.append("High liquidity risk - insufficient cash reserves")
            
        if risk_assessment["operational_risk"] > 0.5:
            factors.append(f"Operational risk detected - {risk_assessment['anomalies_detected']} anomalies found")
            
        if risk_assessment["credit_risk"] > 0.5:
            factors.append("Elevated credit risk - extended collection periods")
            
        if risk_assessment["market_risk"] > 0.5:
            factors.append("Market volatility risk - high transaction variability")
            
        if risk_assessment["concentration_risk"] > 0.5:
            factors.append("Concentration risk - overdependence on single counterparties")
            
        return factors
        
    def _generate_risk_recommendations(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if risk_assessment["liquidity_risk"] > 0.6:
            recommendations.append("Establish additional credit facilities or increase cash reserves")
            
        if risk_assessment["operational_risk"] > 0.5:
            recommendations.append("Investigate operational anomalies and strengthen internal controls")
            
        if risk_assessment["credit_risk"] > 0.5:
            recommendations.append("Review credit policies and accelerate collection processes")
            
        if risk_assessment["market_risk"] > 0.5:
            recommendations.append("Consider hedging strategies to reduce market exposure")
            
        if risk_assessment["concentration_risk"] > 0.5:
            recommendations.append("Diversify counterparty relationships and set exposure limits")
            
        if risk_assessment["overall_risk_score"] > 0.7:
            recommendations.append("Immediate risk committee review recommended")
            
        return recommendations
        
    async def _decide_liquidity_action(self, context: Dict[str, Any]) -> AgentDecision:
        """Make liquidity management decision."""
        liquidity_data = context.get("liquidity_data", {})
        current_balance = liquidity_data.get("current_balance", 0)
        minimum_required = liquidity_data.get("minimum_required", 1000000)
        
        shortfall = minimum_required - current_balance
        
        if shortfall > 0:
            if shortfall > 5000000:  # $5M+
                recommendation = "CRITICAL: Activate emergency credit facilities immediately"
                confidence = 0.95
            elif shortfall > 1000000:  # $1M+
                recommendation = "HIGH: Draw on credit lines and delay non-essential payments"
                confidence = 0.85
            else:
                recommendation = "MEDIUM: Monitor closely and prepare contingency funding"
                confidence = 0.75
        else:
            recommendation = "GOOD: Liquidity position adequate, no immediate action required"
            confidence = 0.90
            
        decision = AgentDecision(
            decision_id=f"liquidity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=self.agent_id,
            decision_type="liquidity_action",
            recommendation=recommendation,
            confidence_score=confidence,
            supporting_data={
                "current_balance": current_balance,
                "minimum_required": minimum_required,
                "shortfall": shortfall,
                "risk_assessment": "high" if shortfall > 1000000 else "medium" if shortfall > 0 else "low"
            }
        )
        
        self.record_decision(decision, success=True)
        return decision
        
    async def _analyze_consensus_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus proposal from risk perspective."""
        proposal_content = proposal.get("content", {})
        proposal_type = proposal.get("proposal_type", "")
        
        # Risk analysis based on proposal type
        if "investment" in proposal_type.lower():
            return await self._analyze_investment_proposal(proposal_content)
        elif "payment" in proposal_type.lower():
            return await self._analyze_payment_proposal(proposal_content)
        elif "credit" in proposal_type.lower():
            return await self._analyze_credit_proposal(proposal_content)
        else:
            return await self._analyze_general_proposal(proposal_content)
            
    async def _analyze_investment_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze investment proposal for risk."""
        amount = proposal.get("amount", 0)
        duration = proposal.get("duration_days", 30)
        risk_rating = proposal.get("risk_rating", "medium")
        
        # Risk assessment
        if amount > 10000000:  # $10M+
            vote = "reject"
            rationale = "Investment amount exceeds risk tolerance for single position"
            confidence = 0.9
        elif risk_rating in ["high", "speculative"]:
            vote = "reject"
            rationale = f"Risk rating '{risk_rating}' incompatible with treasury risk appetite"
            confidence = 0.85
        elif duration > 180:  # 6+ months
            vote = "abstain"
            rationale = "Long-term investment may impact liquidity flexibility"
            confidence = 0.7
        else:
            vote = "approve"
            rationale = "Investment parameters within acceptable risk bounds"
            confidence = 0.8
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale,
            "risk_assessment": {
                "amount_risk": "high" if amount > 10000000 else "medium" if amount > 5000000 else "low",
                "duration_risk": "high" if duration > 180 else "medium" if duration > 90 else "low",
                "rating_risk": risk_rating
            }
        }
        
    async def _analyze_payment_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze payment proposal for risk."""
        total_amount = proposal.get("total_amount", 0)
        payment_count = proposal.get("payment_count", 0)
        liquidity_impact = proposal.get("liquidity_impact", 0)
        
        if liquidity_impact < -5000000:  # -$5M impact
            vote = "reject"
            rationale = "Payment schedule creates unacceptable liquidity risk"
            confidence = 0.9
        elif total_amount > 25000000:  # $25M+
            vote = "abstain"
            rationale = "Large payment batch requires additional risk review"
            confidence = 0.8
        else:
            vote = "approve"
            rationale = "Payment proposal within acceptable risk parameters"
            confidence = 0.85
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale
        }
        
    async def _analyze_general_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze general proposal for risk implications."""
        # Default conservative approach
        financial_impact = proposal.get("financial_impact", 0)
        
        if abs(financial_impact) > 10000000:
            vote = "abstain"
            rationale = "High financial impact requires detailed risk analysis"
            confidence = 0.7
        else:
            vote = "approve"
            rationale = "No significant risk concerns identified"
            confidence = 0.75
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale
        }
        
    async def _general_risk_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make a general risk decision for unspecified scenarios."""
        decision_id = f"risk_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract relevant risk parameters
        liquidity_position = context.get("liquidity_position", 0)
        market_volatility = context.get("market_volatility", 0.1)
        credit_exposure = context.get("credit_exposure", 0)
        
        # General risk assessment logic
        risk_factors = []
        risk_score = 0.0
        
        # Liquidity risk assessment
        if liquidity_position < 500000:
            risk_factors.append("Low liquidity position")
            risk_score += 0.3
        elif liquidity_position < 1000000:
            risk_factors.append("Moderate liquidity concern")
            risk_score += 0.15
            
        # Market risk assessment
        if market_volatility > 0.2:
            risk_factors.append("High market volatility")
            risk_score += 0.25
        elif market_volatility > 0.15:
            risk_factors.append("Elevated market volatility")
            risk_score += 0.1
            
        # Credit risk assessment
        if credit_exposure > 10000000:
            risk_factors.append("High credit exposure")
            risk_score += 0.2
        elif credit_exposure > 5000000:
            risk_factors.append("Moderate credit exposure")
            risk_score += 0.1
            
        # Generate recommendation based on overall risk score
        if risk_score > 0.5:
            recommendation = f"HIGH RISK: Immediate action required. Risk factors: {', '.join(risk_factors)}"
            confidence = 0.9
        elif risk_score > 0.3:
            recommendation = f"MODERATE RISK: Monitor closely and consider mitigation. Risk factors: {', '.join(risk_factors)}"
            confidence = 0.85
        elif risk_score > 0.1:
            recommendation = f"LOW RISK: Standard monitoring sufficient. Minor concerns: {', '.join(risk_factors)}"
            confidence = 0.8
        else:
            recommendation = "MINIMAL RISK: Current risk levels are acceptable"
            confidence = 0.75
            
        decision = AgentDecision(
            decision_id=decision_id,
            agent_id=self.agent_id,
            decision_type="risk_assessment",
            recommendation=recommendation,
            confidence_score=confidence,
            supporting_data={
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "liquidity_position": liquidity_position,
                "market_volatility": market_volatility,
                "credit_exposure": credit_exposure,
                "assessment_timestamp": datetime.now().isoformat()
            }
        )
        
        self.record_decision(decision, success=True)
        return decision