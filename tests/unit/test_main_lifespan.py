import pytest
from fastapi import FastAPI

from app import main as main_module


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_lifespan_seeds_manager_without_starting_worker(monkeypatch):
    calls = []
    db = FakeSession()
    monkeypatch.setattr(main_module, "init_db", lambda: calls.append("init_db"))
    monkeypatch.setattr(main_module, "SessionLocal", lambda: db)
    monkeypatch.setattr(
        main_module,
        "seed_manager",
        lambda session: calls.append(("seed_manager", session)),
    )

    async with main_module.lifespan(FastAPI()):
        pass

    assert calls == [
        "init_db",
        ("seed_manager", db),
    ]
    assert db.closed is True
