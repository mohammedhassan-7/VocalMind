"""Reset the LOCAL dev database to a clean, minimal, usable state.

DESTRUCTIVE: truncates every application table in the configured DATABASE_URL,
then seeds the two organizations from the TTS audio project (Nexalink + Meridian),
each with a manager and its agent roster, so manual UI uploads work. No demo
calls, policies, or KB — those are added manually afterwards.

All users share the local-dev password (default: ``password123``), matching the
existing seed_nexalink / seed_meridian convention. Email/password login only.

Safety guardrails:
  * Refuses to run unless DATABASE_URL clearly points at a LOCAL host
    (localhost / 127.0.0.1 / host.docker.internal / the compose ``db`` service),
    so it can never wipe the remote Supabase database.
  * Requires ``--yes`` to actually execute.

Usage (from the backend/ directory):
  uv run python -m scripts.reset_local_db --yes
  uv run python -m scripts.reset_local_db --yes --password mysecret
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.enums import AgentType, OrgStatus, UserRole
from app.models.organization import Organization
from app.models.user import User

# Orgs + rosters mirror the TTS audio project (data/agents/<org>/<agent>) and the
# existing seed_nexalink / seed_meridian scripts, so an uploaded
# CALL_<NN>_<agent>_*.wav can be assigned to a like-named agent.
_ORGS: tuple[dict, ...] = (
    {
        "name": "Nexalink",
        "slug": "nexalink",
        "manager": ("manager@nexalink.com", "Nexalink Manager"),
        "agents": [
            ("agent.priya@nexalink.com", "Priya"),
            ("agent.daniel@nexalink.com", "Daniel"),
            ("agent.marcus@nexalink.com", "Marcus"),
            ("agent.aisha@nexalink.com", "Aisha"),
            ("agent.hannah@nexalink.com", "Hannah"),
        ],
    },
    {
        "name": "Meridian Trust Bank",
        "slug": "meridian",
        "manager": ("manager@meridian.com", "Meridian Trust Bank Manager"),
        "agents": [
            ("agent.sarah@meridian.com", "Sarah"),
            ("agent.tyler@meridian.com", "Tyler"),
            ("agent.andre@meridian.com", "Andre"),
            ("agent.jasmine@meridian.com", "Jasmine"),
            ("agent.karen@meridian.com", "Karen"),
        ],
    },
)

# Tables we never truncate (migration bookkeeping).
_PROTECTED_TABLES = {"alembic_version"}


def _is_local_database_url(url: str) -> bool:
    lowered = url.lower()
    if "supabase" in lowered:
        return False
    local_markers = ("localhost", "127.0.0.1", "host.docker.internal", "@db:", "@db/")
    return any(marker in lowered for marker in local_markers)


async def _truncate_all_tables(conn) -> list[str]:
    result = await conn.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    )
    tables = [row[0] for row in result.fetchall() if row[0] not in _PROTECTED_TABLES]
    if tables:
        quoted = ", ".join(f'"{name}"' for name in tables)
        await conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    return tables


async def _seed_users(session: AsyncSession, password: str) -> int:
    """Seed each org with one manager + its agent roster. Returns user count."""
    pw_hash = get_password_hash(password)
    user_count = 0
    for spec in _ORGS:
        org = Organization(name=spec["name"], slug=spec["slug"], status=OrgStatus.active)
        session.add(org)
        await session.flush()

        manager_email, manager_name = spec["manager"]
        session.add(
            User(
                organization_id=org.id,
                email=manager_email,
                name=manager_name,
                password_hash=pw_hash,
                role=UserRole.manager,
                is_active=True,
            )
        )
        user_count += 1
        for agent_email, agent_name in spec["agents"]:
            session.add(
                User(
                    organization_id=org.id,
                    email=agent_email,
                    name=agent_name,
                    password_hash=pw_hash,
                    role=UserRole.agent,
                    agent_type=AgentType.human,
                    is_active=True,
                )
            )
            user_count += 1
    return user_count


def _print_credentials(password: str) -> None:
    print("[LOGIN] Email/password — all users share this password:")
    for spec in _ORGS:
        print(f"  manager: {spec['manager'][0]:<26} / {password}")
        for agent_email, _ in spec["agents"]:
            print(f"  agent:   {agent_email:<26} / {password}")


async def _run(args: argparse.Namespace) -> int:
    if not _is_local_database_url(settings.DATABASE_URL):
        print(
            "[ABORT] DATABASE_URL does not look like a local database:\n"
            f"        {settings.DATABASE_URL}\n"
            "        Refusing to truncate a non-local (e.g. Supabase) database.",
            file=sys.stderr,
        )
        return 2

    org_count = len(_ORGS)
    user_count = sum(1 + len(spec["agents"]) for spec in _ORGS)

    if not args.yes:
        print(
            "[DRY RUN] This will TRUNCATE every table in:\n"
            f"          {settings.DATABASE_URL}\n"
            f"          then seed {org_count} orgs and {user_count} users "
            "(managers + agents, no calls/policies/KB).\n"
            "          Re-run with --yes to execute.",
        )
        return 0

    async with engine.begin() as conn:
        truncated = await _truncate_all_tables(conn)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        seeded = await _seed_users(session, args.password)
        await session.commit()

    print(f"[OK] Truncated {len(truncated)} table(s).")
    print(f"[OK] Seeded {org_count} orgs and {seeded} users.")
    _print_credentials(args.password)
    print("[NEXT] Log in at http://localhost:3000, then upload sample audio.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Actually execute (otherwise dry-run).")
    parser.add_argument(
        "--password",
        default="password123",
        help="Local-dev password shared by all seeded users (managers + agents).",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
