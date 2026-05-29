from threading import Event

from sqlalchemy.orm import sessionmaker

from app.audit.logger import log_event
from app.services import job_processing_service


def run_worker(
    db_factory: sessionmaker,
    poll_interval_seconds: int = 5,
    stop_event: Event | None = None,
) -> None:
    worker_stop_event = stop_event or Event()
    log_event("worker_started", {"poll_interval_seconds": poll_interval_seconds})
    _worker_loop(db_factory, poll_interval_seconds, worker_stop_event)


def process_next_job(db) -> bool:
    return job_processing_service.process_next_job(db)


def _worker_loop(
    db_factory: sessionmaker,
    poll_interval_seconds: int,
    stop_event: Event,
) -> None:
    while not stop_event.is_set():
        db = db_factory()
        try:
            process_next_job(db)
        except Exception as error:
            log_event("worker_error", {"error": str(error)})
        finally:
            db.close()
        if stop_event.wait(poll_interval_seconds):
            break
