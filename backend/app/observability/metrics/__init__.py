from prometheus_client import Counter, Gauge, Histogram, Info

REQUEST_COUNT = Counter("aiops_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram(
    "aiops_request_latency_seconds", "Request latency", ["method", "endpoint"]
)
ACTIVE_AGENTS = Gauge("aiops_active_agents", "Number of active agents")
PLATFORM_INFO = Info("aiops_platform", "Platform info")
LLM_CALLS = Counter("aiops_llm_calls_total", "Total LLM calls", ["provider", "model", "status"])
LLM_TOKENS_USED = Counter("aiops_llm_tokens_total", "Total LLM tokens used", ["model"])
AGENT_EXECUTIONS = Counter(
    "aiops_agent_executions_total", "Total agent executions", ["agent", "status"]
)


def setup_metrics() -> None:
    PLATFORM_INFO.info({"version": "1.0.0", "env": "development"})


def get_metrics() -> dict:
    return {
        "request_count": REQUEST_COUNT,
        "request_latency": REQUEST_LATENCY,
        "active_agents": ACTIVE_AGENTS,
        "platform_info": PLATFORM_INFO,
        "llm_calls": LLM_CALLS,
    }
