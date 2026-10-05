import json
from pathlib import Path


CHECKPOINT_PATH = Path("data/checkpoint.json")

VALID_STATUSES = {
    "pending",
    "running",
    "completed",
    "blocked",
    "no_documents_found",
    "failed",
}


class Checkpoint:
    def __init__(
        self,
        path: Path = CHECKPOINT_PATH,
    ) -> None:
        self.path = path
        self.data: dict[str, str] = self.load()

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text()
        )

    def save(self) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.path.with_suffix(
            ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                self.data,
                indent=2,
            )
        )

        temporary_path.replace(
            self.path
        )

    def get_status(
        self,
        payer_name: str,
    ) -> str:
        return self.data.get(
            payer_name,
            "pending",
        )

    def set_status(
        self,
        payer_name: str,
        status: str,
    ) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid checkpoint status: {status}"
            )

        self.data[payer_name] = status
        self.save()

    def mark_running(
        self,
        payer_name: str,
    ) -> None:
        self.set_status(
            payer_name,
            "running",
        )

    def mark_completed(
        self,
        payer_name: str,
    ) -> None:
        self.set_status(
            payer_name,
            "completed",
        )

    def mark_blocked(
        self,
        payer_name: str,
    ) -> None:
        self.set_status(
            payer_name,
            "blocked",
        )

    def mark_no_documents_found(
        self,
        payer_name: str,
    ) -> None:
        self.set_status(
            payer_name,
            "no_documents_found",
        )

    def mark_failed(
        self,
        payer_name: str,
    ) -> None:
        self.set_status(
            payer_name,
            "failed",
        )

    def is_completed(
        self,
        payer_name: str,
    ) -> bool:
        return (
            self.get_status(payer_name)
            == "completed"
        )