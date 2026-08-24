# Enterprise Agentic AI for IT Operations Automation

## Project Overview

Enterprise Agentic AI for IT Ops is a production-ready, multi-agent AI platform that automates enterprise IT operations. It uses Large Language Models (LLMs) orchestrated through a LangGraph state machine to handle incident response, access management, troubleshooting, and knowledge retrieval — all through a natural language chat interface.

Users type requests in plain English, and the system automatically classifies the intent, creates an execution plan, and routes the work to specialized AI agents that carry out the tasks using real enterprise tools.

---

## How It Works

### 1. User Sends a Message

A user types a request into the React chat interface, such as:

- "My Kubernetes pod is crash looping in production"
- "I need read access to the production database"
- "What's our runbook for handling SSL certificate expiry?"

### 2. Intent Detection

The **IntentDetectionAgent** classifies the message into one of four intent categories:

| Intent | Example |
|--------|---------|
| `troubleshooting` | "Pod is crash looping", "Server is unresponsive" |
| `low_risk_access` | "Need read access to staging logs" |
| `high_risk_access` | "Need admin access to production database" |
| `general_inquiry` | "What's our incident response process?" |

### 3. Planning

The **PlannerAgent** creates a step-by-step execution plan based on the detected intent. It defines which agents to invoke, in what order, and what inputs each agent needs.

### 4. Execution Pipeline

Depending on the intent, different agents are triggered:

**Troubleshooting Flow:**
```
TroubleshootCollect → SearchKnowledge (RAG) → AnalyzeRootCause → ExecuteRemediation → Notify → Audit
```

**Access Request Flow:**
```
PolicyAgent (risk evaluation) → Auto-Approve or RequestApproval → AccessManagementAgent → Notify → Audit
```

**General Inquiry Flow:**
```
SearchKnowledge (RAG) → Notify → Audit
```

### 5. Response Delivered

The final response is streamed back to the user's chat interface, including:
- AI-generated answer with citations from the knowledge base
- Actions taken (access granted, remediation executed, etc.)
- Approval status if human approval was required
- Audit trail of all operations performed

---

## System Architecture

### Backend (Python + FastAPI)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Server | FastAPI + Uvicorn | REST API endpoints |
| Agent Orchestration | LangGraph | State machine managing agent workflows |
| LLM Integration | LangChain + 4 adapters | OpenAI, Anthropic, Gemini, Ollama |
| Database | PostgreSQL 16 | Users, access requests, audit logs, workflows |
| Cache / Memory | Redis 7 | 4-tier memory (session, conversation, long-term, organizational) |
| Vector Database | Qdrant | RAG knowledge base storage and retrieval |
| Auth | JWT + RBAC + Azure AD OAuth | 8 roles, 14 permissions, enterprise SSO |
| Encryption | Fernet (AES) | Secrets and token encryption at rest |
| Observability | structlog + OpenTelemetry + Prometheus | Logging, tracing, metrics |

### Frontend (React + TypeScript)

| Component | Technology |
|-----------|-----------|
| Framework | React 18 with TypeScript |
| Build Tool | Vite 5 |
| Styling | Tailwind CSS 3.4 |
| State Management | Zustand (client) + React Query v5 (server) |
| Icons | Lucide React |
| Markdown Rendering | React Markdown + Syntax Highlighter |

### Infrastructure

| Layer | Technology |
|-------|-----------|
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes + Kustomize |
| Infrastructure as Code | Terraform (AWS: VPC, EKS, RDS, ElastiCache) |
| CI/CD | GitHub Actions (lint, test, build, deploy) |
| Cloud Deployment | GCP Cloud Run, Render.com |

---

## The 10 AI Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **IntentDetectionAgent** | Classifies user messages into intent categories using LLM |
| 2 | **PlannerAgent** | Creates step-by-step execution plans with fallback strategies |
| 3 | **TroubleshootingAgent** | Collects diagnostics, searches knowledge, diagnoses root causes |
| 4 | **RAGAgent** | Searches the knowledge base (runbooks, SOPs, incident reports) via vector search |
| 5 | **PolicyAgent** | Evaluates risk scores with configurable thresholds |
| 6 | **AccessManagementAgent** | Processes access requests and executes grants through enterprise tools |
| 7 | **HumanApprovalAgent** | Creates and manages approval workflows with expiry and notifications |
| 8 | **NotificationAgent** | Sends alerts via Slack, Microsoft Teams, and Email |
| 9 | **AuditAgent** | Logs every action for compliance and security audit trails |
| 10 | **MemoryManager** | Coordinates the 4-tier memory system across Redis |

---

## 11 Enterprise Tool Integrations

All tools share a common `BaseTool` interface with health checks, PII masking, error handling, and structured logging.

| Tool | Category | What It Does |
|------|----------|-------------|
| Azure AD | Identity | User provisioning, group management, access checks |
| Okta | Identity | User lifecycle management, app assignments |
| ServiceNow | ITSM | Incident creation, KB search, change requests |
| Jira | Project Mgmt | Issue tracking, sprint management |
| GitHub | Source Code | Repo access, PR management, code reviews |
| AWS IAM | Cloud IAM | Role/user management, policy attachment |
| Kubernetes | Containers | Pod diagnostics, deployments, events |
| Slack | Communication | Channel messaging, alerts, thread replies |
| Microsoft Teams | Communication | Channel and chat notifications |
| Email | Communication | SMTP-based email notifications |
| REST API | Generic | Custom API integrations |

---

