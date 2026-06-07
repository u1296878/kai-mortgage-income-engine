from app import worker_main


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_main_initializes_db_recovers_jobs_and_runs_worker(monkeypatch):
    calls = []
    db = FakeSession()
    monkeypatch.setattr(worker_main, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(worker_main, "SessionLocal", lambda: db)
    monkeypatch.setattr(
        worker_main,
        "recover_stuck_jobs",
        lambda session: calls.append(("recover_stuck_jobs", session)),
    )
    monkeypatch.setattr(
        worker_main,
        "run_worker",
        lambda db_factory, poll_interval: calls.append((db_factory, poll_interval)),
    )
    monkeypatch.setattr(worker_main.settings, "worker_poll_interval", 7)

    worker_main.main()

    assert calls == [
        "init_db",
        ("recover_stuck_jobs", db),
        (worker_main.SessionLocal, 7),
    ]
    assert db.closed is True
