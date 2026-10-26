# Game Telemetry API

[![CI](https://github.com/Th3RoadNotTaken/game-telemetry-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Th3RoadNotTaken/game-telemetry-api/actions/workflows/ci.yml)

A small backend service that stores play events from a game and answers one question: **did this tuning pass hit its design targets?**

I'm a game designer working on combat and enemy AI. My other project, the [Design Tuning Copilot](https://github.com/Th3RoadNotTaken/design-tuning-copilot), simulates souls like boss playtests, checks the results against design targets, and asks an LLM to propose tuning changes. This API is the data service that could sit behind it. It takes raw per attempt events, and returns metrics in exactly the shape the Copilot's targets use, so the output is ready to hand to an LLM or compare against a target file.

The API does not call an LLM itself. It stores and measures. The Copilot decides.

All data in this repo is simulated. Nothing comes from a real game or a studio.

## What it does

* Stores one event per player attempt: encounter, run, player, play style, attempt number, win or loss, fight duration, plus optional fields like skill and damage taken.
* Groups events by a `run_id`, so a "before" and an "after" tuning pass stay separate and a report always describes exactly one run.
* Returns a per encounter report with the same metrics the Copilot's targets use, split by play style (aggressive and cautious):
  * `median_first_win`: the median attempt number of a player's first win
  * `share_before_attempt_5`: how many players won within their first 4 attempts
  * `share_never_won`: how many players never won
  * `late_win_rate`: win rate once players have had time to learn (attempt 30 onward)
  * `relapse_rate`: how often a player loses after they have already won once
  * `time_to_kill_s`: average duration of winning fights, overall
* Validates every incoming event, and rejects a whole bulk upload if one row is bad.

## Stack

* **FastAPI** for the REST API, with **Pydantic** models for validation
* **PostgreSQL 17** with **SQLAlchemy 2.0** (psycopg 3 driver)
* **Docker** and **Docker Compose** for the API and the database
* **pytest** against a real Postgres test database
* **GitHub Actions** running the test suite on every push and pull request

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Is the API up |
| GET | `/health/db` | Can the API reach Postgres (returns 503 if not) |
| POST | `/events` | Store one event |
| POST | `/events/bulk` | Store 1 to 1000 events in a single all or nothing transaction |
| GET | `/encounters/{encounter}/report?run_id=...` | Metrics for one encounter and one run, split by play style |

Interactive docs are served at `/docs` once the API is running.

### Example report

```json
{
  "encounter": "boss",
  "run_id": "after",
  "by_style": {
    "aggressive": {
      "players": 60,
      "median_first_win": 10.0,
      "share_before_attempt_5": 0.033,
      "share_never_won": 0.0,
      "late_win_rate": 0.52,
      "relapse_rate": 0.536
    },
    "cautious": {
      "players": 60,
      "median_first_win": 11.0,
      "share_before_attempt_5": 0.017,
      "share_never_won": 0.0,
      "late_win_rate": 0.882,
      "relapse_rate": 0.23
    }
  },
  "overall": { "time_to_kill_s": 95.68 }
}
```

I loaded the Copilot's simulated "before" and "after" playtests (4,800 events each, 120 players each) and checked that the SQL reports match the Copilot's own Python metrics exactly.

## Run it locally

You need Docker. Copy the example environment file and start everything:

```powershell
copy .env.example .env
docker compose up -d --build
```

Then open http://127.0.0.1:8000/docs.

The database runs in its own container with a named volume, so your data survives restarts. The API waits for the database healthcheck to pass before it starts.

### Load the Copilot's simulated playtests

```powershell
python scripts/load_csv.py path\to\telemetry_before.csv --encounter boss --run-id before
python scripts/load_csv.py path\to\telemetry_after.csv --encounter boss --run-id after
```

Then try `/encounters/boss/report?run_id=before` and `run_id=after`.

### Run the tests

Create a virtual environment, install the dependencies, and run pytest. Postgres needs to be running (for example `docker compose up -d db`).

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
```

The tests create their own `telemetry_test` database, so they never touch your dev data. The report tests use a small hand computed sample, so every expected number can be checked by hand.

## Design decisions

**A real Postgres in tests, not mocks.** The report endpoint is mostly SQL (medians, filtered counts, joins). A mocked database would test nothing that can actually go wrong, so the tests and CI run against a real Postgres instead.

**`run_id` is required.** A tuning loop compares passes, so every event belongs to a run, and a report always covers exactly one run.

**Bulk upload is all or nothing.** One transaction, capped at 1000 events. If one row is invalid, nothing is stored, so a half loaded run can't quietly skew results.

**Config from environment variables.** Settings come from env vars (and a gitignored `.env` locally). CI and containers use the same names, and no credentials are committed.

**The container runs as a non root user.** The Dockerfile copies `requirements.txt` first so dependency layers stay cached when only app code changes.

**Pinned dependencies.** `requirements.txt` holds exact versions so local, Docker, and CI builds all install the same libraries.

## Known limitations

I'd rather list these than hide them.

* **No migrations yet.** Tables are created with `create_all` on startup. A real deployment should use Alembic.
* **Loads aren't idempotent.** Loading the same CSV twice under the same run ID stores duplicates. A unique constraint on (encounter, run, player, attempt) is the fix.
* **One event per attempt.** The model assumes one row per attempt, and a loss means the player died. Separate death or hit events aren't stored yet.
* **First win averages have survivorship bias.** Players who never win don't appear in the first win median. That's why `share_never_won` is reported next to it.
* **Some CSV columns aren't stored or reported yet** (damage and healing details).
* **Report queries are computed on demand.** Fine at this size, but a cache would help with large runs.

## Roadmap

* JSON structured logs and a `/metrics` endpoint
* Locust load test, including bulk versus single inserts
* Deploy to AWS (EC2 with Docker, managed Postgres on RDS)
* Redis cache for reports
* An LLM ready summary endpoint that compares a report against a targets file

## Project layout

```
app/
  main.py        endpoints and report queries
  config.py      settings from environment variables
  db.py          engine and session
  models.py      the events table
  schemas.py     Pydantic request and response models
scripts/
  load_csv.py    loads Copilot CSVs through the bulk endpoint
tests/           pytest suite with a real test database
.github/workflows/ci.yml
Dockerfile
docker-compose.yml
```
