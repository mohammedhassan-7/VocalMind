#!/usr/bin/env python3
"""Ensure NexaLink agents belong to nexalink-operations with a known password."""

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
from app.core.security import get_password_hash  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.interaction import Interaction  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.user import User  # noqa: E402

DATASET_ORG_SLUG = "nexalink-operations"
AGENT_PASSWORD = "NexaLink2026!"
AGENT_EMAILS = {
    "Priya": "agent.priya@nexalink.com",
    "Daniel": "agent.daniel@nexalink.com",
    "Marcus": "agent.marcus@nexalink.com",
    "Aisha": "agent.aisha@nexalink.com",
    "Hannah": "agent.hannah@nexalink.com",
}
AGENT_NAME_BY_EMAIL = {email: name for name, email in AGENT_EMAILS.items()}


async def main() -> int:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        org = (await session.exec(select(Organization).where(Organization.slug == DATASET_ORG_SLUG))).first()
        if not org:
            print(f"Missing org: {DATASET_ORG_SLUG}", file=sys.stderr)
            return 1

        pwd_hash = get_password_hash(AGENT_PASSWORD)
        for name, email in AGENT_EMAILS.items():
            user = (await session.exec(select(User).where(User.email == email))).first()
            if not user:
                user = User(
                    email=email,
                    name=name,
                    password_hash=pwd_hash,
                    organization_id=org.id,
                    role=UserRole.agent,
                    is_active=True,
                )
                session.add(user)
                print(f"created {email}")
            else:
                user.organization_id = org.id
                user.password_hash = pwd_hash
                user.role = UserRole.agent
                user.is_active = True
                user.name = name
                session.add(user)
                print(f"updated {email} -> org {DATASET_ORG_SLUG}")

        await session.commit()

        # Re-bind interactions in dataset org to agent users by agentName in list payload is not in DB;
        # interactions store agent_id. Match by email prefix from seeded agent ids in load script.
        agents = {
            email: (await session.exec(select(User).where(User.email == email))).first()
            for email in AGENT_EMAILS.values()
        }
        name_to_agent = {AGENT_NAME_BY_EMAIL[email]: agent for email, agent in agents.items() if agent}

        rows = (await session.exec(select(Interaction).where(Interaction.organization_id == org.id))).all()
        rebound = 0
        for row in rows:
            # Infer agent from audio filename token, e.g. CALL_09_daniel_...
            audio = (row.audio_file_path or "").lower()
            matched = None
            for agent_name, agent in name_to_agent.items():
                if f"_{agent_name.lower()}_" in audio:
                    matched = agent
                    break
            if matched and row.agent_id != matched.id:
                row.agent_id = matched.id
                session.add(row)
                rebound += 1
        await session.commit()
        print(f"rebound {rebound} interactions to dataset agents")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
