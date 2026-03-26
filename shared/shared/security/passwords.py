"""Password hashing and verification using passlib + bcrypt.

bcrypt is CPU-intensive, so verify runs in a thread executor
to avoid blocking the async event loop.
"""

import asyncio
from functools import partial

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt. Synchronous — safe for seed scripts."""
    return pwd_context.hash(password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Runs in a thread executor to avoid blocking the event loop
    since bcrypt verification is CPU-bound.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        partial(pwd_context.verify, plain_password, hashed_password),
    )
