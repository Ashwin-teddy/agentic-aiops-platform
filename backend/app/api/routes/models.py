from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.core.llm.embeddings.embedding_router import get_embedding_router
from app.core.llm.router import get_model_router
from app.core.llm.types import TaskType
from app.observability.logging import get_logger

router = APIRouter(prefix="/models", tags=["Model Management"])
logger = get_logger(__name__)


class ModelOverrideRequest(BaseModel):
    task: str = Field(..., description="Task type to override")
    model: str = Field(..., description="Model key to use for this task")


class DefaultModelRequest(BaseModel):
    model: str = Field(..., description="Model key to set as default")


@router.get("/")
async def list_models(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    router_instance = get_model_router()
    models = router_instance.list_models()
    routing = router_instance.get_task_routing()
    return {
        "models": models,
        "task_routing": routing,
        "total_models": len(models),
    }


@router.get("/health")
async def model_health(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    router_instance = get_model_router()
    health = await router_instance.health_check_all()
    return {"providers": health}


@router.get("/embeddings")
async def list_embedding_models(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    emb_router = get_embedding_router()
    return {"models": emb_router.list_models()}


@router.post("/override")
async def set_task_model_override(
    request: ModelOverrideRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    try:
        task = TaskType(request.task)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task type: {request.task}. Valid: {[t.value for t in TaskType]}",
        )
    try:
        router_instance = get_model_router()
        router_instance.set_task_model(task, request.model)
        return {
            "success": True,
            "message": f"Task '{request.task}' now uses model '{request.model}'",
            "current_routing": router_instance.get_task_routing(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/routing")
async def get_routing(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    router_instance = get_model_router()
    routing = router_instance.get_task_routing()
    return {
        "routing": routing,
        "description": "Model routing per task type. First model in each list is the default.",
    }
