from app.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.workers.job_worker import run_worker


def main() -> None:
    init_db()
    run_worker(SessionLocal, settings.worker_poll_interval)


if __name__ == "__main__":
    main()
