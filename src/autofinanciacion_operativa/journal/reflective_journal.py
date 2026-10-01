from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class ReflectiveJournal:
    """Stores structured decisions and portfolio context for future audit and reasoning."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def append_decision(self, decision: Dict[str, Any]) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
        }
        file_path = self.directory / f"decision_{timestamp}.json"
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return file_path
