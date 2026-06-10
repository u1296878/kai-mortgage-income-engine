import urllib.error

from app import __main__ as app_main


def test_main_runs_uvicorn_on_localhost_without_browser(monkeypatch):
    calls = []
    monkeypatch.setattr(
        app_main.uvicorn,
        "run",
        lambda target, host, port: calls.append((target, host, port)),
    )

    app_main.main(["--no-browser", "--port", "8123"])

    assert calls == [("app.main:app", "127.0.0.1", 8123)]


def test_open_when_ready_opens_browser_after_http_response(monkeypatch):
    opened = []
    error = urllib.error.HTTPError("http://127.0.0.1:8123", 404, "Not Found", {}, None)
    monkeypatch.setattr(app_main.urllib.request, "urlopen", lambda url, timeout: (_ for _ in ()).throw(error))
    monkeypatch.setattr(app_main.webbrowser, "open", lambda url: opened.append(url))

    app_main._open_when_ready("http://127.0.0.1:8123", timeout_seconds=1)

    assert opened == ["http://127.0.0.1:8123"]


def test_open_when_ready_keeps_waiting_on_connection_error(monkeypatch):
    opened = []
    times = iter([0, 0, 2])
    monkeypatch.setattr(app_main.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(app_main.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        app_main.urllib.request,
        "urlopen",
        lambda url, timeout: (_ for _ in ()).throw(urllib.error.URLError("refused")),
    )
    monkeypatch.setattr(app_main.webbrowser, "open", lambda url: opened.append(url))

    app_main._open_when_ready("http://127.0.0.1:8123", timeout_seconds=1)

    assert opened == []
