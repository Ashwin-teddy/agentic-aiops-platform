# Code Review Report - Enterprise Agentic AI for IT Ops

**Date:** August 20, 2026
**Reviewer:** AI Code Review
**Overall Score:** 6/10
**Verification:** All findings verified against source code on August 20, 2026

---

## Summary by Area

| Area | Score | Key Issue |
|------|-------|-----------|
| Backend Agents | 7/10 | In-memory audit/approvals, no error handling in workflow nodes |
| Backend Tools & API | 6.5/10 | SHA-256 passwords, SSRF in REST tool, no CSRF validation |
| Frontend | 6.5/10 | XSS via ReactMarkdown, `any` types, no accessibility |
| Infrastructure | 4.5/10 | Real creds in .env, root containers, empty Terraform modules |

---

## CRITICAL ISSUES (Must Fix Before Interview)

### C1. Passwords hashed with bare SHA-256 (no salt)
**File:** `backend/app/api/routes/auth.py:32` (login) and `:59` (register)
**Issue:** Uses `hashlib.sha256(password.encode()).hexdigest()` — unsalted, trivially brute-forced. No bcrypt/argon2 anywhere in the codebase.
**Fix:** Use `bcrypt` or `argon2`.

### C2. SSRF in REST API tool
**File:** `backend/app/tools/rest_api/rest_api_tool.py:30-39`
**Issue:** Accepts any URL and makes server-side requests. No URL allowlist, no blocking of internal/private IPs (127.0.0.0/8, 10.0.0.0/8, 169.254.0.0/16). Attacker could scan internal networks or access cloud metadata.
**Fix:** Add URL validation, block private IPs.

