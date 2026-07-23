# Agentic AIOps Platform — Complete Code Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
6. [Backend Deep Dive](#backend-deep-dive)
7. [Frontend Deep Dive](#frontend-deep-dive)
8. [Infrastructure & Deployment](#infrastructure--deployment)
9. [Configuration](#configuration)
10. [API Reference](#api-reference)
11. [Testing](#testing)

---

## Project Overview

A production-ready **Agentic AI Platform for IT Operations Automation**. It uses a multi-agent system with RAG (Retrieval-Augmented Generation), tool integrations, and a React frontend to automate incident response, access management, troubleshooting, and more.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                            │
│              (Chat, Dashboard, Access, Approvals)                │
└──────────────────────────┬───────────────────────────────────────┘
                           │ REST API (port 3000 → 8000 proxy)
┌──────────────────────────▼───────────────────────────────────────┐
│                      FASTAPI BACKEND                              │
│  ┌────────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐ │
│  │ Auth/JWT   │ │  Chat    │ │  Access   │ │ Health/Models    │ │
│  └─────┬──────┘ └────┬─────┘ └─────┬─────┘ └───────┬──────────┘ │
│        └─────────────┼────────────┼────────────────┘             │
│                ┌─────▼────────────▼─────┐                        │
│                │   AIOpsWorkflow (LCG)  │                        │
│                │   10 AI Agents         │                        │
│                └─────┬────────────┬─────┘                        │
│           ┌──────────┤            ├──────────┐                    │
│    ┌──────▼──┐ ┌─────▼────┐ ┌────▼──────┐ ┌─▼──────────┐       │
│    │LLM Router│ │RAG Pipeline│ │Tool Reg  │ │Memory System│       │
│    │4 Providers│ │Qdrant    │ │11 Tools  │ │4-Tier       │       │
│    └─────────┘ └──────────┘ └──────────┘ └────────────┘       │
└──────────────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
    │ PostgreSQL  │     │   Redis     │     │   Qdrant    │
    │   (port 5432)│     │ (port 6379) │     │ (port 6333) │
    └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Python 3.11+) |
| LLM Adapters | OpenAI, Anthropic, Google Gemini, Ollama |
| Agent Orchestration | LangGraph (state machine) |
| Vector Store | Qdrant |
| Database | PostgreSQL 16 (SQLAlchemy async) |
| Cache/Memory | Redis |
| Auth | JWT + RBAC + Azure AD OAuth2 |
| Observability | structlog + OpenTelemetry + Prometheus |
| Encryption | Fernet (AES-128-CBC) |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + TypeScript |
| Styling | Tailwind CSS 3.4 |
| State | Zustand + React Query |
| HTTP Client | Axios |
| Icons | Lucide React |
| Build Tool | Vite 5 |
| Markdown | React Markdown |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containers | Docker + Docker Compose |
| Orchestration | Kubernetes + Kustomize |
| IaC | Terraform (AWS) |
| CI/CD | GitHub Actions |
| Reverse Proxy | Nginx |

---

## Project Structure

```
agentic-aiops-platform/
├── backend/                    # Python FastAPI backend
│   └── app/
│       ├── main.py             # App entry point, middleware, startup
│       ├── agents/             # 10 AI agents + workflow orchestrator
│       ├── api/                # Routes, schemas, dependencies
│       ├── core/               # Config, LLM, security, middleware
│       ├── db/                 # SQLAlchemy models, session management
│       ├── domain/             # Entities, enums, interfaces (DDD)
│       ├── memory/             # 4-tier memory system
│       ├── observability/      # Logging, tracing, metrics
│       ├── rag/                # RAG pipeline (chunking, retrieval, vector store)
│       ├── services/           # Business logic services
│       └── tools/              # 11 integration tools
├── frontend/                   # React TypeScript frontend
│   └── src/
│       ├── App.tsx             # Route definitions
│       ├── main.tsx            # App entry point
│       ├── components/         # Layout, Sidebar
│       ├── pages/              # Chat, Dashboard, Access, Approvals
│       ├── services/           # Axios API client
│       ├── store/              # Zustand state store
│       └── types/              # TypeScript interfaces
├── infra/                      # Infrastructure as Code
│   ├── kubernetes/             # K8s manifests + Kustomize overlays
│   └── terraform/              # AWS Terraform modules
├── tests/                      # Unit + integration tests
├── scripts/                    # Setup, dev, and deployment scripts
├── data/                       # Knowledge base, runbooks, SOPs
├── docker-compose.yml          # Local dev orchestration
├── pyproject.toml              # Python project config
└── .github/workflows/          # CI/CD pipeline
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Homebrew (macOS)

### 1. Clone & Setup

```bash
cd /path/to/agentic-aiops-platform

# Backend setup
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Frontend setup
cd frontend
npm install
cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys (or leave defaults for local dev)
```

### 3. Start Infrastructure

```bash
docker compose up -d postgres redis qdrant
```

### 4. Start Backend (Terminal 1)

```bash
cd backend
source ../venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### 5. Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

### 6. Open Browser

- **Frontend UI**: http://localhost:3000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

---

## Backend Deep Dive

### Entry Point — `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config.settings import settings
from app.observability.logging import setup_logging
from app.observability.tracing import setup_tracing
from app.observability.metrics import setup_metrics

# Initialize observability
setup_logging(log_level="DEBUG" if settings.app_debug else "INFO")
setup_tracing()
setup_metrics()

app = FastAPI(
    title="Agentic AIOps Platform",
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
from app.api.routes import auth, chat, access, health, models
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(access.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")

# Startup: init DB, register tools, ensure Qdrant collection
@app.on_event("startup")
async def startup():
    from app.db.session import init_db
    from app.tools.base.tool_registry import get_tool_registry
    await init_db()
    registry = get_tool_registry()
    # Lazy-load tools (resilient to missing optional deps)
    for cls_name, module_path in tool_classes:
        try:
            mod = importlib.import_module(module_path)
            registry.register(getattr(mod, cls_name)())
        except Exception as e:
            print(f"Warning: Could not load tool {cls_name}: {e}")
```

### Configuration — `backend/app/core/config/settings.py`

Uses `pydantic-settings` to load from `.env` file:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", case_sensitive=False, extra="ignore")

    # Required fields
    app_secret_key: str = Field(..., min_length=16)
    database_url: str          # PostgreSQL async URL
    jwt_secret_key: str = Field(..., min_length=16)
    encryption_key: str

    # Optional with defaults
    app_env: Literal["development", "staging", "production"] = "development"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    cors_origins: list[str] = ["http://localhost:3000"]
```

### 10 AI Agents

| Agent | File | Purpose |
|-------|------|---------|
| IntentDetectionAgent | `agents/intent_detection/` | Classifies user intent (incident, access, query, etc.) |
| PlannerAgent | `agents/planner/` | Creates step-by-step execution plans |
| TroubleshootingAgent | `agents/troubleshooting/` | Diagnoses issues using tools + knowledge base |
| RAGAgent | `agents/rag/` | Retrieves relevant docs from vector store |
| PolicyAgent | `agents/policy/` | Enforces RBAC, risk assessment, compliance |
| AccessManagementAgent | `agents/access_management/` | Handles access request lifecycle |
| HumanApprovalAgent | `agents/human_approval/` | Routes high-risk actions for human review |
| NotificationAgent | `agents/notification/` | Sends alerts via Slack/Teams/Email |
| AuditAgent | `agents/audit/` | Logs all actions for compliance |
| MemoryManager | `agents/memory/` | Manages conversation + organizational memory |

### Workflow Orchestrator — `aiops_workflow.py`

Uses **LangGraph** to define a state machine:

```
START → IntentDetection → [branch based on intent]
  ├── incident → Planner → Troubleshooting → Audit → END
  ├── access_request → Policy → AccessManagement → Audit → END
  ├── query → RAG → Audit → END
  ├── approval_needed → HumanApproval → Audit → END
  └── notification → Notification → Audit → END
```

### LLM Router — `core/llm/router.py`

Routes tasks to the best LLM provider:

| Task | Default Model | Fallback |
|------|--------------|----------|
| Chat | gpt-4o | claude-3-opus |
| Intent | gpt-4o-mini | claude-3-haiku |
| Planning | gpt-4o | claude-3-opus |
| Troubleshooting | gpt-4o | gemini-pro |
| Embeddings | text-embedding-3-large | ollama-nomic |

4 Adapters in `core/llm/adapters/`:
- **OpenAIAdapter** — GPT-4o, GPT-4o-mini, embeddings
- **AnthropicAdapter** — Claude 3 Opus/Sonnet/Haiku
- **GeminiAdapter** — Google Gemini Pro
- **OllamaAdapter** — Self-hosted (llama3, mistral, nomic-embed)

### 11 Integration Tools

| Tool | Category | What It Does |
|------|----------|-------------|
| AzureADTool | Identity | User/group management, app registrations |
| OktaTool | Identity | SSO, MFA, user lifecycle |
| ServiceNowTool | ITSM | Incident/Change/Problem management |
| JiraTool | Project Mgmt | Issue CRUD, sprint management |
| GitHubTool | SCM | Repo, PR, issue, workflow management |
| AWSIAMTool | Cloud | IAM users, roles, policies |
| KubernetesTool | Containers | Pod/deployment/service management |
| SlackTool | Communication | Channel messages, bot interactions |
| MicrosoftTeamsTool | Communication | Team messages, card notifications |
| EmailTool | Communication | SMTP email sending |
| RestAPITool | Integration | Generic REST API calls |

### RAG Pipeline — `rag/`

```
Document → DocumentChunker → EmbeddingService → QdrantVectorStore
                                                        │
User Query → Retriever (hybrid search) ←────────────────┘
                  │
                  ▼
         RAGPipeline (context + citations)
```

- **DocumentChunker**: Splits docs into 512-token chunks with 50-token overlap
- **EmbeddingService**: Routes to OpenAI or Ollama embeddings
- **QdrantStore**: Stores/retrieves vectors with metadata
- **Retriever**: Hybrid semantic + keyword search with MMR

### Memory System — `memory/`

| Tier | Storage | TTL | What It Stores |
|------|---------|-----|----------------|
| Session Memory | Redis | 30 min | Current conversation context |
| Conversation Memory | Redis | 24 hours | Full chat history per session |
| Long-term Memory | Redis | 30 days | User preferences, past resolutions |
| Organizational Memory | Redis | Permanent | Team patterns, common issues, runbooks |

### Security — `core/security/`

- **JWT**: Access tokens (30min) + Refresh tokens (7 days), RS256/HS256
- **RBAC**: 8 roles (admin, ops_engineer, security_analyst, etc.) × 14 permissions
- **OAuth2**: Azure AD integration with PKCE flow
- **Encryption**: Fernet symmetric encryption for secrets + PII masking

### Database — `db/`

7 SQLAlchemy models:

| Model | Table | Key Fields |
|-------|-------|-----------|
| User | users | id, email, role, departments, permissions |
| Incident | incidents | id, title, severity, status, assigned_to |
| AccessRequest | access_requests | id, resource_type, risk_level, status |
| Approval | approvals | id, request_id, decision, risk_score |
| AuditLog | audit_logs | id, action, agent, timestamp, details |
| Knowledge | knowledge | id, title, content, category, embedding_id |
| Workflow | workflows | id, intent, plan, status, steps |

---

## Frontend Deep Dive

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Chat | `/chat` | AI assistant chat interface with markdown rendering |
| Dashboard | `/dashboard` | System stats, tool health, active sessions |
| Access Requests | `/access` | Request access with risk assessment |
| Approvals | `/approvals` | Review/approve pending access requests |

### State Management

**Zustand Store** (`store/index.ts`):
```typescript
interface AppState {
  user: User | null;
  messages: ChatMessage[];
  sessionId: string | null;
  isLoading: boolean;
  sidebarOpen: boolean;
  // + setters
}
```

**React Query**: Server state for API data (tools list, health, approvals).

### API Client (`services/api.ts`)

Axios instance with:
- Base URL: `/api/v1` (proxied to backend via Vite)
- Auth interceptor: Adds Bearer token from localStorage
- 401 interceptor: Redirects to `/login`

### Design System (CSS Variables)

```css
--bg-primary: #000000;       /* Pure black background */
--accent: #ff4d00;           /* Orange (Nike-inspired) */
--success: #00d26a;          /* Green for positive states */
--warning: #ffc107;          /* Yellow for caution */
--error: #ff3b3b;            /* Red for errors */
--gradient-1: linear-gradient(135deg, #ff4d00, #ff8a00);  /* Brand gradient */
```

Reusable CSS classes:
- `.glass-card` — Glassmorphism card with hover lift effect
- `.btn-primary` — Orange gradient button with hover glow
- `.btn-ghost` — Transparent outlined button
- `.input-field` — Dark input with focus glow
- `.select-field` — Custom styled select dropdown

---

## Infrastructure & Deployment

### Docker Compose (Local Dev)

```yaml
services:
  postgres:    # PostgreSQL 16 → port 5432
  redis:       # Redis 7 → port 6379
  qdrant:      # Qdrant vector DB → port 6333-6334
  backend:     # FastAPI app → port 8000
  frontend:    # React app → port 3000
```

### Kubernetes

- `infra/kubernetes/base/` — Base manifests (Deployment, Service, ConfigMap, Secrets)
- `infra/kubernetes/overlays/dev/` — Development overrides
- `infra/kubernetes/overlays/staging/` — Staging overrides
- `infra/kubernetes/overlays/production/` — Production overrides

### Terraform (AWS)

6 modules:
- **VPC** — 3-tier networking (public, private, data)
- **EKS** — Managed Kubernetes cluster
- **RDS** — PostgreSQL with Multi-AZ
- **ElastiCache** — Redis cluster
- **IAM** — Service roles and policies
- **Qdrant** — EC2-hosted vector DB

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci-cd.yaml
Jobs:
  lint:        # ruff, mypy, eslint
  test:        # pytest, jest
  build:       # docker build
  deploy-dev:  # auto on main branch
  deploy-prod: # manual approval gate
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Core
APP_SECRET_KEY=mysupersecretkey12345
DATABASE_URL=postgresql+asyncpg://aiops:aiops_secret@localhost:5432/aiops_db
JWT_SECRET_KEY=myjwtsecretkey12345678901234
ENCRYPTION_KEY=myencryptionkey123456789012345678

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# LLM Providers (set at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
OLLAMA_BASE_URL=http://localhost:11434

# Integrations
SERVICENOW_URL=https://your-instance.service-now.com
JIRA_URL=https://your-org.atlassian.net
GITHUB_TOKEN=ghp_...
SLACK_BOT_TOKEN=xoxb-...
```

---

## API Reference

All endpoints are prefixed with `/api/v1`:

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/tools` | List registered tools |
| GET | `/tools/health` | Tool health status |
| GET | `/metrics` | Prometheus metrics |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Email/password login |
| GET | `/auth/me` | Get current user |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/azure-ad/authorize` | Azure AD OAuth start |
| POST | `/auth/azure-ad/callback` | Azure AD OAuth callback |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/` | Send message to AI assistant |
| GET | `/chat/sessions/{id}/history` | Get session chat history |

### Access Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/access/request` | Create access request |
| GET | `/access/pending` | List pending approvals |
| POST | `/access/approve/{id}` | Approve/reject request |

### Model Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models/` | List available models |
| GET | `/models/health` | Model provider health |
| GET | `/models/embeddings` | List embedding models |
| POST | `/models/override` | Override task→model mapping |
| GET | `/models/routing` | Get routing configuration |

### Schemas

**ChatRequest**:
```json
{
  "message": "string (1-5000 chars)",
  "session_id": "string | null",
  "context": {},
  "channels": ["slack", "teams"]
}
```

**ChatResponse**:
```json
{
  "session_id": "uuid",
  "response": "AI response text",
  "intent": "incident | access_request | query | ...",
  "status": "completed | requires_approval | error",
  "citations": [{"index": 1, "title": "...", "source": "..."}],
  "requires_approval": false,
  "approval_id": null
}
```

**AccessRequestCreate**:
```json
{
  "resource_type": "jira | github | aws_iam | ...",
  "resource_identifier": "PROJECT-123",
  "access_type": "read | write | admin",
  "justification": "Business reason",
  "duration_hours": 8
}
```

---

## Testing

### Run Tests

```bash
# All tests
pytest

# Unit only
pytest tests/unit/

# Integration only
pytest tests/integration/

# With coverage
pytest --cov=backend/app --cov-report=html
```

### Test Structure

```
tests/
├── unit/
│   ├── agents/           # Intent, policy, approval, audit agent tests
│   ├── api/              # JWT, encryption, model router tests
│   └── tools/            # Tool registry tests
└── integration/
    ├── agents/           # End-to-end agent tests
    ├── api/              # API endpoint tests
    └── rag/              # RAG pipeline tests
```

### Linting

```bash
# Backend
ruff check backend/
mypy backend/

# Frontend
cd frontend && npm run lint
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.sh` | One-command full setup |
| `scripts/start-dev.sh` | Start backend + frontend |
| `scripts/start-all-docker.sh` | Start all Docker services |
| `scripts/stop.sh` | Stop all services |
| `scripts/lint-and-test.sh` | Run linters + tests |
| `scripts/ingest-knowledge.sh` | Ingest docs into RAG |
