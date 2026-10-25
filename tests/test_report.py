import pytest


def event(player, style, attempt, won, duration, run_id="t"):
    return {
        "encounter": "boss",
        "run_id": run_id,
        "player_id": player,
        "player_style": style,
        "attempt": attempt,
        "won": won,
        "duration_s": duration,
    }

SAMPLE = [
    event("a1", "aggressive", 1, False, 50),
    event("a1", "aggressive", 2, False, 60),
    event("a1", "aggressive", 3, True, 90),
    event("a1", "aggressive", 4, False, 40),
    event("a1", "aggressive", 5, True, 100),
    event("a2", "aggressive", 1, True, 80),
    event("a2", "aggressive", 30, True, 70),
    event("a3", "aggressive", 1, False, 30),
    event("a3", "aggressive", 2, False, 30),
    event("c1", "cautious", 1, False, 55),
    event("c1", "cautious", 2, True, 95),
    event("c1", "cautious", 30, False, 45),
]

@pytest.fixture
def report(client):
    response = client.post("/events/bulk", json=SAMPLE)
    assert response.status_code == 201
    return client.get("/encounters/boss/report", params={"run_id": "t"}).json()

def test_first_win_metrics_for_aggressive(report):
    aggressive = report["by_style"]["aggressive"]
    assert aggressive["players"] == 3
    assert aggressive["median_first_win"] == 2.0
    assert aggressive["share_before_attempt_5"] == pytest.approx(2 / 3)
    assert aggressive["share_never_won"] == pytest.approx(1 / 3)

def test_first_win_metrics_for_cautious(report):
    cautious = report["by_style"]["cautious"]
    assert cautious["players"] == 1
    assert cautious["median_first_win"] == 2.0
    assert cautious["share_before_attempt_5"] == 1.0
    assert cautious["share_never_won"] == 0.0

def test_late_win_rate(report):
    assert report["by_style"]["aggressive"]["late_win_rate"] == 1.0
    assert report["by_style"]["cautious"]["late_win_rate"] == 0.0

def test_relapse_rate(report):
    assert report["by_style"]["aggressive"]["relapse_rate"] == pytest.approx(0.2)
    assert report["by_style"]["cautious"]["relapse_rate"] == pytest.approx(0.5)

def test_time_to_kill_averages_only_winning_fights(report):
    assert report["overall"]["time_to_kill_s"] == pytest.approx(87.0)

def test_runs_are_kept_apart(client, report):
    other = [event("z1", "aggressive", 1, True, 10, run_id="other")]
    assert client.post("/events/bulk", json=other).status_code == 201
    again = client.get("/encounters/boss/report", params={"run_id": "t"}).json()
    assert again["by_style"]["aggressive"]["players"] == 3
    only_other = client.get("/encounters/boss/report", params={"run_id": "other"}).json()
    assert only_other["by_style"]["aggressive"]["players"] == 1

def test_unknown_run_is_404_and_missing_run_id_is_422(client):
    assert client.get("/encounters/boss/report", params={"run_id": "nope"}).status_code == 404
    assert client.get("/encounters/boss/report").status_code == 422