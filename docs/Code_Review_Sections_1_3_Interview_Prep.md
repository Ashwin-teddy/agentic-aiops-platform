# Code Walkthrough & Interview Prep — Agentic AIOps Platform

**Sections 1-3 explained line-by-line (beginner-friendly) + Interview Q&A bank**

---

## SECTION 1: `main.py` — The Front Door

**File:** `backend/app/main.py` (84 lines)

```
Line 1: from fastapi import FastAPI      ← Import the app builder
Line 2: ...CORSMiddleware                ← Bouncer (who's allowed to talk)
Line 3: ...TrustedHostMiddleware          ← Doorman (domain check)
Line 5: from app.core.config.settings import settings   ← Master control panel

Line 6-8:  setup_logging, setup_metrics, setup_tracing  ← Dashboard imports
Line 10-12: Turn on the dashboard (logging + tracing + metrics)

Line 14-20: app = FastAPI(title=..., version=..., docs_url=...)
            ← Create the app; hide /docs in production

Line 22-28: app.add_middleware(CORSMiddleware, allow_origins=[...])
            ← "Let my frontend talk to me"

Line 30-31: if production: add TrustedHostMiddleware
            ← Only guard domains in production

Line 33-40: app.include_router(auth.router, prefix="/api/v1")
            ← Register all 6 departments (auth, chat, access, health, models, drive)

Line 43-77: @app.on_event("startup")  ← On start:
                - Connect DB (init_db)
                - Load ALL 11 tools (Jira, Slack, AWS, GitHub...)
                - Connect Qdrant & ensure collection

Line 80-84: @app.on_event("shutdown") ← On stop: close DB
```

**Flow:** `Import → Dashboard ON → Create app → Guards → Routes → Startup prep → Ready to serve`

### Key concepts in main.py

| Line(s) | Concept | Simple meaning |
|---------|---------|----------------|
| 1 | FastAPI class | The web framework - "the building" |
| 2 | CORS Middleware | Security guard letting frontend talk to backend |
| 3 | TrustedHost Middleware | Only checks domains in production |
| 5 | settings object | Master control panel (one source of truth) |
| 6-8 | Observability | Logging (diary), Metrics (speedometer), Tracing (GPS) |
| 10 | log_level | DEBUG (write everything) vs INFO (important only) |
| 14-20 | FastAPI() creation | Create app with name, version, docs |
| 18-19 | docs_url/redoc_url | Show docs in dev, hide in production |
| 24 | allow_origins | Which frontend domains are allowed |
| 35-40 | include_router | Register API departments with /api/v1 prefix |
| 43 | on_event startup | What happens when app starts |
| 49 | init_db | Connect to PostgreSQL, create tables |
| 51-71 | Load 11 tools | Jira, Slack, AWS, GitHub, Okta, etc. |
| 73-77 | Qdrant setup | Connect vector database |

---

## SECTION 2: `settings.py` — The Control Panel

**File:** `backend/app/core/config/settings.py` (149 lines)

**Purpose:** Collects ALL configuration (API keys, URLs, ports) in ONE place. Every other file reads from here — change once, updates everywhere.

### Structure

| Line Range | What it configures |
|-----------|-------------------|
| 10-16 | Reads `.env` file automatically |
| 18-25 | App name, version, port, secret key |
| 27-37 | Databases (PostgreSQL, Redis, Qdrant) |
| 39-48 | LLM providers (OpenAI, Anthropic, Google, Cohere, Ollama) |
| 50-60 | Google OAuth + default models (llama3.2 via Ollama) |
| 62-70 | JWT secret/expiry + Azure AD |
| 72-105 | Tool credentials (Okta, ServiceNow, Jira, GitHub, AWS, K8s, Slack, Teams, Email) |
| 107-124 | Monitoring (OTEL, Prometheus) + risk thresholds |
| 126-141 | Helper functions (is_production, sync URL) |
| 144-149 | Singleton (create settings once, reuse everywhere) |

### Key concepts

- **`Field(..., min_length=16)`** — required value; app fails to start if missing (fail fast = secure)
- **`model_config`** — tells pydantic to read `.env` for values
- **`@property is_production`** — shortcut used in main.py
- **`@lru_cache` + `settings = get_settings()`** — singleton pattern

### Risk thresholds (important for interviews)

```
auto_approve_threshold = 0.3   → Risk below 0.3 = auto approved
high_risk_threshold = 0.7      → Risk above 0.7 = high risk
critical_risk_threshold = 0.9  → Risk above 0.9 = critical
```

---

## SECTION 3: `auth.py` — Login & Register

**File:** `backend/app/api/routes/auth.py` (143 lines)

**Purpose:** Handles everything about **who you are** — login, register, refresh token, Microsoft login, and "who am I."

