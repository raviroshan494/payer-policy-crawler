import csv
from dataclasses import asdict
from pathlib import Path

from payer_policy_crawler.models import DocumentRecord


OUTPUT_COLUMNS = [
    "payer_name",
    "payer_alias",
    "state_or_region",
    "line_of_business",
    "document_title",
    "document_type",
    "document_url",
    "source_page_url",
    "discovery_path",
    "file_type",
    "policy_number",
    "effective_date",
    "last_updated_date",
    "http_status",
    "content_hash_sha256",
    "file_size_bytes",
    "requires_auth",
    "render_mode",
    "extraction_method",
    "confidence_score",
    "scrape_timestamp_utc",
    "notes",
]


def record_to_row(record: DocumentRecord) -> dict:
    data = asdict(record)

    return {
        column: data[column]
        for column in OUTPUT_COLUMNS
    }


def write_records_csv(
    records: list[DocumentRecord],
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=OUTPUT_COLUMNS,
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writeheader()

        for record in records:
            writer.writerow(record_to_row(record))