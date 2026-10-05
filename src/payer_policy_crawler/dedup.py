from payer_policy_crawler.models import DocumentRecord


def deduplicate_records(
    records: list[DocumentRecord],
) -> tuple[list[DocumentRecord], int]:
    """
    Remove duplicate document URLs globally.

    Returns:
        (deduplicated_records, duplicate_count)
    """
    seen_urls: set[str] = set()
    unique_records: list[DocumentRecord] = []
    duplicate_count = 0

    for record in records:
        document_url = record.document_url

        if document_url in seen_urls:
            duplicate_count += 1
            continue

        seen_urls.add(document_url)
        unique_records.append(record)

    return unique_records, duplicate_count