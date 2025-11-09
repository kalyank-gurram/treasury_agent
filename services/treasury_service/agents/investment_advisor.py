"""Investment Advisor Agent for treasury investment and yield optimization."""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from .base_agent import (
    BaseAgent, AgentRole, AgentCapability, AgentMessage, AgentDecision,
    MessageType, MessagePriority
)
from .infrastructure.observability import get_observability_manager


class InvestmentAdvisorAgent(BaseAgent):
    """Specialized agent for treasury investment management and yield optimization."""
    
    def __init__(self, agent_id: str = "investment_advisor_001"):
        capabilities = [
            AgentCapability.INVESTMENT_ANALYSIS,
            AgentCapability.LIQUIDITY_MANAGEMENT,
            AgentCapability.RISK_ASSESSMENT,
            AgentCapability.CASH_FORECASTING
        ]
        
        super().__init__(agent_id, AgentRole.INVESTMENT_ADVISOR, capabilities)
        
        # Investment universe and constraints
        self.investment_universe = {
            "money_market": {
                "risk_level": "very_low",
                "typical_yield": 0.045,  # 4.5%
                "liquidity": "daily",
                "minimum_amount": 100000
            },
            "commercial_paper": {
                "risk_level": "low",
                "typical_yield": 0.052,  # 5.2%
                "liquidity": "maturity",
                "minimum_amount": 250000,
                "max_maturity_days": 270
            },
            "certificates_of_deposit": {
                "risk_level": "low",
                "typical_yield": 0.048,  # 4.8%
                "liquidity": "maturity",
                "minimum_amount": 100000,
                "max_maturity_days": 365
            },
            "treasury_bills": {
                "risk_level": "very_low",
                "typical_yield": 0.043,  # 4.3%
                "liquidity": "secondary_market",
                "minimum_amount": 100000,
                "max_maturity_days": 365
            },
            "repo_agreements": {
                "risk_level": "very_low",
                "typical_yield": 0.046,  # 4.6%
                "liquidity": "maturity",
                "minimum_amount": 500000,
                "max_maturity_days": 30
            },
            "corporate_bonds": {
                "risk_level": "medium",
                "typical_yield": 0.065,  # 6.5%
                "liquidity": "secondary_market",
                "minimum_amount": 250000,
                "max_maturity_days": 1825  # 5 years
            }
        }
        
        # Investment policy constraints
        self.investment_policy = {
            "maximum_maturity_days": 365,
            "minimum_liquidity_buffer": 0.15,  # 15% in liquid investments
            "maximum_single_issuer": 0.10,  # 10% max per issuer
            "maximum_investment_percentage": 0.80,  # 80% of available cash
            "risk_tolerance": "conservative",  # conservative, moderate, aggressive
            "yield_target": 0.045,  # 4.5% minimum yield target
            "diversification_requirement": True
        }
        
        # Performance tracking
        self.portfolio_performance = {
            "total_investments": 0,
            "average_yield": 0.0,
            "duration": 0.0,
            "liquidity_score": 0.0,
            "risk_score": 0.0
        }
        
        # Subscribe to relevant message types
        self.subscribe_to_message_type(MessageType.REQUEST)
        self.subscribe_to_message_type(MessageType.NOTIFICATION)
        self.subscribe_to_message_type(MessageType.CONSENSUS_PROPOSAL)
        
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize investment advisor configuration."""
        return {
            "investment_horizon": "short_term",  # short_term, medium_term, long_term
            "optimization_objective": "yield_liquidity_balanced",  # yield_focused, liquidity_focused, risk_focused, balanced
            "rebalancing_frequency": "weekly",
            "market_monitoring_frequency": timedelta(hours=4),
            "yield_curve_analysis": True,
            "credit_analysis_depth": "standard",  # basic, standard, comprehensive
            "benchmark": "3m_treasury"
        }
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages for investment management."""
        try:
            if message.message_type == MessageType.REQUEST:
                return await self._handle_investment_request(message)
            elif message.message_type == MessageType.NOTIFICATION:
                return await self._handle_investment_notification(message)
            elif message.message_type == MessageType.CONSENSUS_PROPOSAL:
                return await self._handle_consensus_proposal(message)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}",
                            message_id=message.message_id, error_type=type(e).__name__)
            return None
            
    async def _handle_investment_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle investment analysis and optimization requests."""
        content = message.content
        capability = content.get("capability")
        parameters = content.get("parameters", {})
        
        result = None
        
        if capability == AgentCapability.INVESTMENT_ANALYSIS.value:
            result = await self._analyze_investment_opportunities(parameters)
        elif capability == AgentCapability.LIQUIDITY_MANAGEMENT.value:
            result = await self._optimize_liquidity_ladder(parameters)
        elif capability == AgentCapability.RISK_ASSESSMENT.value:
            result = await self._assess_investment_risk(parameters)
        elif capability == AgentCapability.CASH_FORECASTING.value:
            result = await self._forecast_investment_returns(parameters)
            
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
        
    async def make_decision(self, context: Dict[str, Any]) -> AgentDecision:
        """Make investment decision based on context."""
        decision_type = context.get("decision_type", "investment_allocation")
        
        if decision_type == "investment_allocation":
            return await self._decide_investment_allocation(context)
        elif decision_type == "maturity_ladder":
            return await self._decide_maturity_ladder(context)
        elif decision_type == "yield_optimization":
            return await self._decide_yield_optimization(context)
        elif decision_type == "liquidity_rebalancing":
            return await self._decide_liquidity_rebalancing(context)
        else:
            return await self._general_investment_decision(context)
            
    async def _analyze_investment_opportunities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current investment opportunities."""
        available_cash = parameters.get("available_cash", 0)
        investment_horizon = parameters.get("investment_horizon", 90)  # days
        liquidity_needs = parameters.get("liquidity_needs", {})
        risk_tolerance = parameters.get("risk_tolerance", self.investment_policy["risk_tolerance"])
        
        self.logger.info(f"Analyzing investment opportunities for ${available_cash:,.0f}")
        
        # Calculate investable amount (reserve liquidity buffer)
        liquidity_buffer = available_cash * self.investment_policy["minimum_liquidity_buffer"]
        investable_amount = available_cash - liquidity_buffer
        max_investment = investable_amount * self.investment_policy["maximum_investment_percentage"]
        
        # Filter investment universe by constraints
        suitable_investments = self._filter_suitable_investments(
            max_investment, investment_horizon, risk_tolerance
        )
        
        # Generate investment recommendations
        recommendations = []
        
        for investment_type, details in suitable_investments.items():
            # Calculate expected return
            expected_yield = self._calculate_expected_yield(investment_type, investment_horizon)
            
            # Assess suitability score
            suitability_score = self._calculate_suitability_score(
                investment_type, details, investment_horizon, risk_tolerance
            )
            
            # Calculate optimal allocation
            suggested_allocation = self._calculate_optimal_allocation(
                investment_type, max_investment, suitability_score
            )
            
            if suggested_allocation >= details["minimum_amount"]:
                recommendations.append({
                    "investment_type": investment_type,
                    "suggested_allocation": suggested_allocation,
                    "expected_yield": expected_yield,
                    "suitability_score": suitability_score,
                    "risk_level": details["risk_level"],
                    "liquidity": details["liquidity"],
                    "maturity_recommendation": min(investment_horizon, details.get("max_maturity_days", 365)),
                    "rationale": self._generate_investment_rationale(investment_type, details, suitability_score)
                })
                
        # Sort by suitability score
        recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
        
        # Calculate portfolio metrics
        total_allocation = sum(rec["suggested_allocation"] for rec in recommendations)
        weighted_yield = sum(
            rec["suggested_allocation"] * rec["expected_yield"] for rec in recommendations
        ) / total_allocation if total_allocation > 0 else 0
        
        return {
            "available_cash": available_cash,
            "liquidity_buffer": liquidity_buffer,
            "investable_amount": investable_amount,
            "recommended_investments": recommendations,
            "portfolio_metrics": {
                "total_investment": total_allocation,
                "weighted_average_yield": weighted_yield,
                "investment_utilization": (total_allocation / max_investment) * 100 if max_investment > 0 else 0,
                "diversification_score": len(recommendations) / len(self.investment_universe) * 100
            },
            "liquidity_ladder": self._generate_liquidity_ladder(recommendations, liquidity_needs)
        }
        
    async def _optimize_liquidity_ladder(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize maturity ladder for liquidity management."""
        total_investment = parameters.get("total_investment", 0)
        cash_flow_forecast = parameters.get("cash_flow_forecast", {})
        maturity_horizon = parameters.get("maturity_horizon", 365)
        
        # Generate maturity buckets
        maturity_buckets = {
            "0-30_days": {"target_percentage": 0.30, "allocation": 0},
            "31-60_days": {"target_percentage": 0.25, "allocation": 0},
            "61-90_days": {"target_percentage": 0.20, "allocation": 0},
            "91-180_days": {"target_percentage": 0.15, "allocation": 0},
            "181-365_days": {"target_percentage": 0.10, "allocation": 0}
        }
        
        # Allocate based on cash flow needs and yield optimization
        for bucket_name, bucket_data in maturity_buckets.items():
            bucket_data["allocation"] = total_investment * bucket_data["target_percentage"]
            
        # Optimize within each bucket
        optimized_ladder = {}
        
        for bucket_name, bucket_data in maturity_buckets.items():
            bucket_days = self._parse_bucket_days(bucket_name)
            
            optimized_ladder[bucket_name] = {
                "allocation": bucket_data["allocation"],
                "target_percentage": bucket_data["target_percentage"],
                "recommended_instruments": self._recommend_instruments_for_bucket(
                    bucket_data["allocation"], bucket_days
                ),
                "expected_yield": self._calculate_bucket_yield(bucket_days),
                "liquidity_score": self._calculate_bucket_liquidity_score(bucket_days)
            }
            
        return {
            "total_investment": total_investment,
            "maturity_ladder": optimized_ladder,
            "ladder_metrics": {
                "average_maturity": self._calculate_weighted_average_maturity(optimized_ladder),
                "yield_pickup": self._calculate_yield_pickup(optimized_ladder),
                "liquidity_coverage": self._calculate_liquidity_coverage(optimized_ladder, cash_flow_forecast)
            }
        }
        
    async def _assess_investment_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess investment portfolio risk."""
        portfolio = parameters.get("portfolio", [])
        market_conditions = parameters.get("market_conditions", {})
        
        risk_assessment = {
            "overall_risk_score": 0.0,
            "credit_risk": 0.0,
            "interest_rate_risk": 0.0,
            "liquidity_risk": 0.0,
            "concentration_risk": 0.0,
            "market_risk": 0.0,
            "risk_factors": [],
            "risk_mitigation_recommendations": []
        }
        
        if not portfolio:
            return risk_assessment
            
        # Calculate individual risk components
        risk_assessment["credit_risk"] = self._calculate_credit_risk(portfolio)
        risk_assessment["interest_rate_risk"] = self._calculate_interest_rate_risk(portfolio, market_conditions)
        risk_assessment["liquidity_risk"] = self._calculate_liquidity_risk(portfolio)
        risk_assessment["concentration_risk"] = self._calculate_concentration_risk(portfolio)
        risk_assessment["market_risk"] = self._calculate_market_risk(portfolio, market_conditions)
        
        # Calculate overall risk score (weighted average)
        weights = {
            "credit": 0.30, "interest_rate": 0.25, "liquidity": 0.20,
            "concentration": 0.15, "market": 0.10
        }
        
        risk_assessment["overall_risk_score"] = (
            risk_assessment["credit_risk"] * weights["credit"] +
            risk_assessment["interest_rate_risk"] * weights["interest_rate"] +
            risk_assessment["liquidity_risk"] * weights["liquidity"] +
            risk_assessment["concentration_risk"] * weights["concentration"] +
            risk_assessment["market_risk"] * weights["market"]
        )
        
        # Generate risk factors and recommendations
        risk_assessment["risk_factors"] = self._identify_investment_risk_factors(risk_assessment)
        risk_assessment["risk_mitigation_recommendations"] = self._generate_risk_mitigation_recommendations(risk_assessment)
        
        return risk_assessment
        
    def _filter_suitable_investments(self, max_investment: float, horizon_days: int, 
                                   risk_tolerance: str) -> Dict[str, Dict[str, Any]]:
        """Filter investment universe based on constraints."""
        suitable = {}
        
        for inv_type, details in self.investment_universe.items():
            # Check amount constraint
            if details["minimum_amount"] > max_investment:
                continue
                
            # Check maturity constraint
            max_maturity = details.get("max_maturity_days", 365)
            if max_maturity < horizon_days:
                continue
                
            # Check risk tolerance
            if not self._risk_suitable(details["risk_level"], risk_tolerance):
                continue
                
            suitable[inv_type] = details.copy()
            
        return suitable
        
    def _risk_suitable(self, investment_risk: str, risk_tolerance: str) -> bool:
        """Check if investment risk level matches risk tolerance."""
        risk_levels = {
            "very_low": 1, "low": 2, "medium": 3, "high": 4, "very_high": 5
        }
        
        tolerance_levels = {
            "conservative": 2, "moderate": 3, "aggressive": 4
        }
        
        inv_risk_level = risk_levels.get(investment_risk, 3)
        tolerance_level = tolerance_levels.get(risk_tolerance, 2)
        
        return inv_risk_level <= tolerance_level
        
    def _calculate_expected_yield(self, investment_type: str, horizon_days: int) -> float:
        """Calculate expected yield for investment type."""
        base_yield = self.investment_universe[investment_type]["typical_yield"]
        
        # Adjust for current market conditions (simplified)
        market_adjustment = np.random.normal(0, 0.002)  # ±20 basis points volatility
        
        # Adjust for maturity (yield curve)
        if horizon_days <= 30:
            maturity_adjustment = -0.001  # -10 basis points for short term
        elif horizon_days <= 90:
            maturity_adjustment = 0.0
        elif horizon_days <= 180:
            maturity_adjustment = 0.0005  # +5 basis points
        else:
            maturity_adjustment = 0.001  # +10 basis points for longer term
            
        return max(0.01, base_yield + market_adjustment + maturity_adjustment)
        
    def _calculate_suitability_score(self, investment_type: str, details: Dict[str, Any],
                                   horizon_days: int, risk_tolerance: str) -> float:
        """Calculate suitability score (0-1) for investment."""
        score = 0.0
        
        # Yield component (30% weight)
        yield_score = details["typical_yield"] / 0.08  # Normalize to 8% max
        score += min(1.0, yield_score) * 0.30
        
        # Risk component (25% weight)
        risk_levels = {"very_low": 1.0, "low": 0.8, "medium": 0.6, "high": 0.4, "very_high": 0.2}
        risk_score = risk_levels.get(details["risk_level"], 0.6)
        score += risk_score * 0.25
        
        # Liquidity component (25% weight)
        liquidity_scores = {"daily": 1.0, "secondary_market": 0.8, "maturity": 0.6}
        liquidity_score = liquidity_scores.get(details["liquidity"], 0.6)
        score += liquidity_score * 0.25
        
        # Maturity matching component (20% weight)
        max_maturity = details.get("max_maturity_days", 365)
        if horizon_days <= max_maturity:
            maturity_score = 1.0 - abs(horizon_days - max_maturity/2) / (max_maturity/2)
        else:
            maturity_score = 0.5
        score += max(0.0, maturity_score) * 0.20
        
        return min(1.0, max(0.0, score))
        
    def _calculate_optimal_allocation(self, investment_type: str, max_investment: float,
                                    suitability_score: float) -> float:
        """Calculate optimal allocation for investment type."""
        # Base allocation proportional to suitability
        base_allocation = max_investment * suitability_score * 0.3
        
        # Apply diversification constraints
        max_single_allocation = max_investment * self.investment_policy["maximum_single_issuer"]
        
        return min(base_allocation, max_single_allocation)
        
    def _generate_investment_rationale(self, investment_type: str, details: Dict[str, Any],
                                     suitability_score: float) -> str:
        """Generate rationale for investment recommendation."""
        yield_pct = details["typical_yield"] * 100
        risk_level = details["risk_level"].replace("_", " ").title()
        
        if suitability_score > 0.8:
            return f"Excellent fit: {yield_pct:.2f}% yield with {risk_level} risk profile aligns well with investment objectives"
        elif suitability_score > 0.6:
            return f"Good option: {yield_pct:.2f}% yield provides solid return for {risk_level} risk level"
        elif suitability_score > 0.4:
            return f"Acceptable choice: {yield_pct:.2f}% yield with {risk_level} risk suitable for diversification"
        else:
            return f"Limited appeal: {yield_pct:.2f}% yield may not justify {risk_level} risk level"
            
    async def _decide_investment_allocation(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on investment allocation strategy."""
        available_cash = context.get("available_cash", 0)
        market_conditions = context.get("market_conditions", {})
        liquidity_needs = context.get("liquidity_needs", {})
        
        # Analyze market conditions
        interest_rate_trend = market_conditions.get("interest_rate_trend", "stable")
        credit_spread_trend = market_conditions.get("credit_spread_trend", "stable")
        
        # Generate allocation strategy
        if interest_rate_trend == "rising":
            recommendation = "SHORTEN: Reduce duration and increase short-term allocations"
            strategy = "defensive"
            confidence = 0.80
        elif interest_rate_trend == "falling":
            recommendation = "EXTEND: Lock in current yields with longer maturities"
            strategy = "opportunistic"
            confidence = 0.75
        elif credit_spread_trend == "widening":
            recommendation = "QUALITY: Focus on highest credit quality investments"
            strategy = "conservative"
            confidence = 0.85
        else:
            recommendation = "BALANCED: Maintain diversified ladder across maturities"
            strategy = "balanced"
            confidence = 0.70
            
        decision = AgentDecision(
            decision_id=f"allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=self.agent_id,
            decision_type="investment_allocation",
            recommendation=recommendation,
            confidence_score=confidence,
            supporting_data={
                "available_cash": available_cash,
                "strategy": strategy,
                "market_conditions": market_conditions,
                "interest_rate_trend": interest_rate_trend,
                "credit_spread_trend": credit_spread_trend
            }
        )
        
        self.record_decision(decision, success=True)
        return decision
        
    async def _analyze_consensus_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus proposal from investment perspective."""
        proposal_content = proposal.get("content", {})
        proposal_type = proposal.get("proposal_type", "")
        
        if "investment" in proposal_type.lower():
            return await self._analyze_investment_policy_proposal(proposal_content)
        elif "liquidity" in proposal_type.lower():
            return await self._analyze_liquidity_policy_proposal(proposal_content)
        elif "risk" in proposal_type.lower():
            return await self._analyze_risk_policy_proposal(proposal_content)
        else:
            return await self._analyze_general_investment_proposal(proposal_content)
            
    async def _analyze_investment_policy_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze investment policy changes."""
        policy_changes = proposal.get("policy_changes", {})
        
        # Key factors to evaluate
        max_maturity_change = policy_changes.get("maximum_maturity_days")
        risk_tolerance_change = policy_changes.get("risk_tolerance")
        yield_target_change = policy_changes.get("yield_target")
        
        risk_factors = []
        
        if max_maturity_change and max_maturity_change > 730:  # > 2 years
            risk_factors.append("Extended maturity increases interest rate risk")
            
        if risk_tolerance_change == "aggressive":
            risk_factors.append("Aggressive risk tolerance may compromise principal preservation")
            
        if yield_target_change and yield_target_change > 0.07:  # > 7%
            risk_factors.append("High yield target may require excessive risk-taking")
            
        if len(risk_factors) >= 2:
            vote = "reject"
            rationale = f"Multiple risk concerns: {'; '.join(risk_factors)}"
            confidence = 0.85
        elif len(risk_factors) == 1:
            vote = "abstain"
            rationale = f"Risk concern requiring discussion: {risk_factors[0]}"
            confidence = 0.75
        else:
            vote = "approve"
            rationale = "Policy changes align with prudent investment management"
            confidence = 0.80
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale,
            "investment_impact": "negative" if len(risk_factors) >= 2 else "neutral"
        }