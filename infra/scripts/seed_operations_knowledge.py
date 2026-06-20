#!/usr/bin/env python3
"""Seed SOP + KB articles for nexalink-operations from the source nexalink org."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv(REPO_ROOT / "backend" / ".env")

from app.core.database import engine  # noqa: E402
from app.core.knowledge_seed import ensure_organization_knowledge_from_source  # noqa: E402
from app.models.organization import Organization  # noqa: E402

TARGET_SLUG = "nexalink-operations"
SOURCE_SLUG = "nexalink"


async def main() -> int:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        result = await session.exec(select(Organization).where(Organization.slug == TARGET_SLUG))
        org = result.first()
        if not org:
            print(f"Organization not found: {TARGET_SLUG}", file=sys.stderr)
            return 1
        counts = await ensure_organization_knowledge_from_source(
            session,
            org.id,
            source_org_slug=SOURCE_SLUG,
        )
        await session.commit()
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
