from app.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.job_service import recover_stuck_jobs
from app.workers.job_worker import run_worker


# TODO step: remove (Railway).
def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        recover_stuck_jobs(db)
    finally:
        db.close()
    run_worker(SessionLocal, settings.worker_poll_interval)


if __name__ == "__main__":
    main()
