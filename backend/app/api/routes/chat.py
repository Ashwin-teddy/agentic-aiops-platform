from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.agents.workflow.aiops_workflow import get_aiops_workflow
from app.observability.logging import get_logger
from app.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY, AGENT_EXECUTIONS
import time

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ChatResponse:
    start = time.monotonic()
    workflow = get_aiops_workflow()
    try:
        result = await workflow.run(
            user_message=request.message,
            user_id=current_user.user_id,
            session_id=request.session_id,
            metadata=request.context,
        )
        elapsed = time.monotonic() - start
        REQUEST_COUNT.labels(method="POST", endpoint="/chat", status="200").inc()
        REQUEST_LATENCY.labels(method="POST", endpoint="/chat").observe(elapsed)
        AGENT_EXECUTIONS.labels(agent="workflow", status="completed").inc()
        return ChatResponse(
            session_id=result["session_id"],
            response=result["response"],
            intent=result.get("intent", ""),
            status=result.get("status", ""),
            metadata=result.get("metadata", {}),
        )
    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/chat", status="500").inc()
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    from app.agents.workflow.aiops_workflow import get_aiops_workflow
    workflow = get_aiops_workflow()
    context = await workflow.memory_manager.get_session_context(session_id)
    history = await workflow.memory_manager.get_user_history(current_user.user_id)
    return {"session_id": session_id, "context": context, "history": history}
