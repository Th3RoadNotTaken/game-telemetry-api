import random

from locust import HttpUser, between, task

def make_event():
    return {
        "encounter": "boss",
        "run_id": "loadtest",
        "player_id": f"player-{random.randint(1, 100000)}",
        "player_style": random.choice(["aggressive", "cautious"]),
        "attempt": random.randint(1, 40),
        "won": random.random() < 0.5,
        "duration_s": round(random.uniform(30, 120), 1),
    }

class SingleEventUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def post_one_event(self):
        self.client.post("/events", json=make_event())


class BulkEventUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def post_fifty_events(self):
        self.client.post("/events/bulk", json=[make_event() for _ in range(50)])