import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path("output/run_log.jsonl")


class RunLogger:
    def __init__(
        self,
        path: Path = LOG_PATH,
    ) -> None:
        self.path = path
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def log(
        self,
        event: str,
        **data: Any,
    ) -> None:
        record = {
            "timestamp_utc": (
                datetime.now(timezone.utc)
                .strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            ),
            "event": event,
            **data,
        }

        with self.path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )