from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class KnowledgeVersion(SQLModel, table=True):
    """An immutable snapshot of an organization's full knowledge state.

    Every mutating knowledge action (policy / SOP / KB add·edit·toggle·delete)
    creates a new version capturing the active doc set + content at that moment.
    Exactly one version per organization is ``is_active``; activating an earlier
    version restores its snapshot into the live knowledge tables.
    """

    __tablename__ = "knowledge_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    version_number: int = Field(index=True)
    summary: str = Field(max_length=255, default="")
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    is_active: bool = Field(default=False)
    # JSON (not JSONB) so SQLite test fixtures and Postgres both accept the column.
    # Shape: {"policies": [...], "policy_links": [...], "faqs": [...], "faq_links": [...]}
    snapshot: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
