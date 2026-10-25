from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (Index("ix_events_encounter_run", "encounter", "run_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter: Mapped[str] = mapped_column(String(64))
    run_id: Mapped[str] = mapped_column(String(64))
    player_id: Mapped[str] = mapped_column(String(64))
    player_style: Mapped[str] = mapped_column(String(32))
    attempt: Mapped[int]
    won: Mapped[bool]
    duration_s: Mapped[float]
    skill: Mapped[float | None]
    damage_taken: Mapped[float | None]
    damage_in_recovery: Mapped[float | None]
    heals_used: Mapped[int | None]
    heals_interrupted: Mapped[int | None]
    time_spent_healing_s: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )