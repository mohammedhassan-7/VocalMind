from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlmodel import SQLModel, Session, create_engine, select

import app.models  # noqa: F401
from app.core import audio_folder_watcher as watcher
from app.models.enums import UserRole
from app.models.interaction import Interaction
from app.models.organization import Organization
from app.models.user import User


class _SyncResult:
    def __init__(self, result):
        self._result = result

    def first(self):
        return self._result.first()

    def all(self):
        return self._result.all()


class _AsyncSessionAdapter:
    def __init__(self, wrapped: Session):
        self._wrapped = wrapped

    async def exec(self, statement):
        return _SyncResult(self._wrapped.exec(statement))

    def add(self, instance):
        self._wrapped.add(instance)

    async def flush(self):
        self._wrapped.flush()

    async def commit(self):
        self._wrapped.commit()

    async def refresh(self, instance):
        self._wrapped.refresh(instance)


def _seed_org_with_users(session: Session, *, slug: str = "org-a") -> Organization:
    org = Organization(
        id=uuid4(),
        name="Org A",
        slug=slug,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    manager = User(
        id=uuid4(),
        organization_id=org.id,
        email="manager@orga.test",
        password_hash="hash",
        name="Manager",
        role=UserRole.manager,
        is_active=True,
    )
    agent = User(
        id=uuid4(),
        organization_id=org.id,
        email="agent@orga.test",
        password_hash="hash",
        name="Priya",
        role=UserRole.agent,
        is_active=True,
    )
    session.add(org)
    session.add(manager)
    session.add(agent)
    session.commit()
    return org


def test_out_of_bounds_symlink_path_is_rejected(tmp_path):
    org_dir = tmp_path / "audio" / "org-a"
    org_dir.mkdir(parents=True)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "escape.wav"
    outside_file.write_bytes(b"RIFF....WAVE")

    link_path = org_dir / "escape.wav"
    try:
        link_path.symlink_to(outside_file)
    except OSError:
        # Windows environments may block symlink creation without elevation;
        # fallback still validates an obvious out-of-bounds absolute path.
        assert _is_path_within_org_dir(outside_file, org_dir) is False
        return

    assert watcher._is_path_within_org_dir(link_path, org_dir) is False


def test_in_bounds_file_path_is_accepted(tmp_path):
    org_dir = tmp_path / "audio" / "org-a"
    org_dir.mkdir(parents=True)
    in_bounds = org_dir / "call_01.wav"
    in_bounds.write_bytes(b"RIFF....WAVE")

    assert watcher._is_path_within_org_dir(in_bounds, org_dir) is True


@pytest.mark.asyncio
async def test_scan_skips_out_of_bounds_symlink_and_warns(tmp_path, monkeypatch, caplog):
    engine = create_engine(f"sqlite:///{tmp_path / 'watcher.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    async_session = _AsyncSessionAdapter(session)
    org = _seed_org_with_users(session)

    root = tmp_path / "storage" / "audio"
    org_dir = root / org.slug
    org_dir.mkdir(parents=True)
    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"RIFF....WAVE")
    symlink = org_dir / "CALL_01_priya_escape.wav"
    try:
        symlink.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation not permitted in current environment")

    monkeypatch.setattr(watcher, "_audio_root", lambda: root)
    monkeypatch.setattr(watcher, "create_processing_jobs", AsyncMock())
    monkeypatch.setattr(watcher, "enqueue_interaction_processing", AsyncMock())

    with caplog.at_level("WARNING"):
        queued = await watcher._scan_organization_folder(async_session, org)

    assert queued == []
    assert "Watcher skipping out-of-bounds path for org=org-a" in caplog.text
    assert str(symlink) in caplog.text
    assert session.exec(select(Interaction)).all() == []


@pytest.mark.asyncio
async def test_scan_accepts_in_bounds_file(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'watcher-ok.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    async_session = _AsyncSessionAdapter(session)
    org = _seed_org_with_users(session)

    root = tmp_path / "storage" / "audio"
    org_dir = root / org.slug
    org_dir.mkdir(parents=True)
    (org_dir / "CALL_01_priya_ok.wav").write_bytes(b"RIFF....WAVE")

    monkeypatch.setattr(watcher, "_audio_root", lambda: root)
    monkeypatch.setattr(watcher, "create_processing_jobs", AsyncMock())
    monkeypatch.setattr(watcher, "enqueue_interaction_processing", AsyncMock())

    queued = await watcher._scan_organization_folder(async_session, org)

    assert len(queued) == 1
    interactions = session.exec(select(Interaction)).all()
    assert len(interactions) == 1
