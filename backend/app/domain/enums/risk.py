from enum import Enum, IntEnum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def to_risk_level(self) -> RiskLevel:
        mapping = {
            RiskCategory.NONE: RiskLevel.LOW,
            RiskCategory.LOW: RiskLevel.LOW,
            RiskCategory.MEDIUM: RiskLevel.MEDIUM,
            RiskCategory.HIGH: RiskLevel.HIGH,
            RiskCategory.CRITICAL: RiskLevel.CRITICAL,
        }
        return mapping[self]
