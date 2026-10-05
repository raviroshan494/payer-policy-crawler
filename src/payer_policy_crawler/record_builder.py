from datetime import datetime, timezone
from payer_policy_crawler.url_utils import normalize_url
from payer_policy_crawler.models import (
    CandidateURL,
    DocumentMetadata,
    DocumentRecord,
)
from payer_policy_crawler.document_resolver import ResolvedDocument
from payer_policy_crawler.file_metadata import file_size_bytes, sha256_hex
from payer_policy_crawler.confidence import calculate_confidence
from payer_policy_crawler.record_validator import validate_record


def combine_extraction_methods(
    discovery_method: str,
    resolution_method: str,
) -> str:
    methods = []

    for method in (discovery_method, resolution_method):
        for item in method.split("|"):
            item = item.strip()
            if item and item not in methods:
                methods.append(item)

    return "|".join(methods)

def build_document_record(
    candidate: CandidateURL,
    resolved: ResolvedDocument,
    metadata: DocumentMetadata,
) -> DocumentRecord:
    result = resolved.fetch_result

    discovery_path = candidate.discovery_path

    if len(resolved.resolution_path) > 1:
        discovery_path += " > " + " > ".join(
            resolved.resolution_path[1:]
        )

    confidence_score = calculate_confidence(
    metadata=metadata,
    http_status=result.status_code,
    content_hash=sha256_hex(result.content),
    discovery_path=discovery_path,
    requires_auth="N",
    document_url=resolved.document_url,
)


    record =  DocumentRecord(
        payer_name=candidate.payer_name,
        payer_alias="",
        state_or_region=metadata.state_or_region,
        line_of_business=metadata.line_of_business,
        document_title=metadata.document_title,
        document_type=metadata.document_type,
        document_url=normalize_url(resolved.document_url),
        source_page_url=candidate.source_page_url,
        discovery_path=discovery_path,
        file_type=metadata.file_type,
        policy_number=metadata.policy_number,
        effective_date=metadata.effective_date,
        last_updated_date=metadata.last_updated_date,
        http_status=result.status_code,
        content_hash_sha256=sha256_hex(result.content),
        file_size_bytes=file_size_bytes(result.content),
        requires_auth="N",
        render_mode=resolved.render_mode,
        extraction_method=combine_extraction_methods(candidate.extraction_method,resolved.extraction_method),
        confidence_score=confidence_score,
        scrape_timestamp_utc=datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        notes="",
    )
    validate_record(record)
    return record