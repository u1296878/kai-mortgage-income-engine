import pytest
from fastapi import FastAPI

from app import main as main_module


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_lifespan_recovers_stuck_jobs_after_seed(monkeypatch):
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
    monkeypatch.setattr(main_module, "run_worker", lambda *args: None)

    async with main_module.lifespan(FastAPI()):
        pass

    assert calls[:3] == [
        "init_db",
        ("seed_manager", db),
        ("recover_stuck_jobs", db),
    ]
    assert db.closed is True
