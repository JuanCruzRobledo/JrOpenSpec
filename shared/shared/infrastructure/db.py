"""Database infrastructure: async engine, session factory, and safe commit."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import settings
from shared.exceptions import AppError, DuplicateError

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for FastAPI Depends injection."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def safe_commit(session: AsyncSession) -> None:
    """Attempt to commit the session, rolling back on errors.

    Catches IntegrityError (duplicate/constraint violations) and
    generic SQLAlchemyError, rolling back the transaction and raising
    domain-specific exceptions.
    """
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.warning("IntegrityError during commit: %s", exc.orig)
        raise DuplicateError(
            message="Resource already exists or constraint violated",
            detail=str(exc.orig),
        ) from exc
    except SQLAlchemyError as exc:
        await session.rollback()
        logger.error("SQLAlchemyError during commit: %s", exc)
        raise AppError(
            message="Database error occurred",
            detail=str(exc),
        ) from exc
