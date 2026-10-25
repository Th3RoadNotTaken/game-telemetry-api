import argparse
import csv

import httpx2

BATCH_SIZE = 500

INT_COLUMNS = ("attempt", "heals_used", "heals_interrupted")
FLOAT_COLUMNS = (
    "skill",
    "duration_s",
    "damage_taken",
    "damage_in_recovery",
    "time_spent_healing_s",
)


def row_to_event(raw: dict, encounter: str, run_id: str) -> dict:
    event = {
        "encounter": encounter,
        "run_id": run_id,
        "player_id": raw["player_id"],
        "player_style": raw["player_style"],
        "won": raw["won"].strip().lower() == "true",
    }
    for name in INT_COLUMNS:
        if name in raw:
            event[name] = int(raw[name])
    for name in FLOAT_COLUMNS:
        if name in raw:
            event[name] = float(raw[name])
    return event


def main() -> None:
    parser = argparse.ArgumentParser(description="Load a Copilot telemetry CSV into the API")
    parser.add_argument("csv_path")
    parser.add_argument("--encounter", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8") as f:
        events = [row_to_event(raw, args.encounter, args.run_id) for raw in csv.DictReader(f)]

    total = 0
    with httpx2.Client(base_url=args.url, timeout=30) as client:
        for start in range(0, len(events), BATCH_SIZE):
            batch = events[start:start + BATCH_SIZE]
            response = client.post("/events/bulk", json=batch)
            response.raise_for_status()
            total += response.json()["inserted"]
    print(f"Loaded {total} events into run '{args.run_id}'")


if __name__ == "__main__":
    main()