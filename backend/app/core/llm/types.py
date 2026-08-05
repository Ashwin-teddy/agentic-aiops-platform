from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"
    COHERE = "cohere"


class ModelTier(str, Enum):
    FLAGSHIP = "flagship"
    BALANCED = "balanced"
    FAST = "fast"
    EMBEDDING = "embedding"


class TaskType(str, Enum):
    INTENT_DETECTION = "intent_detection"
    PLANNING = "planning"
    REASONING = "reasoning"
    TROUBLESHOOTING = "troubleshooting"
    RAG_ANSWER = "rag_answer"
    CODE_ANALYSIS = "code_analysis"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    GENERAL = "general"
    EMBEDDING = "embedding"


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: ModelProvider
    usage: LLMUsage = field(default_factory=LLMUsage)
    finish_reason: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass
class EmbeddingResult:
    embeddings: list[list[float]]
    model: str
    provider: ModelProvider
    dimensions: int = 0
    usage: LLMUsage = field(default_factory=LLMUsage)


@dataclass
class ModelConfig:
    provider: ModelProvider
    model_id: str
    tier: ModelTier
    max_tokens: int = 4096
    context_window: int = 128000
    supports_json_mode: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0
    rate_limit_rpm: int = 60
    embedding_dims: int = 0
    display_name: str = ""
    api_key_env: str = ""
    base_url: str = ""

    def __post_init__(self) -> None:
        if not self.display_name:
            self.display_name = f"{self.provider.value}/{self.model_id}"


