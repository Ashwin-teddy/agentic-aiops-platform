from __future__ import annotations

from typing import Any

from app.memory.conversation.conversation_memory import ConversationMemory
from app.memory.long_term.long_term_memory import LongTermMemory
from app.memory.organizational.org_memory import OrganizationalMemory
from app.memory.session.session_memory import SessionMemory
from app.observability.logging import get_logger

logger = get_logger(__name__)


class MemoryManager:
    name = "memory_manager"

    def __init__(self) -> None:
        self.session = SessionMemory()
        self.conversation = ConversationMemory()
        self.long_term = LongTermMemory()
        self.organizational = OrganizationalMemory()

    async def initialize_session(self, user_id: str) -> str:
        session_id = await self.session.create_session(user_id)
        logger.info("session_initialized", session_id=session_id, user_id=user_id)
        return session_id

    async def get_session_context(self, session_id: str) -> dict[str, Any]:
        return await self.session.get_context(session_id)

    async def update_session_context(self, session_id: str, key: str, value: Any) -> None:
        await self.session.update_context(session_id, key, value)

    async def add_conversation_turn(
        self, user_id: str, session_id: str, user_msg: str, assistant_msg: str, intent: str = ""
    ) -> None:
        await self.conversation.add_turn(user_id, session_id, user_msg, assistant_msg, intent)

    async def get_user_history(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return await self.conversation.get_history(user_id, limit)

    async def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        return await self.long_term.get_all_preferences(user_id)

    async def store_user_preference(self, user_id: str, key: str, value: Any) -> None:
        await self.long_term.store_preference(user_id, key, value)

    async def get_team_knowledge(self, team: str, key: str) -> Any | None:
        return await self.organizational.get_team_knowledge(team, key)

    async def store_team_knowledge(self, team: str, key: str, value: Any) -> None:
        await self.organizational.store_team_knowledge(team, key, value)

    async def get_full_context(self, user_id: str, session_id: str) -> dict[str, Any]:
        session_ctx = await self.session.get_context(session_id)
        history = await self.conversation.get_history(user_id, limit=5)
        preferences = await self.long_term.get_all_preferences(user_id)
        return {
            "session_context": session_ctx,
            "recent_history": history,
            "preferences": preferences,
        }
