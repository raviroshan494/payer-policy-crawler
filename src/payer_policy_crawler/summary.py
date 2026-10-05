import json
from pathlib import Path
from typing import Any


SUMMARY_PATH = Path("output/summary.json")


def build_payer_summary(
    payer_name: str,
    status: str,
    candidates: int,
    successful_documents: int,
    failed_documents: int,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "payer_name": payer_name,
        "status": status,
        "candidates": candidates,
        "successful_documents": successful_documents,
        "failed_documents": failed_documents,
        "notes": notes or [],
    }


def write_summary(
    payer_summaries: list[dict[str, Any]],
    output_path: Path = SUMMARY_PATH,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_candidates = sum(
        item["candidates"]
        for item in payer_summaries
    )

    total_successful = sum(
        item["successful_documents"]
        for item in payer_summaries
    )

    total_failed = sum(
        item["failed_documents"]
        for item in payer_summaries
    )

    completed = sum(
        item["status"] == "completed"
        for item in payer_summaries
    )

    failed = sum(
        item["status"] == "failed"
        for item in payer_summaries
    )

    pending = sum(
        item["status"] == "pending"
        for item in payer_summaries
    )

    running = sum(
        item["status"] == "running"
        for item in payer_summaries
    )

    payload = {
        "overall": {
            "payers_attempted": len(
                payer_summaries
            ),
            "payers_completed": completed,
            "payers_failed": failed,
            "payers_pending": pending,
            "payers_running": running,
            "total_candidates": total_candidates,
            "total_successful_documents": (
                total_successful
            ),
            "total_failed_documents": total_failed,
        },
        "payers": payer_summaries,
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