# Agentic AIOps Platform

Production-ready Agentic AI Platform for IT Operations Automation, built with LangGraph, FastAPI, and enterprise-grade architecture.

## Architecture

```
User Request
    |
    v
[Intent Detection Agent] --> Detects intent (Troubleshooting / Low-Risk Access / High-Risk Access)
    |
    v
[Planner Agent] --> Creates execution plan based on intent
    |
    +--> Troubleshooting Path:
    |      [Collect Logs/Metrics] --> [RAG: Search Runbooks/KB] --> [Analyze Root Cause]
    |      --> [Recommend Remediation] --> [Execute or Confirm] --> [Notify] --> [Audit]
    |
    +--> Low-Risk Access Path:
    |      [Policy Engine] --> [Auto-Approve] --> [Execute Tool] --> [Audit] --> [Notify]
    |
    +--> High-Risk Access Path:
           [Policy Engine] --> [Risk Score] --> [Human Approval] --> [Execute Tool] --> [Audit] --> [Notify]
```

## Tech Stack

| Layer            | Technology                              |
|------------------|-----------------------------------------|
| Backend          | FastAPI, Python 3.11                    |
| Agent Framework  | LangGraph + LangChain                   |
| LLM              | OpenAI GPT-4o (swappable)              |
| Database         | PostgreSQL 16                           |
| Cache            | Redis 7                                 |
| Vector DB        | Qdrant                                  |
| Frontend         | React 18 + TypeScript + Tailwind        |
| Observability    | OpenTelemetry + structlog + Prometheus  |
| Auth             | JWT + Azure AD OAuth2 + RBAC            |
| Deployment       | Docker + Kubernetes + Terraform         |
| CI/CD            | GitHub Actions                          |

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- OpenAI API key

### 1. Clone & Configure
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start Infrastructure
```bash
docker-compose up -d postgres redis qdrant
```

### 3. Install Backend Dependencies
```bash
pip install -e ".[dev]"
```

### 4. Run Backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 5. Run Frontend
```bash
cd frontend && npm install && npm run dev
```

### 6. Access
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Metrics: http://localhost:8000/api/v1/metrics

## Project Structure

```
agentic-aiops-platform/
├── backend/
│   └── app/
│       ├── core/              # Config, security, exceptions, middleware
│       ├── domain/            # Entities, enums, interfaces, repositories
│       ├── agents/            # All AI agents + LangGraph workflow
│       │   ├── intent_detection/
│       │   ├── planner/
│       │   ├── troubleshooting/
│       │   ├── rag/
│       │   ├── policy/
│       │   ├── access_management/
│       │   ├── human_approval/
│       │   ├── notification/
│       │   ├── audit/
│       │   ├── memory/
│       │   └── workflow/      # LangGraph state machine
│       ├── tools/             # 11 tool integrations
│       │   ├── azure_ad, okta, servicenow, jira, github
│       │   ├── aws_iam, kubernetes, slack, microsoft_teams
│       │   ├── email, rest_api
│       │   └── base/          # Tool interface + registry
│       ├── rag/               # RAG pipeline
│       │   ├── chunking/
│       │   ├── embeddings/
│       │   ├── vector_store/  # Qdrant
│       │   ├── retrieval/
│       │   └── pipeline/
│       ├── memory/            # 4-tier memory system
│       │   ├── session/       # Redis session memory
│       │   ├── conversation/  # Conversation history
│       │   ├── long_term/     # User preferences/patterns
│       │   └── organizational/# Team knowledge/policies
│       ├── api/               # FastAPI routes + schemas
│       ├── db/                # SQLAlchemy models + session
│       ├── observability/     # Logging, tracing, metrics
│       ├── services/
│       └── utils/
├── frontend/                  # React + TypeScript SPA
├── tests/                     # Unit + integration tests
├── infra/
│   ├── terraform/             # AWS infrastructure
│   └── kubernetes/            # K8s manifests + kustomize
├── .github/workflows/         # CI/CD pipeline
├── scripts/                   # Utility scripts
└── data/                      # Knowledge base documents
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/` | Main chat endpoint |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/access/request` | Create access request |
| GET | `/api/v1/access/pending` | Pending approvals |
| POST | `/api/v1/access/approve/:id` | Approve/reject |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/tools` | List tools |
| GET | `/api/v1/tools/health` | Tool health |

## Security

- JWT authentication with refresh tokens
- RBAC with 8 roles and 14 permissions
- Azure AD OAuth2 integration
- PII masking on all logs
- Encryption at rest (Fernet)
- Rate limiting
- Security headers (HSTS, CSP, X-Frame-Options)
- Prompt injection protection

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=backend/app --cov-report=html

# Linting
ruff check backend/
ruff format --check backend/
```

## Deployment

```bash
# Build image
docker build -t aiops-backend:latest .

# Deploy to K8s
kubectl apply -k infra/kubernetes/overlays/production/

# Infrastructure
cd infra/terraform && terraform apply
```

## Key Design Decisions

1. **LangGraph State Machine**: The entire workflow is a directed graph with typed state, enabling pause/resume for human-in-the-loop
2. **Pluggable LLM**: Abstracted through OpenAI client; swap by changing the provider
3. **Tool Registry**: Common interface for all 11 integrations with health checks
4. **4-Tier Memory**: Session (Redis TTL), Conversation (Redis list), Long-term (Redis hash), Organizational (Redis key patterns)
5. **Risk Engine**: Scored risk evaluation with configurable thresholds for auto-approve, high-risk, and critical
6. **Defense in Depth**: RBAC + encryption + PII masking + audit logging at every layer
