"""Session service — validates table join requests and issues HMAC tokens.

Pure business logic — no FastAPI imports.
Implements the contract: POST /api/sessions/join
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.exceptions import ConflictError, NotFoundError
from shared.models.core.branch import Branch
from shared.models.room.sector import Sector
from shared.models.room.table import Table
from shared.security.table_tokens import generate_table_token

logger = logging.getLogger(__name__)

# Token lifetime: 3 hours
TOKEN_TTL_SECONDS = 3 * 60 * 60


class SessionService:
    """Handles the session join flow for customer-facing QR entry.

    Responsibilities:
    - Validate the branch exists and is not soft-deleted
    - Validate the table belongs to the branch and is active (status != 'inactive')
    - Generate an HMAC-SHA256 table token
    - Return session payload

    The service does NOT create DB records for the session — the concept of a
    persistent TableSession in the DB belongs to Phase 5 (table-staff-domain).
    For Phase 6 (pwa-menu-base), the token itself IS the session credential.
    """

    def __init__(self, db: AsyncSession, secret: str) -> None:
        self._db = db
        self._secret = secret

    async def join_session(
        self,
        branch_slug: str,
        table_identifier: str,
        display_name: str,
        avatar_color: str,
        locale: str,
    ) -> dict:
        """Validate table access and issue a session token.

        Args:
            branch_slug: Branch identifier from the QR URL.
            table_identifier: Table number/identifier (e.g. "5").
            display_name: Optional customer display name.
            avatar_color: Customer's chosen avatar color (hex).
            locale: Customer's preferred locale (e.g. "es").

        Returns:
            Dict with token, sessionId, expiresAt, branch, table.

        Raises:
            NotFoundError: Branch or table not found.
            ConflictError: Table is not active.
        """
        # Resolve branch
        branch = await self._get_branch_by_slug(branch_slug)

        # Resolve table via sector join — Table has no direct branch_id,
        # it belongs to Sector which belongs to Branch
        table = await self._get_table_by_branch_and_identifier(branch.id, table_identifier)

        # Guard: inactive tables cannot accept new sessions
        if table.status == "inactive":
            raise ConflictError("Table is not active")

        # Phase 6 has no persistent TableSession record yet, and the token helper
        # still requires an integer session_id for downstream compatibility.
        # Expose a public UUID session identifier for the approved join contract,
        # while keeping the integer surrogate only inside the signed token payload.
        token_session_id = table.id
        response_session_id = str(uuid4())

        now_unix = int(time.time())
        expires_at = datetime.fromtimestamp(now_unix + TOKEN_TTL_SECONDS, tz=UTC)

        token = generate_table_token(
            secret=self._secret,
            branch_id=branch.id,
            table_id=table.id,
            session_id=token_session_id,
            ttl=TOKEN_TTL_SECONDS,
        )

        logger.info(
            "Session joined: branch=%s table=%s locale=%s",
            branch_slug,
            table_identifier,
            locale,
        )

        return {
            "token": token,
            "sessionId": response_session_id,
            "expiresAt": expires_at,
            "branch": {
                "id": branch.id,
                "name": branch.name,
                "slug": branch.slug,
            },
            "table": {
                "identifier": table.number,
                "displayName": self._format_table_display_name(table.number),
            },
        }

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    async def _get_branch_by_slug(self, slug: str) -> Branch:
        result = await self._db.execute(
            select(Branch).where(
                Branch.slug == slug,
                Branch.deleted_at.is_(None),
            )
        )
        branch = result.scalar_one_or_none()
        if branch is None:
            raise NotFoundError("Branch or table not found")
        return branch

    def _format_table_display_name(self, table_identifier: str) -> str:
        normalized = table_identifier.strip()
        if not normalized:
            return "Mesa"

        mesa_match = re.match(r"^mesa[-_\s]*(.+)$", normalized, flags=re.IGNORECASE)
        if mesa_match:
            suffix = mesa_match.group(1).strip()
            return f"Mesa {suffix}" if suffix else "Mesa"

        return normalized if normalized.lower().startswith("mesa ") else f"Mesa {normalized}"

    async def _get_table_by_branch_and_identifier(
        self, branch_id: int, table_identifier: str
    ) -> Table:
        """Resolve a table by branch_id + table number via Sector join."""
        result = await self._db.execute(
            select(Table)
            .join(Sector, Sector.id == Table.sector_id)
            .where(
                Sector.branch_id == branch_id,
                Table.number == table_identifier,
                Sector.deleted_at.is_(None),
            )
            .options(joinedload(Table.sector))
        )
        table = result.scalars().first()
        if table is None:
            raise NotFoundError("Branch or table not found")
        return table
