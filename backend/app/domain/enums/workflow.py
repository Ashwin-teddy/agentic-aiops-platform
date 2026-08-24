from enum import StrEnum


class WorkflowType(StrEnum):
    TROUBLESHOOTING = "troubleshooting"
    ACCESS_REQUEST = "access_request"
    INCIDENT_RESPONSE = "incident_response"
    CHANGE_REQUEST = "change_request"
    ONBOARDING = "onboarding"
    OFFBOARDING = "offboarding"


class WorkflowState(StrEnum):
    INITIATED = "initiated"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
