from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        ...

    @abstractmethod
    async def create(self, entity: ModelType) -> ModelType:
        ...

    @abstractmethod
    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> ModelType | None:
        ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool:
        ...

    @abstractmethod
    async def list(
        self, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100
    ) -> list[ModelType]:
        ...

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        ...


class UserRepository(BaseRepository):
    @abstractmethod
    async def get_by_email(self, email: str) -> Any | None:
        ...

    @abstractmethod
    async def get_by_azure_ad_id(self, azure_ad_id: str) -> Any | None:
        ...


class WorkflowRepository(BaseRepository):
    @abstractmethod
    async def get_by_type(self, workflow_type: str) -> list[Any]:
        ...

    @abstractmethod
    async def get_active_workflows(self) -> list[Any]:
        ...


class AccessRequestRepository(BaseRepository):
    @abstractmethod
    async def get_pending_by_user(self, user_id: uuid.UUID) -> list[Any]:
        ...

    @abstractmethod
    async def get_by_status(self, status: str) -> list[Any]:
        ...


class IncidentRepository(BaseRepository):
    @abstractmethod
    async def get_by_severity(self, severity: str) -> list[Any]:
        ...

    @abstractmethod
    async def search(self, query: str) -> list[Any]:
        ...


class ApprovalRepository(BaseRepository):
    @abstractmethod
    async def get_pending_by_approver(self, approver_id: uuid.UUID) -> list[Any]:
        ...

    @abstractmethod
    async def get_by_request(self, request_id: uuid.UUID) -> list[Any]:
        ...


class AuditLogRepository(BaseRepository):
    @abstractmethod
    async def log(self, audit_entry: Any) -> None:
        ...

    @abstractmethod
    async def search(
        self, user_id: uuid.UUID | None = None, action: str | None = None,
        start_date: Any = None, end_date: Any = None, limit: int = 100
    ) -> list[Any]:
        ...


class KnowledgeRepository(BaseRepository):
    @abstractmethod
    async def search_similar(self, query_embedding: list[float], top_k: int = 5) -> list[Any]:
        ...

    @abstractmethod
    async def get_by_source(self, source: str) -> list[Any]:
        ...
