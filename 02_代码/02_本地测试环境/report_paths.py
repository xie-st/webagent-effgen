"""Result folders for local environment checks."""
from datetime import datetime, timezone
from pathlib import Path


def new_environment_result():
    folder = (Path(__file__).resolve().parents[2] / "01_文本/05_测试结果/environment" /
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
    folder.mkdir(parents=True, exist_ok=False)
    return folder