AVAILABLE_MODELS: dict[str, ModelConfig] = {
    # OpenAI Models
    "gpt-5.5-pro": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="gpt-5.5-pro", tier=ModelTier.FLAGSHIP,
        max_tokens=16384, context_window=1_000_000, input_cost_per_million=25.0,
        output_cost_per_million=150.0, supports_vision=True,
        api_key_env="OPENAI_API_KEY", display_name="GPT-5.5 Pro",
    ),
    "gpt-4.1": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="gpt-4.1", tier=ModelTier.BALANCED,
        max_tokens=32768, context_window=1_000_000, input_cost_per_million=2.0,
        output_cost_per_million=8.0, supports_vision=True,
        api_key_env="OPENAI_API_KEY", display_name="GPT-4.1",
    ),
    "gpt-4o": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="gpt-4o", tier=ModelTier.BALANCED,
        max_tokens=16384, context_window=128_000, input_cost_per_million=2.5,
        output_cost_per_million=10.0, supports_vision=True,
        api_key_env="OPENAI_API_KEY", display_name="GPT-4o",
    ),
    "gpt-4o-mini": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="gpt-4o-mini", tier=ModelTier.FAST,
        max_tokens=16384, context_window=128_000, input_cost_per_million=0.15,
        output_cost_per_million=0.6, supports_vision=True,
        api_key_env="OPENAI_API_KEY", display_name="GPT-4o Mini",
    ),
    "o3-mini": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="o3-mini", tier=ModelTier.FAST,
        max_tokens=100000, context_window=128_000, input_cost_per_million=1.1,
        output_cost_per_million=4.4, supports_tools=False,
        api_key_env="OPENAI_API_KEY", display_name="O3 Mini",
    ),
    "gpt-5.4-nano": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="gpt-5.4-nano", tier=ModelTier.FAST,
        max_tokens=32768, context_window=400_000, input_cost_per_million=0.2,
        output_cost_per_million=1.25,
        api_key_env="OPENAI_API_KEY", display_name="GPT-5.4 Nano",
    ),
    "text-embedding-3-large": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="text-embedding-3-large", tier=ModelTier.EMBEDDING,
        context_window=8191, embedding_dims=3072, supports_tools=False,
        input_cost_per_million=0.13, api_key_env="OPENAI_API_KEY",
        display_name="Embedding 3 Large",
    ),
    "text-embedding-3-small": ModelConfig(
        provider=ModelProvider.OPENAI, model_id="text-embedding-3-small", tier=ModelTier.EMBEDDING,
        context_window=8191, embedding_dims=1536, supports_tools=False,
        input_cost_per_million=0.02, api_key_env="OPENAI_API_KEY",
        display_name="Embedding 3 Small",
    ),

    # Anthropic Claude Models
    "claude-opus-4": ModelConfig(
        provider=ModelProvider.ANTHROPIC, model_id="claude-opus-4-20250715", tier=ModelTier.FLAGSHIP,
        max_tokens=32768, context_window=200_000, input_cost_per_million=15.0,
        output_cost_per_million=75.0, supports_vision=True, supports_tools=True,
        api_key_env="ANTHROPIC_API_KEY", display_name="Claude Opus 4",
    ),
    "claude-sonnet-4": ModelConfig(
        provider=ModelProvider.ANTHROPIC, model_id="claude-sonnet-4-20250514", tier=ModelTier.BALANCED,
        max_tokens=16384, context_window=200_000, input_cost_per_million=3.0,
        output_cost_per_million=15.0, supports_vision=True, supports_tools=True,
        api_key_env="ANTHROPIC_API_KEY", display_name="Claude Sonnet 4",
    ),
    "claude-haiku-3.5": ModelConfig(
        provider=ModelProvider.ANTHROPIC, model_id="claude-3-5-haiku-20241022", tier=ModelTier.FAST,
        max_tokens=8192, context_window=200_000, input_cost_per_million=0.8,
        output_cost_per_million=4.0, supports_vision=True, supports_tools=True,
        api_key_env="ANTHROPIC_API_KEY", display_name="Claude Haiku 3.5",
    ),

    # Google Gemini Models
    "gemini-3.1-pro": ModelConfig(
        provider=ModelProvider.GOOGLE, model_id="gemini-3.1-pro", tier=ModelTier.FLAGSHIP,
        max_tokens=65536, context_window=1_000_000, input_cost_per_million=1.25,
        output_cost_per_million=10.0, supports_vision=True, supports_tools=True,
        api_key_env="GOOGLE_API_KEY", display_name="Gemini 3.1 Pro",
    ),
    "gemini-3.5-flash": ModelConfig(
        provider=ModelProvider.GOOGLE, model_id="gemini-3.5-flash", tier=ModelTier.FAST,
        max_tokens=65536, context_window=1_000_000, input_cost_per_million=0.15,
        output_cost_per_million=0.6, supports_vision=True, supports_tools=True,
        api_key_env="GOOGLE_API_KEY", display_name="Gemini 3.5 Flash",
    ),
    "gemini-2.5-flash": ModelConfig(
        provider=ModelProvider.GOOGLE, model_id="gemini-2.5-flash", tier=ModelTier.FAST,
        max_tokens=65536, context_window=1_000_000, input_cost_per_million=0.15,
        output_cost_per_million=0.6, supports_vision=True, supports_tools=True,
        api_key_env="GOOGLE_API_KEY", display_name="Gemini 2.5 Flash",
    ),

    # Ollama / Self-Hosted Models
    "llama3.2": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="llama3.2", tier=ModelTier.BALANCED,
        max_tokens=8192, context_window=128_000, input_cost_per_million=0.0,
        output_cost_per_million=0.0, supports_tools=True,
        base_url="http://localhost:11434", display_name="Llama 3.2 (Self-hosted)",
    ),
    "nomic-embed-text": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="nomic-embed-text", tier=ModelTier.EMBEDDING,
        max_tokens=8192, context_window=8192, input_cost_per_million=0.0,
        output_cost_per_million=0.0, base_url="http://localhost:11434",
        embedding_dims=768, display_name="Nomic Embed Text (Self-hosted)",
    ),
    "llama-4-maverick": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="llama4-maverick", tier=ModelTier.BALANCED,
        max_tokens=32768, context_window=1_000_000, input_cost_per_million=0.0,
        output_cost_per_million=0.0, supports_vision=True, supports_tools=True,
        base_url="http://localhost:11434", display_name="Llama 4 Maverick (Self-hosted)",
    ),
    "llama-3.3-70b": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="llama3.3:70b", tier=ModelTier.BALANCED,
        max_tokens=32768, context_window=128_000, input_cost_per_million=0.0,
        output_cost_per_million=0.0, supports_tools=True,
        base_url="http://localhost:11434", display_name="Llama 3.3 70B (Self-hosted)",
    ),
    "deepseek-v4-pro": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="deepseek-v4-pro", tier=ModelTier.BALANCED,
        max_tokens=32768, context_window=128_000, input_cost_per_million=0.0,
        output_cost_per_million=0.0, supports_tools=True,
        base_url="http://localhost:11434", display_name="DeepSeek V4 Pro (Self-hosted)",
    ),
    "qwen3.5-397b": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="qwen3.5:397b", tier=ModelTier.FLAGSHIP,
        max_tokens=32768, context_window=1_000_000, input_cost_per_million=0.0,
        output_cost_per_million=0.0, supports_tools=True,
        base_url="http://localhost:11434", display_name="Qwen 3.5 397B (Self-hosted)",
    ),
    "mistral-large-2": ModelConfig(
        provider=ModelProvider.OLLAMA, model_id="mistral-large:latest", tier=ModelTier.BALANCED,
        max_tokens=32768, context_window=128_000, input_cost_per_million=0.0,
        output_cost_per_million=0.0, supports_tools=True,
        base_url="http://localhost:11434", display_name="Mistral Large 2 (Self-hosted)",
    ),
}

TASK_MODEL_ROUTING: dict[TaskType, list[str]] = {
    TaskType.INTENT_DETECTION: ["llama3.2", "llama-4-maverick", "mistral-large-2"],
    TaskType.PLANNING: ["llama3.2", "llama-4-maverick", "deepseek-v4-pro"],
    TaskType.REASONING: ["llama3.2", "llama-4-maverick", "deepseek-v4-pro"],
    TaskType.TROUBLESHOOTING: ["llama3.2", "llama-4-maverick", "llama-3.3-70b"],
    TaskType.RAG_ANSWER: ["llama3.2", "llama-4-maverick", "llama-3.3-70b"],
    TaskType.CODE_ANALYSIS: ["llama3.2", "deepseek-v4-pro", "llama-4-maverick"],
    TaskType.SUMMARIZATION: ["llama3.2", "mistral-large-2", "llama-4-maverick"],
    TaskType.CLASSIFICATION: ["llama3.2", "llama-4-maverick", "mistral-large-2"],
    TaskType.GENERAL: ["llama3.2", "llama-4-maverick", "mistral-large-2"],
    TaskType.EMBEDDING: ["nomic-embed-text"],
}


def apply_environment_overrides(ollama_base_url: str | None = None) -> None:
    base_url = ollama_base_url or "http://localhost:11434"
    for config in AVAILABLE_MODELS.values():
        if config.provider == ModelProvider.OLLAMA:
            config.base_url = base_url
