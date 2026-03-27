"""TextureProfile model — system + tenant-scoped texture descriptor."""

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import BaseModel


class TextureProfile(BaseModel):
    """Texture profile (e.g., Crocante, Cremoso, Suave)."""

    __table_args__ = (
        UniqueConstraint("code", "tenant_id", name="uq_texture_profiles_code_tenant"),
        CheckConstraint(
            "is_system = false OR tenant_id IS NULL",
            name="ck_texture_profiles_system_no_tenant",
        ),
    )

    tenant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
