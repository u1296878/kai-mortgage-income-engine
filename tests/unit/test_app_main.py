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
