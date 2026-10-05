import json
from dataclasses import asdict
from pathlib import Path

from payer_policy_crawler.models import DocumentRecord


RESULTS_DIR = Path("data/payer_results")


def payer_filename(payer_name: str) -> str:
    safe_name = "".join(
        char if char.isalnum() else "_"
        for char in payer_name
    )

    return f"{safe_name}.json"


def save_payer_records(
    payer_name: str,
    records: list[DocumentRecord],
) -> Path:
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = RESULTS_DIR / payer_filename(
        payer_name
    )

    payload = {
        "payer_name": payer_name,
        "record_count": len(records),
        "records": [
            asdict(record)
            for record in records
        ],
    }

    temp_path = output_path.with_suffix(".tmp")

    temp_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp_path.replace(output_path)

    return output_path


def load_payer_records(
    payer_name: str,
) -> list[DocumentRecord]:

    path = RESULTS_DIR / payer_filename(
        payer_name
    )

    if not path.exists():
        return []

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return [
        DocumentRecord(**record)
        for record in payload.get(
            "records",
            [],
        )
    ]


def load_all_payer_records() -> list[DocumentRecord]:
    if not RESULTS_DIR.exists():
        return []

    records: list[DocumentRecord] = []

    for path in sorted(
        RESULTS_DIR.glob("*.json")
    ):
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        for record in payload.get(
            "records",
            [],
        ):
            records.append(
                DocumentRecord(**record)
            )

    return records