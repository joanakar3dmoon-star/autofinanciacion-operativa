from __future__ import annotations

from pathlib import Path

from .config import settings


def test_package_import() -> None:
    assert settings.project_name == "autofinanciacion-operativa"

