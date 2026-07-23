from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
    code: str = ""


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: dict | None = None
