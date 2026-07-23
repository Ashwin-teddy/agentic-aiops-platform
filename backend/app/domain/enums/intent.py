from enum import Enum


class IntentType(str, Enum):
    TROUBLESHOOTING = "troubleshooting"
    LOW_RISK_ACCESS = "low_risk_access"
    HIGH_RISK_ACCESS = "high_risk_access"
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"