### Endpoints

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/api/v1/auth/login` | POST | Email + password → JWT tokens |
| `/api/v1/auth/register` | POST | Create account → JWT tokens |
| `/api/v1/auth/azure-ad/authorize` | GET | URL for Microsoft login |
| `/api/v1/auth/azure-ad/callback` | POST | Microsoft code → JWT tokens |
| `/api/v1/auth/me` | GET | My profile (needs valid token) |
| `/api/v1/auth/refresh` | POST | Refresh token → new tokens |

### Login flow (lines 31-55)

1. Log the login attempt
2. Search user by email in DB
3. User not found → 401 (same message as wrong password - prevents account enumeration)
4. Verify password with `bcrypt.checkpw`
5. Wrong password → 401
6. Correct → create JWT token pair, return it

### Register flow (lines 58-86)

1. Check email already exists → 409 Conflict
2. Create user with UUID id + bcrypt-hashed password + role "user"
3. Save to DB, create tokens, return

### Security notes for interviews

- **Same error message** for "user not found" and "wrong password" → prevents account enumeration
- **bcrypt.checkpw** — slow by design, harder to brute force
- **bcrypt.gensalt()** — random salt per user → same password, different hash
- `@router.get("/me")` uses `Depends(get_current_user)` → verifies JWT before returning profile

---

## INTERVIEW Q&A BANK

### Project Questions

**Q: Walk me through your project.**
A: I built an AI system that automates IT operations. It uses LangGraph to coordinate 11 specialized agents in a 12-step workflow. When a user reports an issue or requests access, the system detects intent, plans actions, searches a knowledge base using RAG on Qdrant, evaluates risk, and either auto-completes or routes to a human approver. Backend is FastAPI, frontend React, with PostgreSQL, Redis, and Qdrant.

**Q: Why LangGraph?**
A: LangGraph gives structured state management and checkpoints. Each node is one agent with a single responsibility, and it supports pausing workflows for human approval and resuming later — exactly what I needed for high-risk access requests.

**Q: How does human-in-the-loop approval work?**
A: A policy agent evaluates risk. Below 0.3 risk auto-approves. Above 0.7 requires human approval. The workflow pauses, an approver reviews the request, and the workflow resumes with the decision. No high-risk action happens automatically.

**Q: What is RAG and how did you use it?**
A: RAG is Retrieval-Augmented Generation — giving the AI relevant documents before it answers. I store past incident solutions as embeddings in Qdrant. On a new issue, I search for similar past incidents, get the top 5, and pass them as context. This grounds answers in real data and prevents hallucination.

**Q: What security issues did you find in the code review?**
A: Passwords were SHA-256 hashed without salt — trivial to brute force — so I migrated to bcrypt. Workflow nodes had no error handling, so I added try/except everywhere. The frontend rendered markdown without sanitization, so I added rehype-sanitize. These were real fixes from a proper code review.

### JWT / Auth Questions

**Q: What is JWT and how does it work?**
A: JWT is a token proving identity. It has 3 parts: header, payload, signature. On login, the server signs it with a secret. The client sends it in the Authorization header. The server verifies the signature and grants access. My access tokens expire in 30 minutes, refresh in 7 days.

**Q: Why bcrypt over SHA-256?**
A: SHA-256 is fast and unsalted — hackers can brute-force millions of passwords a second. bcrypt is deliberately slow and uses a random salt per-password, making rainbow-table attacks impractical.

**Q: Why same error for "user not found" and "wrong password"?**
A: To prevent account enumeration. If errors differ, attackers can discover which emails are registered by testing responses.

### Database Questions

**Q: PostgreSQL vs Redis?**
A: PostgreSQL is relational and permanent — users, requests, audit logs. Redis is in-memory and fast — session memory and temporary state. If it's important and must survive restarts, it goes in PostgreSQL. If it needs to be fast and temporary, Redis.

**Q: What's an index?**
A: An index speeds up lookups, like a book's table of contents. My login query runs WHERE email = ? — an index on email makes that instant even with millions of rows.

### RAG / Vector Database Questions

**Q: What is an embedding?**
A: It's converting text into a list of numbers that captures meaning. Related texts have close vectors. 'Server down' and 'server outage' are close; 'server down' and 'morning coffee' are far. Qdrant finds the closest vectors to your query.

**Q: What are the tradeoffs of RAG vs fine-tuning?**
A: RAG is dynamic — you can update the knowledge base without retraining, and responses are grounded in real docs. Fine-tuning changes the model's behavior/tonality but doesn't add new facts and requires retraining. For IT operations, RAG is the right choice.

### Frontend Questions

**Q: What is Zustand?**
A: A React state management library. Components read/write a shared store instead of passing props through many layers. My chat components share messages through one store, and only components that use a specific slice re-render when it changes.

**Q: What is CORS?**
A: Browser security rule blocking requests between different origins. My frontend runs on :3001, backend on :8000. CORS middleware tells the browser to allow those requests.

### Debugging Questions

**Q: Hardest bug you fixed?**
A: After running an auto-formatter, the backend wouldn't start — SQLAlchemy models failed with "Could not de-stringify annotation 'datetime'". The formatter moved datetime into TYPE_CHECKING, but SQLAlchemy evaluates annotations at runtime, so it broke. I moved the imports back and verified all 60+ tests pass.

**Q: How do you debug?**
A: Read the error trace, check the logs first, reproduce locally, isolate the smallest failing piece, then fix and verify with tests.

---

## Skills Summary (from resume)

| Category | Skills |
|----------|--------|
| Languages | Python, JavaScript, TypeScript, SQL |
| AI / Gen AI | LangGraph, LangChain, LLM APIs (OpenAI, Anthropic, Gemini), RAG, Vector Databases (Qdrant), Prompt Engineering, AI Agents |
| Frameworks | FastAPI, React, Zustand |
| Databases | PostgreSQL, Redis |
| DevOps / Tools | Docker, Kubernetes (basics), Git/GitHub, REST APIs |
| Testing | pytest, Unit Testing |
| Others | JWT Auth, RBAC, IT Operations, Incident Management, Access Management |