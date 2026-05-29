from app import worker_main


def test_main_initializes_db_and_runs_worker(monkeypatch):
    calls = []
    monkeypatch.setattr(worker_main, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(
        worker_main,
        "run_worker",
        lambda db_factory, poll_interval: calls.append((db_factory, poll_interval)),
    )
    monkeypatch.setattr(worker_main.settings, "worker_poll_interval", 7)

    worker_main.main()

    assert calls == ["init_db", (worker_main.SessionLocal, 7)]
