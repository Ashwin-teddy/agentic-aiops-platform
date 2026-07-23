from __future__ import annotations

from typing import Any

from app.core.config.settings import settings
from app.domain.enums.access import AccessType, ResourceType
from app.domain.enums.risk import RiskLevel, RiskCategory
from app.memory.organizational.org_memory import OrganizationalMemory
from app.observability.logging import get_logger

logger = get_logger(__name__)

RESOURCE_RISK_MAP: dict[str, dict[str, float]] = {
    "jira": {"read": 0.1, "write": 0.2, "admin": 0.5},
    "confluence": {"read": 0.1, "write": 0.2, "admin": 0.5},
    "github": {"read": 0.1, "write": 0.3, "admin": 0.6},
    "aws_iam": {"read": 0.3, "write": 0.7, "admin": 0.95},
    "kubernetes": {"read": 0.2, "write": 0.6, "admin": 0.9},
    "azure_ad": {"read": 0.3, "write": 0.7, "admin": 0.9},
    "okta": {"read": 0.3, "write": 0.7, "admin": 0.9},
    "servicenow": {"read": 0.1, "write": 0.3, "admin": 0.6},
    "production_database": {"read": 0.6, "write": 0.85, "admin": 0.95, "delete": 1.0},
}


class PolicyAgent:
    name = "policy_agent"

    def __init__(self) -> None:
        self.org_memory = OrganizationalMemory()

    async def evaluate_risk(
        self,
        resource_type: str,
        access_type: str,
        user_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resource_risks = RESOURCE_RISK_MAP.get(resource_type, {})
        base_risk = resource_risks.get(access_type, 0.5)
        adjusted_risk = base_risk
        context_factors: list[str] = []
        if user_context:
            if user_context.get("is_on_team", False):
                adjusted_risk -= 0.1
                context_factors.append("user_is_on_team")
            if user_context.get("has_similar_access", False):
                adjusted_risk -= 0.05
                context_factors.append("has_similar_access")
            if user_context.get("is_new_user", False):
                adjusted_risk += 0.1
                context_factors.append("new_user")
            if user_context.get("outside_business_hours", False):
                adjusted_risk += 0.1
                context_factors.append("outside_business_hours")
        adjusted_risk = max(0.0, min(1.0, adjusted_risk))
        risk_level = self._score_to_level(adjusted_risk)
        policy_check = await self._check_org_policies(resource_type, access_type, user_context)
        return {
            "risk_score": round(adjusted_risk, 3),
            "risk_level": risk_level,
            "base_risk": base_risk,
            "context_factors": context_factors,
            "policy_compliant": policy_check["compliant"],
            "policy_violations": policy_check.get("violations", []),
            "requires_approval": risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL),
            "requires_manager_approval": risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL),
            "requires_security_approval": risk_level == RiskLevel.CRITICAL,
            "auto_approve": risk_level == RiskLevel.LOW and adjusted_risk < settings.auto_approve_threshold,
        }

    async def _check_org_policies(
        self, resource_type: str, access_type: str, user_context: dict[str, Any] | None
    ) -> dict[str, Any]:
        violations: list[str] = []
        policy = await self.org_memory.get_policy(f"access:{resource_type}")
        if policy:
            if policy.get("require_justification", False):
                if not user_context or not user_context.get("justification"):
                    violations.append("Missing required justification")
            if policy.get("max_duration_hours"):
                pass
            blocked_teams = policy.get("blocked_teams", [])
            if user_context and user_context.get("team") in blocked_teams:
                violations.append(f"Team '{user_context['team']}' is not authorized for this resource")
        return {"compliant": len(violations) == 0, "violations": violations}

    @staticmethod
    def _score_to_level(score: float) -> RiskLevel:
        if score < settings.auto_approve_threshold:
            return RiskLevel.LOW
        elif score < settings.high_risk_threshold:
            return RiskLevel.MEDIUM
        elif score < settings.critical_risk_threshold:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    async def get_allowed_resources(self, user_roles: list[str]) -> dict[str, list[str]]:
        allowed: dict[str, list[str]] = {}
        for resource_type, risks in RESOURCE_RISK_MAP.items():
            allowed_access = []
            for access_type, score in risks.items():
                if score < settings.high_risk_threshold or "admin" in user_roles:
                    allowed_access.append(access_type)
            if allowed_access:
                allowed[resource_type] = allowed_access
        return allowed
