"""Compliance Officer Agent for regulatory compliance and audit management."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from .base_agent import (
    BaseAgent, AgentRole, AgentCapability, AgentMessage, AgentDecision,
    MessageType, MessagePriority
)
from .infrastructure.observability import get_observability_manager


class ComplianceOfficerAgent(BaseAgent):
    """Specialized agent for regulatory compliance and audit management."""
    
    def __init__(self, agent_id: str = "compliance_officer_001"):
        capabilities = [
            AgentCapability.COMPLIANCE_CHECK,
            AgentCapability.RISK_ASSESSMENT,
            AgentCapability.REPORTING,
            AgentCapability.SCENARIO_ANALYSIS
        ]
        
        super().__init__(agent_id, AgentRole.COMPLIANCE_OFFICER, capabilities)
        
        # Regulatory frameworks and requirements
        self.regulatory_frameworks = {
            "sox": {
                "name": "Sarbanes-Oxley Act",
                "requirements": ["segregation_of_duties", "approval_workflows", "audit_trails"],
                "critical_controls": ["cash_management", "financial_reporting", "internal_controls"]
            },
            "basel_iii": {
                "name": "Basel III Capital Requirements",
                "requirements": ["liquidity_coverage_ratio", "net_stable_funding_ratio", "capital_adequacy"],
                "critical_controls": ["liquidity_management", "credit_risk", "operational_risk"]
            },
            "coso": {
                "name": "COSO Internal Control Framework",
                "requirements": ["control_environment", "risk_assessment", "control_activities", "monitoring"],
                "critical_controls": ["authorization", "reconciliation", "segregation", "documentation"]
            },
            "gdpr": {
                "name": "General Data Protection Regulation",
                "requirements": ["data_protection", "privacy_controls", "breach_notification"],
                "critical_controls": ["data_encryption", "access_controls", "audit_logging"]
            },
            "pci_dss": {
                "name": "Payment Card Industry Data Security Standard",
                "requirements": ["secure_networks", "cardholder_data_protection", "access_controls"],
                "critical_controls": ["encryption", "authentication", "monitoring", "testing"]
            }
        }
        
        # Compliance monitoring rules
        self.compliance_rules = {
            "transaction_limits": {
                "single_transaction_limit": 10000000,  # $10M
                "daily_aggregate_limit": 50000000,     # $50M
                "monthly_aggregate_limit": 500000000,   # $500M
                "requires_dual_approval": 5000000      # $5M+
            },
            "segregation_of_duties": {
                "payment_initiation_approval": True,
                "reconciliation_independence": True,
                "investment_authorization_separation": True
            },
            "documentation_requirements": {
                "transaction_documentation": "required",
                "approval_documentation": "required",
                "exception_documentation": "required",
                "audit_trail_retention": 2555  # 7 years in days
            },
            "reporting_requirements": {
                "daily_cash_reporting": True,
                "monthly_compliance_report": True,
                "quarterly_risk_assessment": True,
                "annual_audit_preparation": True
            }
        }
        
        # Compliance violations tracking
        self.violation_tracking = {
            "total_violations": 0,
            "critical_violations": 0,
            "resolved_violations": 0,
            "pending_violations": 0
        }
        
        # Subscribe to all message types for compliance monitoring
        for msg_type in MessageType:
            self.subscribe_to_message_type(msg_type)
            
    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize compliance officer configuration."""
        return {
            "regulatory_jurisdiction": "US",  # US, EU, APAC, Global
            "compliance_framework": "comprehensive",  # basic, standard, comprehensive
            "audit_frequency": "quarterly",
            "violation_escalation_time": timedelta(hours=24),
            "compliance_reporting_level": "detailed",
            "automated_monitoring": True,
            "real_time_alerts": True,
            "risk_tolerance": "zero_tolerance"  # zero_tolerance, low, medium
        }
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages for compliance monitoring."""
        try:
            # Monitor all messages for compliance issues
            compliance_check = await self._monitor_message_compliance(message)
            
            if message.message_type == MessageType.REQUEST:
                return await self._handle_compliance_request(message)
            elif message.message_type == MessageType.ALERT:
                return await self._handle_compliance_alert(message)
            elif message.message_type == MessageType.CONSENSUS_PROPOSAL:
                return await self._handle_consensus_proposal(message)
            else:
                # For other messages, return compliance check if violations found
                if compliance_check and compliance_check.get("violations"):
                    return await self._create_compliance_alert(message, compliance_check)
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}",
                            message_id=message.message_id, error_type=type(e).__name__)
            return None
            
    async def _handle_compliance_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle compliance check requests."""
        content = message.content
        capability = content.get("capability")
        parameters = content.get("parameters", {})
        
        result = None
        
        if capability == AgentCapability.COMPLIANCE_CHECK.value:
            result = await self._perform_compliance_check(parameters)
        elif capability == AgentCapability.RISK_ASSESSMENT.value:
            result = await self._assess_compliance_risk(parameters)
        elif capability == AgentCapability.REPORTING.value:
            result = await self._generate_compliance_report(parameters)
        elif capability == AgentCapability.SCENARIO_ANALYSIS.value:
            result = await self._analyze_compliance_scenarios(parameters)
            
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
        """Make compliance decision based on context."""
        decision_type = context.get("decision_type", "compliance_approval")
        
        if decision_type == "compliance_approval":
            return await self._decide_compliance_approval(context)
        elif decision_type == "violation_response":
            return await self._decide_violation_response(context)
        elif decision_type == "audit_preparation":
            return await self._decide_audit_preparation(context)
        elif decision_type == "regulatory_change":
            return await self._decide_regulatory_change_response(context)
        else:
            return await self._general_compliance_decision(context)
            
    async def _monitor_message_compliance(self, message: AgentMessage) -> Dict[str, Any]:
        """Monitor message for compliance violations."""
        violations = []
        
        # Check for transaction limit violations
        if "amount" in message.content:
            amount = message.content.get("amount", 0)
            violations.extend(self._check_transaction_limits(amount, message))
            
        # Check for authorization requirements
        if message.message_type in [MessageType.REQUEST] and "payment" in str(message.content).lower():
            violations.extend(self._check_authorization_requirements(message))
            
        # Check for documentation requirements
        violations.extend(self._check_documentation_requirements(message))
        
        # Check for segregation of duties
        violations.extend(self._check_segregation_of_duties(message))
        
        return {
            "message_id": message.message_id,
            "violations": violations,
            "compliance_score": self._calculate_compliance_score(violations),
            "risk_level": self._assess_message_risk_level(violations)
        }
        
    def _check_transaction_limits(self, amount: float, message: AgentMessage) -> List[Dict[str, Any]]:
        """Check transaction amount against limits."""
        violations = []
        limits = self.compliance_rules["transaction_limits"]
        
        if amount > limits["single_transaction_limit"]:
            violations.append({
                "type": "transaction_limit_exceeded",
                "severity": "critical",
                "description": f"Transaction amount ${amount:,.0f} exceeds single transaction limit of ${limits['single_transaction_limit']:,.0f}",
                "regulatory_framework": "internal_policy",
                "required_action": "executive_approval_required"
            })
            
        if amount > limits["requires_dual_approval"] and "dual_approval" not in message.content:
            violations.append({
                "type": "dual_approval_required",
                "severity": "high",
                "description": f"Transaction amount ${amount:,.0f} requires dual approval",
                "regulatory_framework": "sox",
                "required_action": "obtain_secondary_approval"
            })
            
        return violations
        
    def _check_authorization_requirements(self, message: AgentMessage) -> List[Dict[str, Any]]:
        """Check authorization requirements."""
        violations = []
        
        # Check for required approvals
        if "authorization" not in message.content and "approval" not in message.content:
            violations.append({
                "type": "missing_authorization",
                "severity": "high",
                "description": "Payment request lacks proper authorization documentation",
                "regulatory_framework": "sox",
                "required_action": "obtain_proper_authorization"
            })
            
        return violations
        
    def _check_documentation_requirements(self, message: AgentMessage) -> List[Dict[str, Any]]:
        """Check documentation requirements."""
        violations = []
        
        # Check for audit trail
        if not message.correlation_id:
            violations.append({
                "type": "missing_audit_trail",
                "severity": "medium",
                "description": "Message lacks correlation ID for audit trail",
                "regulatory_framework": "sox",
                "required_action": "implement_correlation_tracking"
            })
            
        return violations
        
    def _check_segregation_of_duties(self, message: AgentMessage) -> List[Dict[str, Any]]:
        """Check segregation of duties requirements."""
        violations = []
        
        # This would be more sophisticated in a real implementation
        # For now, we'll do basic checks
        
        sender_role = message.content.get("sender_role")
        if sender_role == "payment_initiator" and "approval" in message.content:
            violations.append({
                "type": "segregation_of_duties_violation",
                "severity": "critical",
                "description": "Payment initiator cannot also approve payment - segregation of duties violation",
                "regulatory_framework": "sox",
                "required_action": "separate_approval_authority"
            })
            
        return violations
        
    async def _perform_compliance_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive compliance check."""
        check_type = parameters.get("type", "comprehensive")
        entity = parameters.get("entity", "ALL")
        timeframe = parameters.get("timeframe", "current")
        
        self.logger.info(f"Performing {check_type} compliance check for {entity}")
        
        compliance_results = {
            "check_type": check_type,
            "entity": entity,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "overall_compliance_score": 0.0,
            "framework_compliance": {},
            "violations_summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "remediation_actions": [],
            "audit_readiness": "unknown"
        }
        
        # Check each regulatory framework
        for framework_code, framework_info in self.regulatory_frameworks.items():
            framework_compliance = await self._check_framework_compliance(
                framework_code, framework_info, parameters
            )
            compliance_results["framework_compliance"][framework_code] = framework_compliance
            
        # Calculate overall compliance score
        framework_scores = [
            fc["compliance_score"] for fc in compliance_results["framework_compliance"].values()
        ]
        compliance_results["overall_compliance_score"] = sum(framework_scores) / len(framework_scores) if framework_scores else 0.0
        
        # Count violations by severity
        for framework_compliance in compliance_results["framework_compliance"].values():
            for violation in framework_compliance.get("violations", []):
                severity = violation.get("severity", "medium")
                if severity in compliance_results["violations_summary"]:
                    compliance_results["violations_summary"][severity] += 1
                    
        # Generate remediation actions
        compliance_results["remediation_actions"] = self._generate_remediation_actions(compliance_results)
        
        # Assess audit readiness
        compliance_results["audit_readiness"] = self._assess_audit_readiness(compliance_results)
        
        return compliance_results
        
    async def _check_framework_compliance(self, framework_code: str, framework_info: Dict[str, Any],
                                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with specific regulatory framework."""
        framework_result = {
            "framework": framework_info["name"],
            "compliance_score": 0.0,
            "violations": [],
            "control_assessments": {},
            "requirements_met": 0,
            "total_requirements": len(framework_info["requirements"])
        }
        
        # Assess each requirement
        for requirement in framework_info["requirements"]:
            control_assessment = await self._assess_control(framework_code, requirement, parameters)
            framework_result["control_assessments"][requirement] = control_assessment
            
            if control_assessment["compliant"]:
                framework_result["requirements_met"] += 1
            else:
                framework_result["violations"].extend(control_assessment["violations"])
                
        # Calculate framework compliance score
        if framework_result["total_requirements"] > 0:
            framework_result["compliance_score"] = (
                framework_result["requirements_met"] / framework_result["total_requirements"]
            ) * 100
            
        return framework_result
        
    async def _assess_control(self, framework: str, requirement: str, 
                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess specific control requirement."""
        # Simplified control assessment - in reality this would be much more detailed
        
        assessment = {
            "requirement": requirement,
            "compliant": True,
            "violations": [],
            "evidence": [],
            "last_tested": datetime.now().isoformat(),
            "next_review_due": (datetime.now() + timedelta(days=90)).isoformat()
        }
        
        # Framework-specific assessments
        if framework == "sox":
            assessment = await self._assess_sox_control(requirement, parameters)
        elif framework == "basel_iii":
            assessment = await self._assess_basel_control(requirement, parameters)
        elif framework == "coso":
            assessment = await self._assess_coso_control(requirement, parameters)
        elif framework == "gdpr":
            assessment = await self._assess_gdpr_control(requirement, parameters)
        elif framework == "pci_dss":
            assessment = await self._assess_pci_control(requirement, parameters)
            
        return assessment
        
    async def _assess_sox_control(self, requirement: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess SOX control requirement."""
        assessment = {
            "requirement": requirement,
            "compliant": True,
            "violations": [],
            "evidence": ["automated_controls", "audit_trail", "documentation"],
            "last_tested": datetime.now().isoformat(),
            "next_review_due": (datetime.now() + timedelta(days=90)).isoformat()
        }
        
        if requirement == "segregation_of_duties":
            # Check if proper segregation exists
            segregation_rules = self.compliance_rules["segregation_of_duties"]
            for rule, required in segregation_rules.items():
                if required and not self._verify_segregation_implementation(rule):
                    assessment["compliant"] = False
                    assessment["violations"].append({
                        "type": "sox_segregation_failure",
                        "severity": "critical",
                        "description": f"Segregation of duties not properly implemented for {rule}",
                        "regulatory_framework": "sox"
                    })
                    
        elif requirement == "approval_workflows":
            # Check approval workflow implementation
            if not self._verify_approval_workflows():
                assessment["compliant"] = False
                assessment["violations"].append({
                    "type": "sox_approval_failure", 
                    "severity": "high",
                    "description": "Approval workflows not properly configured",
                    "regulatory_framework": "sox"
                })
                
        return assessment
        
    def _verify_segregation_implementation(self, rule: str) -> bool:
        """Verify segregation of duties implementation (simplified)."""
        # In a real implementation, this would check actual system configurations
        return True  # Assume compliant for demo
        
    def _verify_approval_workflows(self) -> bool:
        """Verify approval workflow implementation (simplified)."""
        # In a real implementation, this would check workflow configurations
        return True  # Assume compliant for demo
        
    def _calculate_compliance_score(self, violations: List[Dict[str, Any]]) -> float:
        """Calculate compliance score based on violations."""
        if not violations:
            return 100.0
            
        # Weight violations by severity
        severity_weights = {"critical": 25, "high": 15, "medium": 10, "low": 5}
        
        total_deduction = sum(
            severity_weights.get(violation.get("severity", "medium"), 10)
            for violation in violations
        )
        
        return max(0.0, 100.0 - total_deduction)
        
    def _assess_message_risk_level(self, violations: List[Dict[str, Any]]) -> str:
        """Assess risk level based on violations."""
        if not violations:
            return "low"
            
        critical_count = len([v for v in violations if v.get("severity") == "critical"])
        high_count = len([v for v in violations if v.get("severity") == "high"])
        
        if critical_count > 0:
            return "critical"
        elif high_count > 0:
            return "high"
        elif len(violations) > 3:
            return "medium"
        else:
            return "low"
            
    async def _decide_compliance_approval(self, context: Dict[str, Any]) -> AgentDecision:
        """Decide on compliance approval for proposed action."""
        action_type = context.get("action_type", "unknown")
        compliance_assessment = context.get("compliance_assessment", {})
        risk_level = context.get("risk_level", "medium")
        
        violations = compliance_assessment.get("violations", [])
        compliance_score = compliance_assessment.get("compliance_score", 100.0)
        
        # Decision logic
        if violations and any(v.get("severity") == "critical" for v in violations):
            recommendation = f"REJECT: Critical compliance violations prevent approval of {action_type}"
            confidence = 0.95
            approval = False
        elif compliance_score < 70:
            recommendation = f"CONDITIONAL: {action_type} requires remediation before approval"
            confidence = 0.85
            approval = False
        elif compliance_score < 85:
            recommendation = f"APPROVE WITH CONDITIONS: {action_type} approved with enhanced monitoring"
            confidence = 0.75
            approval = True
        else:
            recommendation = f"APPROVE: {action_type} meets all compliance requirements"
            confidence = 0.90
            approval = True
            
        decision = AgentDecision(
            decision_id=f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=self.agent_id,
            decision_type="compliance_approval",
            recommendation=recommendation,
            confidence_score=confidence,
            supporting_data={
                "action_type": action_type,
                "compliance_score": compliance_score,
                "violations_count": len(violations),
                "risk_level": risk_level,
                "approval_granted": approval
            }
        )
        
        self.record_decision(decision, success=approval)
        return decision
        
    async def _analyze_consensus_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consensus proposal from compliance perspective."""
        proposal_content = proposal.get("content", {})
        proposal_type = proposal.get("proposal_type", "")
        
        # Perform compliance assessment
        compliance_check = await self._perform_compliance_check({
            "type": "proposal_review",
            "proposal": proposal_content
        })
        
        compliance_score = compliance_check.get("overall_compliance_score", 100.0)
        critical_violations = compliance_check.get("violations_summary", {}).get("critical", 0)
        
        if critical_violations > 0:
            vote = "reject"
            rationale = f"Proposal contains {critical_violations} critical compliance violations"
            confidence = 0.95
        elif compliance_score < 70:
            vote = "reject"
            rationale = f"Proposal compliance score ({compliance_score:.1f}%) below minimum threshold"
            confidence = 0.85
        elif compliance_score < 85:
            vote = "abstain"
            rationale = f"Proposal requires compliance remediation (score: {compliance_score:.1f}%)"
            confidence = 0.75
        else:
            vote = "approve"
            rationale = f"Proposal meets compliance standards (score: {compliance_score:.1f}%)"
            confidence = 0.85
            
        return {
            "vote": vote,
            "confidence": confidence,
            "rationale": rationale,
            "compliance_assessment": {
                "score": compliance_score,
                "critical_violations": critical_violations,
                "requires_remediation": compliance_score < 85
            }
        }