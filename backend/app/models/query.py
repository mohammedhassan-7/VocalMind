from sqlmodel import SQLModel, Field
from typing import Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, Enum as SAEnum, JSON
from datetime import datetime, timezone
from app.models.enums import QueryMode


class AssistantSession(SQLModel, table=True):
    __tablename__ = "assistant_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    title: str = Field(max_length=255, default="New chat")
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AssistantQuery(SQLModel, table=True):
    __tablename__ = "assistant_queries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: Optional[UUID] = Field(default=None, foreign_key="assistant_sessions.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    query_mode: QueryMode = Field(
        sa_type=SAEnum(QueryMode, name="query_mode_enum", create_constraint=False, native_enum=True),
    )
    audio_input_path: Optional[str] = None
    query_text: str
    ai_understanding: Optional[str] = None
    generated_sql: Optional[str] = None
    response_text: Optional[str] = None
    execution_time_ms: Optional[int] = None
    # JSON (not JSONB) so SQLite test fixtures and Postgres both accept the column.
    result_rows: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
