__all__ = [
    "AzureADTool",
    "OktaTool",
    "ServiceNowTool",
    "JiraTool",
    "GitHubTool",
    "AWSIAMTool",
    "KubernetesTool",
    "SlackTool",
    "MicrosoftTeamsTool",
    "EmailTool",
    "RestAPITool",
]


def _lazy_import(name: str):
    import importlib

    _MAP = {
        "AzureADTool": "app.tools.azure_ad.azure_ad_tool",
        "OktaTool": "app.tools.okta.okta_tool",
        "ServiceNowTool": "app.tools.servicenow.servicenow_tool",
        "JiraTool": "app.tools.jira.jira_tool",
        "GitHubTool": "app.tools.github.github_tool",
        "AWSIAMTool": "app.tools.aws_iam.aws_iam_tool",
        "KubernetesTool": "app.tools.kubernetes.k8s_tool",
        "SlackTool": "app.tools.slack.slack_tool",
        "MicrosoftTeamsTool": "app.tools.microsoft_teams.teams_tool",
        "EmailTool": "app.tools.email.email_tool",
        "RestAPITool": "app.tools.rest_api.rest_api_tool",
    }
    if name in _MAP:
        mod = importlib.import_module(_MAP[name])
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str):
    return _lazy_import(name)
