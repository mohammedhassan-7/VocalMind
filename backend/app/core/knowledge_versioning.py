"""Whole-knowledge-base versioning for an organization.

A *version* is an immutable JSON snapshot of an org's knowledge tables
(policies + SOPs/KB articles, both content and active flags). The live tables
stay the working copy the analysis pipeline reads; exactly one version per org
is ``is_active``.

- A mutating knowledge edit calls :func:`create_version` (snapshot the current
  live state, ``version_number = max + 1``, flip active).
- :func:`activate_version` restores an earlier snapshot into the live tables and
  moves the active pointer back to it.
- :func:`ensure_baseline_version` lazily seeds ``v1`` from current state so orgs
  that predate this feature (or were created later) always have an active
  version. This replaces an explicit migration backfill.

Restore scope: only the org's **owned** documents (``organization_id == org``)
have their content rewritten; shared/seeded docs owned by another org are left
intact and only the calling org's link ``is_active`` flags are restored.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.faq import FAQArticle, OrganizationFAQArticle
from app.models.knowledge_version import KnowledgeVersion
from app.models.policy import CompanyPolicy, OrganizationPolicy


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


# ── Snapshot ────────────────────────────────────────────────────────────────


async def snapshot_current_state(session: AsyncSession, org_id: UUID) -> dict[str, Any]:
    """Serialize the org's owned knowledge + its link rows into a JSON snapshot."""
    policies = (await session.exec(
        select(CompanyPolicy).where(CompanyPolicy.organization_id == org_id)
    )).all()
    policy_links = (await session.exec(
        select(OrganizationPolicy).where(OrganizationPolicy.organization_id == org_id)
    )).all()
    faqs = (await session.exec(
        select(FAQArticle).where(FAQArticle.organization_id == org_id)
    )).all()
    faq_links = (await session.exec(
        select(OrganizationFAQArticle).where(OrganizationFAQArticle.organization_id == org_id)
    )).all()

    return {
        "policies": [
            {
                "id": str(p.id),
                "policy_category": p.policy_category,
                "policy_title": p.policy_title,
                "policy_text": p.policy_text,
                "is_active": p.is_active,
                "created_at": _iso(p.created_at),
            }
            for p in policies
        ],
        "policy_links": [
            {"id": str(link.id), "policy_id": str(link.policy_id), "is_active": link.is_active}
            for link in policy_links
        ],
        "faqs": [
            {
                "id": str(f.id),
                "question": f.question,
                "answer": f.answer,
                "category": f.category,
                "is_active": f.is_active,
                "created_at": _iso(f.created_at),
            }
            for f in faqs
        ],
        "faq_links": [
            {"id": str(link.id), "article_id": str(link.article_id), "is_active": link.is_active}
            for link in faq_links
        ],
    }


# ── Read ────────────────────────────────────────────────────────────────────


async def get_active_version(session: AsyncSession, org_id: UUID) -> Optional[KnowledgeVersion]:
    return (await session.exec(
        select(KnowledgeVersion)
        .where(KnowledgeVersion.organization_id == org_id, KnowledgeVersion.is_active == True)  # noqa: E712
    )).first()


async def _max_version_number(session: AsyncSession, org_id: UUID) -> int:
    numbers = (await session.exec(
        select(KnowledgeVersion.version_number).where(KnowledgeVersion.organization_id == org_id)
    )).all()
    return max(numbers) if numbers else 0


async def get_version_by_number(
    session: AsyncSession, org_id: UUID, version_number: int
) -> Optional[KnowledgeVersion]:
    return (await session.exec(
        select(KnowledgeVersion).where(
            KnowledgeVersion.organization_id == org_id,
            KnowledgeVersion.version_number == version_number,
        )
    )).first()


def snapshot_to_grounding(snapshot: dict[str, Any]) -> tuple[str, str]:
    """Build (policy_text, sop_text) grounding overrides from a version snapshot.

    Only *active* documents are included, mirroring what the live retrieval layer
    would surface. KB articles and SOPs both live in ``faqs``; both feed the SOP
    grounding override.
    """
    active_link_ids = {
        link["policy_id"] for link in snapshot.get("policy_links", []) if link.get("is_active")
    }
    policy_text = "\n\n".join(
        p["policy_text"]
        for p in snapshot.get("policies", [])
        if p.get("is_active") and p["id"] in active_link_ids
    )
    active_faq_ids = {
        link["article_id"] for link in snapshot.get("faq_links", []) if link.get("is_active")
    }
    sop_text = "\n\n".join(
        f.get("answer", "")
        for f in snapshot.get("faqs", [])
        if f.get("is_active") and f["id"] in active_faq_ids
    )
    return policy_text, sop_text


async def list_versions(session: AsyncSession, org_id: UUID) -> list[KnowledgeVersion]:
    return (await session.exec(
        select(KnowledgeVersion)
        .where(KnowledgeVersion.organization_id == org_id)
        .order_by(KnowledgeVersion.version_number.desc())  # type: ignore[attr-defined]
    )).all()


# ── Write ───────────────────────────────────────────────────────────────────


