from payer_policy_crawler.models import DocumentMetadata


def calculate_confidence(
    metadata: DocumentMetadata,
    http_status: int,
    content_hash: str,
    discovery_path: str,
    requires_auth: str,
    document_url: str,
) -> float:
    score = 0.0

    # Successfully fetched document.
    if http_status == 200:
        score += 0.20

    # Actual file bytes were retrieved and hashed.
    if content_hash:
        score += 0.20

    # We have a reproducible discovery path.
    if discovery_path:
        score += 0.15

    # Document has a valid resolved URL.
    if document_url:
        score += 0.05

    # Document has a title.
    if metadata.document_title:
        score += 0.10

    # Document type was classified.
    if metadata.document_type != "other":
        score += 0.10

    # File type was detected.
    if metadata.file_type != "other":
        score += 0.05

    # Effective date was extracted.
    if metadata.effective_date:
        score += 0.05

    # Last updated date was found.
    if metadata.last_updated_date:
        score += 0.05

    # No authentication was required.
    if requires_auth == "N":
        score += 0.05

    return round(min(score, 1.0), 2)