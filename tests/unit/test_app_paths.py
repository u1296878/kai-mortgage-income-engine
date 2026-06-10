from pathlib import Path

from app.runtime import app_paths


def test_windows_app_data_dir_uses_local_app_data(monkeypatch):
    monkeypatch.setattr(app_paths.platform, "system", lambda: "Windows")
    monkeypatch.setenv("LOCALAPPDATA", "C:/Users/example/AppData/Local")

    data_dir = app_paths.app_data_dir()

    assert data_dir == Path("C:/Users/example/AppData/Local") / "KaiMortgageIncomeEngine"


def test_macos_app_data_dir_uses_application_support(monkeypatch):
    monkeypatch.setattr(app_paths.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(app_paths.Path, "home", lambda: Path("/Users/example"))

    data_dir = app_paths.app_data_dir()

    assert data_dir == Path("/Users/example/Library/Application Support/KaiMortgageIncomeEngine")


def test_linux_app_data_dir_uses_xdg_data_home(monkeypatch):
    monkeypatch.setattr(app_paths.platform, "system", lambda: "Linux")
    monkeypatch.setenv("XDG_DATA_HOME", "/home/example/.local/state")

    data_dir = app_paths.app_data_dir()

    assert data_dir == Path("/home/example/.local/state/kai-mortgage-income-engine")


def test_linux_app_data_dir_falls_back_to_home(monkeypatch):
    monkeypatch.setattr(app_paths.platform, "system", lambda: "Linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(app_paths.Path, "home", lambda: Path("/home/example"))

    data_dir = app_paths.app_data_dir()

    assert data_dir == Path("/home/example/.local/share/kai-mortgage-income-engine")
