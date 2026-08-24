from enum import StrEnum


class AccessType(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    DELETE = "delete"
    EXECUTE = "execute"


class ResourceType(StrEnum):
    JIRA = "jira"
    CONFLUENCE = "confluence"
    GITHUB = "github"
    AWS_IAM = "aws_iam"
    KUBERNETES = "kubernetes"
    AZURE_AD = "azure_ad"
    OKTA = "okta"
    SERVICENOW = "servicenow"
    PRODUCTION_DATABASE = "production_database"
    CUSTOM = "custom"
