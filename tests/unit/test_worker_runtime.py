from threading import Event

from app.runtime import worker_runtime


def test_worker_runtime_starts_and_stops_thread(monkeypatch):
    started = Event()

    def fake_run_worker(db_factory, poll_interval, stop_event):
        started.set()
        stop_event.wait()

    worker_runtime.stop_worker(0.1)
    monkeypatch.setattr(worker_runtime, "run_worker", fake_run_worker)

    thread = worker_runtime.start_worker(lambda: None, 1)

    assert started.wait(timeout=1)
    assert thread.is_alive()

    stopped_thread = worker_runtime.stop_worker(1)

    assert stopped_thread is thread
    assert not thread.is_alive()