## RAG (Retrieval-Augmented Generation) Pipeline

The RAG system allows the AI to search and reference internal documentation.

```
Documents (runbooks, SOPs, incident reports)
  → DocumentChunker (1000 chars, 200 overlap, sentence-aware splitting)
    → EmbeddingService (OpenAI text-embedding-3-large or Ollama nomic-embed-text)
      → Qdrant Vector Store (COSINE similarity)

User Query
  → EmbeddingService → Qdrant.search (top 5 results, threshold 0.75)
    → LLM generates answer with citations from retrieved context
```

Knowledge base sources live in the `data/` directory:
- `data/runbooks/` — Operational runbooks
- `data/sop/` — Standard operating procedures
- `data/incident_reports/` — Past incident reports
- `data/knowledge_base/` — General IT knowledge

---

## 4-Tier Memory System

| Tier | Storage | TTL | Purpose |
|------|---------|-----|---------|
| **Session** | Redis hash | 1 hour | Current conversation context |
| **Conversation** | Redis list | 24 hours | Full chat history per user |
| **Long-term** | Redis hash | 30 days | User preferences, learned patterns |
| **Organizational** | Redis keys | Permanent | Team policies, common issues, shared knowledge |

---

## Security Features

- **JWT Authentication** — Access tokens (30 min) + refresh tokens (7 days)
- **RBAC** — 8 roles (viewer → super_admin) with 14 cumulative permissions
- **Azure AD OAuth2** — Enterprise SSO with PKCE flow
- **Fernet Encryption** — AES encryption for stored secrets and tokens
- **PII Masking** — Automatic detection and masking of emails, phone numbers, SSNs, credit cards, AWS keys
- **Audit Logging** — Every action logged with user, session, timestamp, risk score
- **Rate Limiting** — Configurable per-minute request limits
- **Security Headers** — X-Frame-Options, X-Content-Type-Options, Referrer-Policy

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/` | Send a message and trigger the agent workflow |
| GET | `/chat/sessions/{id}/history` | Retrieve conversation history |
| POST | `/auth/login` | Email/password login |
| POST | `/auth/register` | User registration |
| GET | `/auth/me` | Current user profile |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/azure-ad/authorize` | Start Azure AD OAuth flow |
| POST | `/access/request` | Create an access request |
| GET | `/access/pending` | List pending approvals |
| POST | `/access/approve/{id}` | Approve or reject a request |
| GET | `/models/` | List available LLM models |
| POST | `/models/override` | Override task-to-model routing |
| GET | `/drive/auth-url` | Get Google Drive OAuth URL |
| POST | `/drive/disconnect` | Disconnect Google Drive |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

---

## LLM Model Routing

The `ModelRouter` intelligently routes different task types to the most appropriate model:

| Task Type | Default Model | Rationale |
|-----------|--------------|-----------|
| Intent Detection | GPT-4o Mini | Fast, cheap classification |
| Planning | GPT-4o | Balanced reasoning |
| Troubleshooting | GPT-4o | Complex analysis |
| RAG Query | GPT-4o | Context-aware generation |
| Policy Evaluation | GPT-4o Mini | Structured risk scoring |
| Compaction | Same as session | Context compression |

Supports **24 pre-configured models** across OpenAI, Anthropic, Google, and Ollama with automatic failover.

---

## Deployment Options

### Docker Compose (Local Development)
5 services: PostgreSQL, Redis, Qdrant, Backend (FastAPI), Frontend (React + Nginx)

### Kubernetes
Kustomize overlays for dev, staging, and production with health probes, resource limits, and Prometheus annotations.

### GCP Cloud Run
Backend and frontend as separate Cloud Run services with Supabase (PostgreSQL), Upstash (Redis), and Qdrant Cloud — estimated $0/month within free tier.

### AWS (Terraform)
Full infrastructure: VPC, EKS cluster, RDS PostgreSQL, ElastiCache Redis, IAM roles.

### Render.com
One-click deployment with free-tier PostgreSQL and Redis.

---

## CI/CD Pipeline

GitHub Actions workflow runs on every push to main/develop:

1. **Lint & Typecheck** — ruff check, ruff format, mypy
2. **Test** — pytest with PostgreSQL + Redis service containers, coverage upload to Codecov
3. **Build & Push** — Docker build + push to GitHub Container Registry
4. **Deploy** — Kubernetes deployment

---

## Running Locally

```bash
# Quick setup
./scripts/setup.sh

# Start all services
./scripts/start-all-docker.sh

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Project Structure

```
agentic-aiops-platform/
├── backend/
│   ├── agents/          # 10 AI agents (intent, planner, troubleshooting, RAG, etc.)
│   ├── api/             # FastAPI routes (chat, auth, access, models, drive)
│   ├── core/            # Config, database, LLM router, memory, security
│   ├── models/          # SQLAlchemy ORM models
│   ├── services/        # Business logic (chat, access, RAG, Google Drive)
│   └── tools/           # 11 enterprise tool integrations
├── frontend/
│   ├── src/
│   │   ├── components/  # UI components (ChatMessage, Sidebar, etc.)
│   │   ├── pages/       # Chat, Dashboard, Access, Approvals
│   │   ├── services/    # API client (Axios)
│   │   └── store/       # Zustand state management
│   └── public/
├── data/                # Knowledge base documents
├── infra/               # Terraform, Kubernetes, Helm
├── scripts/             # Setup, start, stop, lint, ingest scripts
├── tests/               # Unit and integration tests
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── render.yaml
```
