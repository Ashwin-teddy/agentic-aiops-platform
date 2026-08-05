from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config.settings import settings
from app.observability.logging import setup_logging
from app.observability.tracing import setup_tracing
from app.observability.metrics import setup_metrics

setup_logging(log_level="DEBUG" if settings.app_debug else "INFO")
setup_tracing()
setup_metrics()

app = FastAPI(
    title="Agentic AIOps Platform",
    description="Production-ready Agentic AI Platform for IT Operations Automation",
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

from app.api.routes import auth, chat, access, health, models

app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(access.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")


@app.on_event("startup")
async def startup() -> None:
    from app.db.session import init_db
    from app.tools.base.tool_registry import get_tool_registry
    from app.rag.vector_store.qdrant_store import QdrantVectorStore

    await init_db()
    registry = get_tool_registry()
    tool_classes = [
        ("AzureADTool", "app.tools.azure_ad.azure_ad_tool"),
        ("OktaTool", "app.tools.okta.okta_tool"),
        ("ServiceNowTool", "app.tools.servicenow.servicenow_tool"),
        ("JiraTool", "app.tools.jira.jira_tool"),
        ("GitHubTool", "app.tools.github.github_tool"),
        ("AWSIAMTool", "app.tools.aws_iam.aws_iam_tool"),
        ("KubernetesTool", "app.tools.kubernetes.k8s_tool"),
        ("SlackTool", "app.tools.slack.slack_tool"),
        ("MicrosoftTeamsTool", "app.tools.microsoft_teams.teams_tool"),
        ("EmailTool", "app.tools.email.email_tool"),
        ("RestAPITool", "app.tools.rest_api.rest_api_tool"),
    ]
    import importlib
    for cls_name, module_path in tool_classes:
        try:
            mod = importlib.import_module(module_path)
            registry.register(getattr(mod, cls_name)())
        except Exception as e:
            print(f"Warning: Could not load tool {cls_name}: {e}")

    try:
        qdrant = QdrantVectorStore()
        await qdrant.ensure_collection()
    except Exception as e:
        print(f"Warning: Qdrant initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown() -> None:
    from app.db.session import close_db
    await close_db()
