import argparse
import time
import urllib.error
import urllib.request
import webbrowser
from threading import Thread
from typing import Sequence

import uvicorn

from app.config import settings


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Kai Mortgage Income Engine locally.")
    parser.add_argument("--port", type=int, default=settings.app_port)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser and not settings.no_browser:
        Thread(target=_open_when_ready, args=(url,), daemon=True).start()

    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port)


def _open_when_ready(url: str, timeout_seconds: float = 15) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                pass
        except urllib.error.HTTPError:
            # Any HTTP response means the local server is listening.
            pass
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
            continue
        webbrowser.open(url)
        return


if __name__ == "__main__":
    main()
