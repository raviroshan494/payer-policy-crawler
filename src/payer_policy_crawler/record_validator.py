from payer_policy_crawler.models import DocumentRecord
from payer_policy_crawler.output import OUTPUT_COLUMNS


DOCUMENT_TYPES = {
    "medical_policy",
    "coverage_guideline",
    "pa_list",
    "formulary",
    "drug_list",
    "provider_manual",
    "bulletin",
    "other",
}

FILE_TYPES = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "html",
    "other",
}

RENDER_MODES = {
    "static",
    "headless",
    "api",
}


def validate_record(record: DocumentRecord) -> None:
    data = record.__dict__

    missing_columns = [
        column
        for column in OUTPUT_COLUMNS
        if column not in data
    ]

    if missing_columns:
        raise ValueError(
            f"Missing output columns: {missing_columns}"
        )

    if record.document_type not in DOCUMENT_TYPES:
        raise ValueError(
            f"Invalid document_type: {record.document_type}"
        )

    if record.file_type not in FILE_TYPES:
        raise ValueError(
            f"Invalid file_type: {record.file_type}"
        )

    if record.render_mode not in RENDER_MODES:
        raise ValueError(
            f"Invalid render_mode: {record.render_mode}"
        )

    if record.requires_auth not in {"Y", "N"}:
        raise ValueError(
            f"requires_auth must be Y/N: {record.requires_auth}"
        )

    if not 0.0 <= record.confidence_score <= 1.0:
        raise ValueError(
            f"Invalid confidence_score: {record.confidence_score}"
        )

    if record.http_status < 0:
        raise ValueError(
            f"Invalid http_status: {record.http_status}"
        )

    if record.file_size_bytes < 0:
        raise ValueError(
            f"Invalid file_size_bytes: {record.file_size_bytes}"
        )

    if len(record.content_hash_sha256) != 64:
        raise ValueError(
            "content_hash_sha256 must be a SHA-256 hex string"
        )

    if record.content_hash_sha256 != record.content_hash_sha256.lower():
        raise ValueError(
            "content_hash_sha256 must be lowercase"
        )

    if not record.document_url:
        raise ValueError("document_url cannot be empty")

    if not record.source_page_url:
        raise ValueError("source_page_url cannot be empty")

    if not record.discovery_path:
        raise ValueError("discovery_path cannot be empty")