from dataclasses import dataclass


@dataclass
class CandidateURL:
    payer_name: str
    url: str
    source_page_url: str
    discovery_path: str
    extraction_method: str


@dataclass
class DocumentMetadata:
    document_title: str = ""
    document_type: str = "other"
    file_type: str = "other"
    policy_number: str = ""
    effective_date: str = ""
    last_updated_date: str = ""
    line_of_business: str = "Unknown"
    state_or_region: str = "Unknown"


@dataclass
class DocumentRecord:
    payer_name: str
    payer_alias: str
    state_or_region: str
    line_of_business: str
    document_title: str
    document_type: str
    document_url: str
    source_page_url: str
    discovery_path: str
    file_type: str
    policy_number: str
    effective_date: str
    last_updated_date: str
    http_status: int
    content_hash_sha256: str
    file_size_bytes: int
    requires_auth: str
    render_mode: str
    extraction_method: str
    confidence_score: float
    scrape_timestamp_utc: str
    notes: str