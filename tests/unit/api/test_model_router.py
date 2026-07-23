import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.llm.types import (
    LLMMessage, LLMResponse, LLMUsage, ModelConfig,
    ModelProvider, ModelTier, TaskType,
    AVAILABLE_MODELS, TASK_MODEL_ROUTING,
)
from app.core.llm.router import ModelRouter


class TestModelRouter:
    @pytest.fixture
    def router(self) -> ModelRouter:
        return ModelRouter(fallback_enabled=False)

    def test_list_models(self, router: ModelRouter) -> None:
        models = router.list_models()
        assert len(models) >= 15
        providers = {m["provider"] for m in models}
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "ollama" in providers

    def test_get_model_for_task_intent(self, router: ModelRouter) -> None:
        model = router.get_model_for_task(TaskType.INTENT_DETECTION)
        assert model in AVAILABLE_MODELS
        config = AVAILABLE_MODELS[model]
        assert config.tier == ModelTier.FAST

    def test_get_model_for_task_planning(self, router: ModelRouter) -> None:
        model = router.get_model_for_task(TaskType.PLANNING)
        assert model in AVAILABLE_MODELS

    def test_task_override(self, router: ModelRouter) -> None:
        router.set_task_model(TaskType.INTENT_DETECTION, "claude-opus-4")
        model = router.get_model_for_task(TaskType.INTENT_DETECTION)
        assert model == "claude-opus-4"

    def test_invalid_model_raises(self, router: ModelRouter) -> None:
        with pytest.raises(ValueError):
            router.set_task_model(TaskType.GENERAL, "nonexistent-model")

    def test_task_routing_covers_all_tasks(self) -> None:
        for task in TaskType:
            if task == TaskType.EMBEDDING:
                continue
            assert task in TASK_MODEL_ROUTING, f"No routing for {task}"
            assert len(TASK_MODEL_ROUTING[task]) > 0, f"Empty routing for {task}"


class TestModelConfigs:
    def test_all_models_have_required_fields(self) -> None:
        for key, config in AVAILABLE_MODELS.items():
            assert config.provider in ModelProvider, f"{key} invalid provider"
            assert config.model_id, f"{key} missing model_id"
            assert config.context_window > 0, f"{key} invalid context_window"

    def test_embedding_models_have_dims(self) -> None:
        for key, config in AVAILABLE_MODELS.items():
            if config.tier == ModelTier.EMBEDDING:
                assert config.embedding_dims > 0, f"{key} missing embedding_dims"

    def test_openai_models_have_api_key_env(self) -> None:
        for key, config in AVAILABLE_MODELS.items():
            if config.provider == ModelProvider.OPENAI:
                assert config.api_key_env == "OPENAI_API_KEY"

    def test_anthropic_models_have_api_key_env(self) -> None:
        for key, config in AVAILABLE_MODELS.items():
            if config.provider == ModelProvider.ANTHROPIC:
                assert config.api_key_env == "ANTHROPIC_API_KEY"

    def test_ollama_models_have_base_url(self) -> None:
        for key, config in AVAILABLE_MODELS.items():
            if config.provider == ModelProvider.OLLAMA:
                assert config.base_url == "http://localhost:11434"
