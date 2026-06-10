from threading import Event, Thread

from sqlalchemy.orm import sessionmaker

from app.workers.job_worker import run_worker


_worker_stop_event = Event()
_worker_thread: Thread | None = None


def start_worker(
    db_factory: sessionmaker,
    poll_interval_seconds: int,
) -> Thread:
    global _worker_thread

    if _worker_thread is not None and _worker_thread.is_alive():
        return _worker_thread

    _worker_stop_event.clear()
    _worker_thread = Thread(
        target=run_worker,
        args=(db_factory, poll_interval_seconds, _worker_stop_event),
        daemon=True,
        name="kai-job-worker",
    )
    _worker_thread.start()
    return _worker_thread


def stop_worker(timeout_seconds: float) -> Thread | None:
    thread = _worker_thread
    if thread is None:
        return None

    _worker_stop_event.set()
    thread.join(timeout=timeout_seconds)
    return thread


def get_worker_thread() -> Thread | None:
    return _worker_thread