async def create_version(
    session: AsyncSession,
    org_id: UUID,
    user_id: UUID | None,
    summary: str,
) -> KnowledgeVersion:
    """Snapshot the org's current live knowledge and make it the active version."""
    snapshot = await snapshot_current_state(session, org_id)
    next_number = await _max_version_number(session, org_id) + 1

    # Demote the previous active version.
    current_active = await get_active_version(session, org_id)
    if current_active is not None:
        current_active.is_active = False
        session.add(current_active)

    version = KnowledgeVersion(
        organization_id=org_id,
        version_number=next_number,
        summary=summary[:255],
        created_by=user_id,
        is_active=True,
        snapshot=snapshot,
        created_at=_now(),
    )
    session.add(version)
    await session.flush()
    return version


async def ensure_baseline_version(
    session: AsyncSession,
    org_id: UUID,
    user_id: UUID | None = None,
) -> KnowledgeVersion:
    """Return the org's active version, lazily creating a v1 baseline if none exists."""
    active = await get_active_version(session, org_id)
    if active is not None:
        return active
    return await create_version(session, org_id, user_id, "Initial knowledge baseline")


async def get_active_version_number(
    session: AsyncSession,
    org_id: UUID,
    user_id: UUID | None = None,
) -> int:
    """Active version number for the org, seeding a baseline if needed."""
    active = await ensure_baseline_version(session, org_id, user_id)
    return active.version_number


async def activate_version(
    session: AsyncSession,
    org_id: UUID,
    version_id: UUID,
    user_id: UUID | None = None,
) -> KnowledgeVersion:
    """Restore the chosen version's snapshot into the live tables and flip active.

    Raises ``ValueError`` if the version does not belong to the org.
    """
    target = (await session.exec(
        select(KnowledgeVersion).where(KnowledgeVersion.id == version_id)
    )).first()
    if target is None or target.organization_id != org_id:
        raise ValueError("Knowledge version not found for this organization")

    await _restore_snapshot(session, org_id, target.snapshot or {})

    # Move the active pointer to the restored version.
    for version in (await session.exec(
        select(KnowledgeVersion).where(
            KnowledgeVersion.organization_id == org_id, KnowledgeVersion.is_active == True  # noqa: E712
        )
    )).all():
        version.is_active = False
        session.add(version)
    target.is_active = True
    session.add(target)
    await session.flush()
    return target


async def _restore_snapshot(session: AsyncSession, org_id: UUID, snapshot: dict[str, Any]) -> None:
    """Reconcile the org's owned docs + links to match a snapshot (upsert + prune)."""
    await _restore_policies(session, org_id, snapshot.get("policies", []), snapshot.get("policy_links", []))
    await _restore_faqs(session, org_id, snapshot.get("faqs", []), snapshot.get("faq_links", []))


async def _restore_policies(
    session: AsyncSession,
    org_id: UUID,
    policies: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> None:
    snap_by_id = {UUID(p["id"]): p for p in policies}
    existing = {
        p.id: p
        for p in (await session.exec(
            select(CompanyPolicy).where(CompanyPolicy.organization_id == org_id)
        )).all()
    }
    for pid, snap in snap_by_id.items():
        row = existing.get(pid)
        if row is None:
            row = CompanyPolicy(id=pid, organization_id=org_id, created_at=_parse_dt(snap.get("created_at")) or _now())
        row.policy_category = snap["policy_category"]
        row.policy_title = snap["policy_title"]
        row.policy_text = snap["policy_text"]
        row.is_active = snap["is_active"]
        row.updated_at = _now()
        session.add(row)
    for pid, row in existing.items():
        if pid not in snap_by_id:
            await session.delete(row)

    await _restore_links(
        session, OrganizationPolicy, OrganizationPolicy.organization_id == org_id,
        org_id, links, id_field="policy_id",
    )


async def _restore_faqs(
    session: AsyncSession,
    org_id: UUID,
    faqs: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> None:
    snap_by_id = {UUID(f["id"]): f for f in faqs}
    existing = {
        f.id: f
        for f in (await session.exec(
            select(FAQArticle).where(FAQArticle.organization_id == org_id)
        )).all()
    }
    for fid, snap in snap_by_id.items():
        row = existing.get(fid)
        if row is None:
            row = FAQArticle(id=fid, organization_id=org_id, created_at=_parse_dt(snap.get("created_at")) or _now())
        row.question = snap["question"]
        row.answer = snap["answer"]
        row.category = snap["category"]
        row.is_active = snap["is_active"]
        row.updated_at = _now()
        session.add(row)
    for fid, row in existing.items():
        if fid not in snap_by_id:
            await session.delete(row)

    await _restore_links(
        session, OrganizationFAQArticle, OrganizationFAQArticle.organization_id == org_id,
        org_id, links, id_field="article_id",
    )


async def _restore_links(
    session: AsyncSession,
    model: Any,
    org_clause: Any,
    org_id: UUID,
    links: list[dict[str, Any]],
    *,
    id_field: str,
) -> None:
    """Restore junction-table active flags; recreate missing links, prune extras."""
    snap_by_id = {UUID(link["id"]): link for link in links}
    existing = {link.id: link for link in (await session.exec(select(model).where(org_clause))).all()}
    for link_id, snap in snap_by_id.items():
        row = existing.get(link_id)
        if row is None:
            row = model(id=link_id, organization_id=org_id, **{id_field: UUID(snap[id_field])})
        row.is_active = snap["is_active"]
        session.add(row)
    for link_id, row in existing.items():
        if link_id not in snap_by_id:
            await session.delete(row)
