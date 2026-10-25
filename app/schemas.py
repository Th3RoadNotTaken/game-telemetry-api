from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventIn(BaseModel):
    encounter: str = Field(min_length=1, max_length=64)
    run_id: str = Field(min_length=1, max_length=64)
    player_id: str = Field(min_length=1, max_length=64)
    player_style: str = Field(min_length=1, max_length=32)
    attempt: int = Field(ge=1)
    won: bool
    duration_s: float = Field(ge=0, le=3600)
    skill: float | None = Field(default=None, ge=0, le=1)
    damage_taken: float | None = Field(default=None, ge=0)
    damage_in_recovery: float | None = Field(default=None, ge=0)
    heals_used: int | None = Field(default=None, ge=0)
    heals_interrupted: int | None = Field(default=None, ge=0)
    time_spent_healing_s: float | None = Field(default=None, ge=0)

class EventOut(EventIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class StyleReport(BaseModel):
    players: int
    median_first_win: float | None
    share_before_attempt_5: float
    share_never_won: float
    late_win_rate: float | None
    relapse_rate: float | None

class OverallReport(BaseModel):
    time_to_kill_s: float | None

class Report(BaseModel):
    encounter: str
    run_id: str
    by_style: dict[str, StyleReport]
    overall: OverallReport