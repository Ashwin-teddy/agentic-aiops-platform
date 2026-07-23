from enum import Enum


class AccessType(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    DELETE = "delete"
    EXECUTE = "execute"


class ResourceType(str, Enum):
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
