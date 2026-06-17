"""user avatar_url column

Revision ID: 0003_user_avatar
Revises: 0002_notif_and_dispute
Create Date: 2026-06-17 22:00:00 UTC

Adds ``users.avatar_url`` (nullable TEXT) so the account-settings page can store
a profile picture. Idempotent so it is safe to re-run against a DB that was
hand-patched out-of-band.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_user_avatar"
down_revision: Union[str, Sequence[str], None] = "0002_notif_and_dispute"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT NULL;")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS avatar_url;")