### C3. XSS via ReactMarkdown
**File:** `frontend/src/pages/ChatPage.tsx:153`
**Issue:** `<ReactMarkdown>{msg.content}</ReactMarkdown>` — no explicit sanitization. Note: react-markdown escapes raw HTML by default unless `rehype-raw` is added (it isn't), so severity is lower than initially assessed. However, adding `rehype-sanitize` is still recommended as defense-in-depth.
**Fix:** Install `rehype-sanitize` and wrap the markdown renderer.

### C4. No error handling in workflow nodes
**File:** `backend/app/agents/workflow/aiops_workflow.py`
**Issue:** No node catches exceptions. If any agent call raises (LLM timeout, tool failure), entire LangGraph execution crashes.
**Fix:** Wrap each node in try/except, set `error` in state, route to fallback.

### C5. Audit logs stored in-memory only
**File:** `backend/app/agents/audit/audit_agent.py`
**Issue:** `self.audit_logs: list[dict[str, Any]] = []` — all audit data lost on restart.
**Fix:** Persist to database or external log store.

### C6. Human approval state in-memory only
**File:** `backend/app/agents/human_approval/approval_agent.py`
**Issue:** `self.pending_approvals: dict[str, dict[str, Any]] = {}` — pending approvals lost on restart.
**Fix:** Persist to database/Redis.

### C7. OAuth state not validated (CSRF)
**File:** `backend/app/api/routes/drive.py` and `auth.py`
**Issue:** Google Drive callback accepts `state` directly as `user_id` with no CSRF validation. Azure AD creates state but never checks it.
**Fix:** Store state server-side, validate on callback.

### C8. Teams notification is a no-op stub
**File:** `backend/app/agents/notification/notification_agent.py`
**Issue:** `_send_teams` fetches tool but never calls `safe_execute`, always returns `True`.
**Fix:** Implement or return `False` with warning.

### C9. AccessManagementAgent.revoke_access doesn't revoke
**File:** `backend/app/agents/access_management/access_agent.py`
**Issue:** Logs "access_revoked" and returns success but never calls any tool.
**Fix:** Actually call the tool's revoke method, or raise NotImplementedError.

### C10. PII masking is a no-op
**File:** `backend/app/tools/base/tool_interface.py`
**Issue:** `mask_pii(str(v))` is called but `sanitized_kwargs` is never used — original `kwargs` passed to `execute()`.
**Fix:** Use the masked kwargs.

---

## WARNING ISSUES (Should Fix)

### W1. `catch (err: any)` in frontend
**File:** `frontend/src/pages/ChatPage.tsx`, `LoginPage.tsx`
**Fix:** Use `catch (err: unknown)` and narrow type.

### W2. Untyped API responses
**File:** `frontend/src/services/api.ts`
**Issue:** All functions return `Promise<AxiosResponse<any>>`.
**Fix:** Add response generics.

### W3. Zustand store fully destructured
**File:** `frontend/src/pages/ChatPage.tsx`
**Issue:** `const { messages, addMessage, ... } = useAppStore()` subscribes to every store change.
**Fix:** Use individual selectors.

### W4. No input validation on agents
**Files:** All agent files
**Issue:** Empty strings, None values propagate silently.

### W5. Unused imports across multiple files
**Files:** `access_management/access_agent.py`, `policy/policy_agent.py`

### W6. Inconsistent return type hints
**Files:** `intent_detection/intent_agent.py`, `rag/rag_agent.py`, `planner/planner_agent.py`

### W7. Dead code in policy agent
**File:** `backend/app/agents/policy/policy_agent.py`
**Issue:** `if policy.get("max_duration_hours"): pass` — does nothing.

### W8. No docstrings on any agent class
**Files:** All 11 agent files.

### W9. Session memory has race conditions
**File:** `backend/app/memory/session/session_memory.py`
**Issue:** `add_message` does read-modify-write on Redis without locking.

### W10. No rate limiting applied
**File:** `backend/app/api/routes/auth.py`
**Issue:** `settings.rate_limit_per_minute` exists but is never used.

### W11. K8s deployment uses `latest` tag
**File:** `infra/kubernetes/base/deployments/backend.yaml`
**Fix:** Use SHA-pinned tags.

### W12. mypy silenced in CI
**File:** `.github/workflows/ci-cd.yaml`
**Issue:** `mypy ... || true` — type failures ignored.

### W13. No `.dockerignore` in project
**Issue:** No `.dockerignore` exists in `agentic-aiops-platform/`. Build context includes `.git/`, `venv/`, `node_modules/`, `data/`, `tests/`.

### W14. Docker runs as root
**Files:** `Dockerfile`, `Dockerfile.backend` (note: these are byte-identical duplicates)
**Fix:** Add non-root user.

### W15. Terraform modules are empty and broken
**Files:** `infra/terraform/modules/` — all 6 directories (eks, elasticache, iam, qdrant, rds, vpc) contain zero files. `main.tf` references 5 of them, so `terraform plan` would fail outright.

---

## NICE-TO-HAVE

1. Lazy imports in `__init__.py` but eager in workflow
2. RAG agent has redundant retrieval
3. NotificationAgent returns inconsistent shapes
4. MemoryManager `get_full_context` does sequential awaits (use `asyncio.gather`)
5. Hardcoded Slack channel names
6. No code splitting / lazy loading in frontend
7. Monolithic ChatPage should be decomposed
8. No `React.memo` on message items
9. No error boundaries
10. No accessibility (aria-labels, label associations)
11. No dark mode
12. No HorizontalPodAutoscaler in K8s
13. No PodDisruptionBudget
14. No Ingress resource
15. No NetworkPolicy

---

## Top 10 Priority Fixes

| # | Issue | File | Fix Time |
|---|-------|------|----------|
| 1 | SHA-256 passwords -> bcrypt | `auth.py` | 15 min |
| 2 | SSRF in REST tool | `rest_api_tool.py` | 15 min |
| 3 | XSS via ReactMarkdown | `ChatPage.tsx` | 5 min |
| 4 | Error handling in workflow nodes | `aiops_workflow.py` | 30 min |
| 5 | Audit logs -> database | `audit_agent.py` | 30 min |
| 6 | OAuth state validation | `drive.py`, `auth.py` | 20 min |
| 7 | Fix Teams stub | `notification_agent.py` | 5 min |
| 8 | Fix `any` types in frontend | `ChatPage.tsx`, `LoginPage.tsx` | 10 min |
| 9 | Add .dockerignore | root | 5 min |
| 10 | Non-root Docker user | `Dockerfile` | 5 min |

---

## Backend Agents Scorecard

| Agent | Score | Key Issue |
|-------|-------|-----------|
| IntentDetectionAgent | 7/10 | Prompt injection risk, missing type hints |
| PlannerAgent | 7/10 | Opaque JSONDecodeError, no type hints |
| TroubleshootingAgent | 8/10 | Silent truncation |
| RAGAgent | 6/10 | Double retrieval, thin wrapper |
| PolicyAgent | 7/10 | Dead code, unused imports |
| AccessManagementAgent | 5/10 | Fake revoke, misleading logging |
| HumanApprovalAgent | 6/10 | In-memory state |
| NotificationAgent | 5/10 | Teams stub, inconsistent returns |
| AuditAgent | 5/10 | In-memory only |
| MemoryManager | 7/10 | Sequential awaits |
| AIOpsWorkflow | 6/10 | No node error handling |

## Frontend Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Code Quality | 7/10 | Clean structure, some convoluted logic |
| TypeScript | 5/10 | Strict mode on, but `any` leaks |
| State Management | 6/10 | Zustand clean, but full-store destructuring |
| Component Design | 6/10 | Good basics, monolithic pages |
| API Integration | 5/10 | React Query used inconsistently |
| Security | 4/10 | XSS, localStorage tokens |
| Performance | 5/10 | No lazy loading, no memoization |
| Accessibility | 3/10 | Missing aria-labels, no labels |

## Infrastructure Scorecard

| Category | Score | Key Gaps |
|----------|-------|----------|
| Docker | 4/10 | No .dockerignore, root user, no multi-stage |
| Kubernetes | 5/10 | Good probes, but no securityContext, no HPA |
| Terraform | 2/10 | Good structure, but all modules empty |
| CI/CD | 5/10 | Good shape, but silenced mypy, no caching |
| Security | 2/10 | Real creds in .env, secrets in git |
