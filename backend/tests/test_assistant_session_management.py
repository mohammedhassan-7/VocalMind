"""
Regression tests for assistant session rename / delete.

These endpoints had a latent bug: `session.exec(text(...), {params})` passed the
params dict positionally, but SQLModel's `AsyncSession.exec` takes `params` as a
keyword-only argument, so every rename/delete raised TypeError -> HTTP 500.

They are exercised here against a real async (aiosqlite) session by calling the
route coroutines directly, which avoids the sync-Session / UUID-text-representation
mismatches that make a full TestClient flow unreliable for these two routes.
"""
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import app.models  # noqa: F401 — register all tables on SQLModel.metadata
from app.api.routes.assistant import (
    AssistantSessionRenameRequest,
    delete_assistant_session,
    rename_assistant_session,
)
from app.models.enums import UserRole
from app.models.user import User
from fastapi import HTTPException

MGR_ID = UUID("b0000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("b0000000-0000-0000-0000-0000000000ff")
ORG_ID = UUID("a0000000-0000-0000-0000-000000000001")


def _manager() -> User:
    return User(
        id=MGR_ID,
        organization_id=ORG_ID,
        email="manager@test.local",
        password_hash="x",
        name="Manager",
        role=UserRole.manager,
        is_active=True,
    )


def _agent() -> User:
    u = _manager()
    u.role = UserRole.agent
    return u


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


async def _seed_session(session: AsyncSession, *, owner: UUID, title: str = "Original") -> str:
    """Insert one assistant_sessions row; return its id as the route would receive it."""
    sid = uuid4()
    await session.exec(
        text(
            "INSERT INTO assistant_sessions (id, user_id, organization_id, title, is_deleted, created_at) "
            "VALUES (:id, :uid, :oid, :title, 0, :created)"
        ),
        params={
            "id": str(sid),
            "uid": str(owner),
            "oid": str(ORG_ID),
            "title": title,
            "created": "2026-06-22 00:00:00",
        },
    )
    await session.commit()
    # Match the exact text form the route's `CAST(id AS TEXT)` will compare against.
    row = await session.exec(
        text("SELECT CAST(id AS TEXT) FROM assistant_sessions WHERE CAST(user_id AS TEXT) = :uid"),
        params={"uid": str(owner)},
    )
    return row.scalar()


async def _title_of(session: AsyncSession, sid_text: str) -> str:
    row = await session.exec(
        text("SELECT title FROM assistant_sessions WHERE CAST(id AS TEXT) = :sid"),
        params={"sid": sid_text},
    )
    return row.scalar()


async def _is_deleted(session: AsyncSession, sid_text: str) -> bool:
    row = await session.exec(
        text("SELECT is_deleted FROM assistant_sessions WHERE CAST(id AS TEXT) = :sid"),
        params={"sid": sid_text},
    )
    return bool(row.scalar())


@pytest.mark.asyncio
async def test_rename_updates_title(async_session):
    sid = await _seed_session(async_session, owner=MGR_ID, title="Original")

    result = await rename_assistant_session(
        sid, AssistantSessionRenameRequest(title="Renamed Q2 review"), _manager(), async_session
    )

    assert result == {"success": True}
    assert await _title_of(async_session, sid) == "Renamed Q2 review"


@pytest.mark.asyncio
async def test_rename_truncates_long_title(async_session):
    sid = await _seed_session(async_session, owner=MGR_ID)
    long_title = "x" * 400

    await rename_assistant_session(
        sid, AssistantSessionRenameRequest(title=long_title), _manager(), async_session
    )

    assert len(await _title_of(async_session, sid)) == 255


@pytest.mark.asyncio
async def test_rename_missing_session_returns_404(async_session):
    with pytest.raises(HTTPException) as exc:
        await rename_assistant_session(
            str(uuid4()), AssistantSessionRenameRequest(title="x"), _manager(), async_session
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_rename_other_users_session_returns_404(async_session):
    # Owned by someone else -> manager must not be able to rename it.
    sid = await _seed_session(async_session, owner=OTHER_USER_ID, title="Theirs")

    with pytest.raises(HTTPException) as exc:
        await rename_assistant_session(
            sid, AssistantSessionRenameRequest(title="hijacked"), _manager(), async_session
        )

    assert exc.value.status_code == 404
    assert await _title_of(async_session, sid) == "Theirs"


@pytest.mark.asyncio
async def test_rename_requires_manager_role(async_session):
    sid = await _seed_session(async_session, owner=MGR_ID)
    with pytest.raises(HTTPException) as exc:
        await rename_assistant_session(
            sid, AssistantSessionRenameRequest(title="x"), _agent(), async_session
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_soft_deletes_session(async_session):
    sid = await _seed_session(async_session, owner=MGR_ID)
    assert await _is_deleted(async_session, sid) is False

    result = await delete_assistant_session(sid, _manager(), async_session)

    assert result == {"success": True}
    assert await _is_deleted(async_session, sid) is True


@pytest.mark.asyncio
async def test_delete_missing_session_returns_404(async_session):
    with pytest.raises(HTTPException) as exc:
        await delete_assistant_session(str(uuid4()), _manager(), async_session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_users_session_returns_404(async_session):
    sid = await _seed_session(async_session, owner=OTHER_USER_ID)
    with pytest.raises(HTTPException) as exc:
        await delete_assistant_session(sid, _manager(), async_session)
    assert exc.value.status_code == 404
    assert await _is_deleted(async_session, sid) is False


@pytest.mark.asyncio
async def test_delete_requires_manager_role(async_session):
    sid = await _seed_session(async_session, owner=MGR_ID)
    with pytest.raises(HTTPException) as exc:
        await delete_assistant_session(sid, _agent(), async_session)
    assert exc.value.status_code == 403
