import pytest
from pydantic import ValidationError

from app.schemas import EventIn


def valid_event():
    return {
        "encounter": "bell_warden",
	"run_id": "baseline",
        "player_id": "p12",
        "player_style": "aggressive",
        "attempt": 4,
        "won": False,
        "duration_s": 63.2,
    }


def test_valid_event_parses():
    event = EventIn(**valid_event())
    assert event.attempt == 4
    assert event.won is False


def test_negative_duration_is_rejected():
    with pytest.raises(ValidationError):
        EventIn(**{**valid_event(), "duration_s": -1})


def test_attempt_zero_is_rejected():
    with pytest.raises(ValidationError):
        EventIn(**{**valid_event(), "attempt": 0})


def test_missing_player_id_is_rejected():
    data = valid_event()
    del data["player_id"]
    with pytest.raises(ValidationError):
        EventIn(**data)

def test_optional_fields_default_to_none():
    event = EventIn(**valid_event())
    assert event.skill is None


def test_missing_run_id_is_rejected():
    data = valid_event()
    del data["run_id"]
    with pytest.raises(ValidationError):
        EventIn(**data)