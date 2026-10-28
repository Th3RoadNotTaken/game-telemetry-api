import logging
import time
import uuid

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Body
from sqlalchemy import Integer, cast, func, select, text
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.models import Base, Event
from app.schemas import EventIn, EventOut, Report, StyleReport, OverallReport

from app.logging_config import setup_logging

LATE_FROM_ATTEMPT = 30

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

setup_logging()
logger = logging.getLogger("app.requests")
app = FastAPI(title="Game Telemetry API", lifespan=lifespan)

@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request",
        extra={"extra_fields": {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }},
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}


@app.post("/events", response_model=EventOut, status_code=201)
def create_event(event: EventIn, db: Session = Depends(get_db)):
    row = Event(**event.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@app.post("/events/bulk", status_code=201)
def create_events_bulk(
    events: Annotated[list[EventIn], Body(min_length=1, max_length=1000)],
    db: Session = Depends(get_db),
):
    db.add_all([Event(**e.model_dump()) for e in events])
    db.commit()
    return {"inserted": len(events)}

@app.get("/encounters/{encounter}/report", response_model=Report)
def encounter_report(encounter: str, run_id: str, db: Session = Depends(get_db)):
    per_player = (
        select(
            Event.player_style,
            Event.player_id,
            func.min(Event.attempt).filter(Event.won).label("first_win"),
        )
        .where(Event.encounter == encounter, Event.run_id == run_id)
        .group_by(Event.player_style, Event.player_id)
        .subquery()
    )
    stmt = select(
        per_player.c.player_style,
        func.count(),
        func.percentile_cont(0.5).within_group(per_player.c.first_win),
        func.count().filter(per_player.c.first_win < 5),
        func.count().filter(per_player.c.first_win.is_(None)),
    ).group_by(per_player.c.player_style)
    rows = db.execute(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail="no events for this encounter and run")

    late_stmt = (
        select(Event.player_style, func.avg(cast(Event.won, Integer)))
        .where(
            Event.encounter == encounter,
            Event.run_id == run_id,
            Event.attempt >= LATE_FROM_ATTEMPT,
        )
        .group_by(Event.player_style)
    )
    late = dict(db.execute(late_stmt).all())

    relapse_stmt = (
        select(Event.player_style, func.avg(cast(~Event.won, Integer)))
        .join(per_player, Event.player_id == per_player.c.player_id)
        .where(
            Event.encounter == encounter,
            Event.run_id == run_id,
            Event.attempt >= per_player.c.first_win,
        )
        .group_by(Event.player_style)
    )
    relapse = dict(db.execute(relapse_stmt).all())
    time_to_kill = db.execute(
        select(func.avg(Event.duration_s)).where(
            Event.encounter == encounter,
            Event.run_id == run_id,
            Event.won,
        )
    ).scalar()

    return Report(
        encounter=encounter,
        run_id=run_id,
        by_style={
            style: StyleReport(
                players=players,
                median_first_win=median,
                share_before_attempt_5=early / players,
                share_never_won=never / players,
                late_win_rate=late.get(style),
                relapse_rate=relapse.get(style),
            )
            for style, players, median, early, never in rows
        },
	overall=OverallReport(time_to_kill_s=time_to_kill),
    )