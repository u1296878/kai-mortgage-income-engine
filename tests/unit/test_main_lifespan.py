import pytest
from fastapi import FastAPI
from threading import Event

from app import main as main_module
from app.runtime import worker_runtime


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_lifespan_recovers_stuck_jobs_and_starts_worker(monkeypatch):
    calls = []
    db = FakeSession()
    monkeypatch.setattr(main_module, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(main_module, "SessionLocal", lambda: db)
    monkeypatch.setattr(
        main_module,
        "seed_manager",
        lambda session: calls.append(("seed_manager", session)),
    )
    monkeypatch.setattr(
        main_module,
        "recover_stuck_jobs",
        lambda session: calls.append(("recover_stuck_jobs", session)),
    )
    monkeypatch.setattr(
        main_module,
        "start_worker",
        lambda db_factory, poll_interval: calls.append(
            ("start_worker", db_factory, poll_interval),
        ),
    )
    monkeypatch.setattr(
        main_module,
        "stop_worker",
        lambda timeout: calls.append(("stop_worker", timeout)),
    )

    async with main_module.lifespan(FastAPI()):
        pass

    assert calls[:3] == [
        "init_db",
        ("seed_manager", db),
        ("recover_stuck_jobs", db),
    ]
    assert calls[3][0] == "start_worker"
    assert calls[3][1] is main_module.SessionLocal
    assert calls[3][2] == main_module.settings.worker_poll_interval
    assert calls[4] == ("stop_worker", main_module.settings.worker_poll_interval + 2)
    assert db.closed is True


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_worker_thread(monkeypatch):
    started = Event()
    db = FakeSession()

    def fake_run_worker(db_factory, poll_interval, stop_event):
        started.set()
        stop_event.wait()

    worker_runtime.stop_worker(0.1)
    monkeypatch.setattr(main_module, "init_db", lambda: None)
    monkeypatch.setattr(main_module, "SessionLocal", lambda: db)
    monkeypatch.setattr(main_module, "seed_manager", lambda session: None)
    monkeypatch.setattr(main_module, "recover_stuck_jobs", lambda session: None)
    monkeypatch.setattr(worker_runtime, "run_worker", fake_run_worker)
    monkeypatch.setattr(main_module, "start_worker", worker_runtime.start_worker)
    monkeypatch.setattr(main_module, "stop_worker", worker_runtime.stop_worker)
    monkeypatch.setattr(main_module.settings, "worker_poll_interval", 1)

    async with main_module.lifespan(FastAPI()):
        assert started.wait(timeout=1)
        thread = worker_runtime.get_worker_thread()
        assert thread is not None
        assert thread.is_alive()

    thread = worker_runtime.get_worker_thread()
    assert thread is not None
    assert not thread.is_alive()
