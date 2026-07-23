from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor


_tracer = None


def setup_tracing() -> None:
    global _tracer
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("agentic-aiops")


def get_tracer(name: str = "agentic-aiops") -> trace.Tracer:
    return trace.get_tracer(name)
