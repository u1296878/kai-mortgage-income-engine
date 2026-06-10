import os
import platform
from pathlib import Path


APP_DIR_NAME = "KaiMortgageIncomeEngine"
LINUX_DIR_NAME = "kai-mortgage-income-engine"


def app_data_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return _windows_data_dir()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    return _linux_data_dir()


def _windows_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_DIR_NAME
    return Path.home() / "AppData" / "Local" / APP_DIR_NAME


def _linux_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / LINUX_DIR_NAME
    return Path.home() / ".local" / "share" / LINUX_DIR_NAME
