from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Death(Base):
    __tablename__ = "deaths"
    __table_args__ = (UniqueConstraint("source_key", name="uq_death_source_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    victim: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    killer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    happened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    guild: Mapped[str] = mapped_column(String(40), default="unknown", index=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
