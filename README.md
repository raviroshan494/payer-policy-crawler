# Payer Policy Crawler

A production-oriented asynchronous Python crawler for discovering publicly available
medical-policy and provider documents across U.S. healthcare payer websites.

The crawler starts from a configurable list of payer seed domains, discovers relevant
pages and documents through robots.txt, sitemaps, HTML links, and document viewers,
downloads accessible documents, extracts metadata, validates the results, and produces
a normalized 22-column output dataset with full discovery traceability.

---

## Features

- Crawls all configured payer seed domains asynchronously.
- Respects `robots.txt` and avoids authenticated/private content.
- Discovers documents through:
  - `robots.txt`
  - XML sitemaps / sitemap indexes
  - HTML links
  - recursive policy-page discovery
  - direct document URLs
  - embedded/viewer PDF resolution
- Supports PDF, DOC, DOCX, XLS, and XLSX document detection.
- Follows HTTP redirects and records the resolved document URL.
- Captures a reproducible `discovery_path` from seed domain to document.
- Computes SHA-256 hashes from the exact downloaded bytes.
- Extracts document metadata where available.
- Classifies discovered documents into policy/document categories.
- Applies bounded concurrency, retries, exponential backoff, and `Retry-After`.
- Produces structured JSONL execution logs.
- Maintains per-payer checkpoints for resumable runs.
- Persists payer-level intermediate results.
- Performs global URL deduplication before producing the final output.
- Includes a Streamlit dashboard for inspecting crawler results and execution logs.

---

## Project Structure

```text
payer-policy-crawler/
├── config/
│   └── payer_seed_list.csv
│
├── data/
│   ├── checkpoint.json
│   └── payer_results/
│       ├── UHC.json
│       ├── Cigna.json
│       └── ...
│
├── output/
│   ├── output.csv
│   ├── summary.json
│   └── run_log.jsonl
│
├── src/
│   └── payer_policy_crawler/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── models.py
│       ├── http_client.py
│       ├── robots.py
│       ├── sitemap.py
│       ├── discovery.py
│       ├── url_filter.py
│       ├── url_utils.py
│       ├── html_parser.py
│       ├── document_resolver.py
│       ├── file_detector.py
│       ├── file_metadata.py
│       ├── pdf_parser.py
│       ├── pdf_metadata.py
│       ├── document_classifier.py
│       ├── metadata_extractor.py
│       ├── confidence.py
│       ├── record_builder.py
│       ├── record_validator.py
│       ├── dedup.py
│       ├── payer_runner.py
│       ├── payer_storage.py
│       ├── checkpoint.py
│       ├── output.py
│       ├── summary.py
│       └── run_logger.py
│
├── tests/
│
├── streamlit_app.py
├── pyproject.toml
├── README.md
└── NOTES.md
```

## Core Modules

| Module | Responsibility |
| --- | --- |
| `main.py` | Main CLI entry point and overall crawl orchestration |
| `config.py` | Loads and validates payer seed configuration |
| `models.py` | Defines crawler candidates, metadata, and output record models |
| `http_client.py` | Async HTTP client with connection limits, retries, backoff, and redirects |
| `robots.py` | Retrieves and evaluates `robots.txt` and discovers sitemap references |
| `sitemap.py` | Parses sitemap indexes and URL sets |
| `discovery.py` | Coordinates payer-level URL and document discovery |
| `url_filter.py` | Identifies likely policy/document URLs using generic rules |
| `url_utils.py` | URL normalization and removal of tracking/session parameters |
| `html_parser.py` | Extracts links and document references from HTML |
| `document_resolver.py` | Resolves redirects and document/viewer URLs |
| `file_detector.py` | Determines document/file type |
| `file_metadata.py` | Calculates raw document size and SHA-256 hash |
| `pdf_parser.py` | Extracts text from PDF documents |
| `pdf_metadata.py` | Extracts metadata such as dates and document title from PDFs |
| `document_classifier.py` | Classifies documents into policy/document categories |
| `metadata_extractor.py` | Builds structured metadata from discovered documents |
| `confidence.py` | Calculates deterministic record confidence scores |
| `record_builder.py` | Builds the final 22-column document record |
| `record_validator.py` | Validates output schema and field constraints |
| `dedup.py` | Performs global document URL deduplication |
| `payer_runner.py` | Executes the document crawl for an individual payer |
| `payer_storage.py` | Persists and reloads per-payer results |
| `checkpoint.py` | Maintains resumable payer crawl state |
| `output.py` | Writes the final CSV output |
| `summary.py` | Generates payer and overall run summaries |
| `run_logger.py` | Writes structured JSONL execution logs |
| `streamlit_app.py` | Dashboard for crawler status, documents, and logs |

## Architecture at a glance

```text
                    payer_seed_list.csv
                            │
                            ▼
                       config.py
                            │
                            ▼
                        main.py
                            │
                            ▼
                     payer_runner.py
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
         discovery.py                checkpoint.py
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
    robots  sitemap  HTML discovery
       │      │        │
       └──────┼────────┘
              ▼
        document candidates
              │
              ▼
      document_resolver.py
              │
              ▼
       document download
              │
       ┌──────┴───────────┐
       ▼                  ▼
 file_detector       PDF/parser/metadata
       │                  │
       └────────┬─────────┘
                ▼
        record_builder.py
                │
                ▼
       record_validator.py
                │
                ▼
       payer_storage.py
                │
                ▼
          Global dedup
                │
                ▼
           output.csv
```

## Installation

Python 3.12+ is recommended.

```bash
python -m venv venv
source venv/bin/activate

pip install -e .
```

For the Streamlit dashboard:

```bash
pip install streamlit
```

## Running the Crawler

Run the complete crawl with:

```bash
payer-policy-crawler
```

Payers are configured in:

`config/payer_seed_list.csv`

Example:

```text
payer_name,hint_host
UHC,uhcprovider.com
Horizon BCBS NJ,horizonblue.com
Cigna,cigna.com
UPMC Health Plan,upmchealthplan.com
Elevance / Anthem,anthem.com
CareSource,caresource.com
Centene,centene.com
Geisinger,geisinger.org
Highmark,highmark.com
BCBST (BCBS Tennessee),bcbst.com
```

No payer domains are hard-coded into the crawler.

## Discovery Flow

For each payer, the crawler follows approximately:

```text
Seed Domain
    ↓
robots.txt
    ↓
Sitemap Discovery
    ↓
Sitemap URLs / HTML Pages
    ↓
Policy Candidate Pages
    ↓
Document Candidates
    ↓
Redirect / Viewer Resolution
    ↓
Document Fetch
    ↓
Metadata Extraction
    ↓
Validation
    ↓
Per-Payer Persistence
```

Every discovered document retains a `source_page_url` and a `discovery_path` where
available, allowing the discovery route to be manually reproduced.

A path may look like:

`seed URL > sitemap > policy page > document URL > final redirected document URL`

## Output

The primary result is:

`output/output.csv`

It follows the required 22-column schema:

```text
payer_name
payer_alias
state_or_region
line_of_business
document_title
document_type
document_url
source_page_url
discovery_path
file_type
policy_number
effective_date
last_updated_date
http_status
content_hash_sha256
file_size_bytes
requires_auth
render_mode
extraction_method
confidence_score
scrape_timestamp_utc
notes
```

document_url is globally deduplicated before the final CSV is written.

Missing metadata is represented as an empty string where appropriate. Metadata that
cannot be reliably determined is not intentionally inferred beyond the crawler's
limited deterministic classification rules.

## Resumability

Crawler progress is stored in:

`data/checkpoint.json`

Supported payer states include:

- `pending`
- `running`
- `completed`
- `blocked`
- `no_documents_found`
- `failed`

Completed payer results are persisted under:

`data/payer_results/`

This allows interrupted executions to resume without unnecessarily repeating
successfully completed payer crawls.

## Logging and Run Summary

Structured execution logs are written as JSON Lines:

`output/run_log.jsonl`

Each event contains a UTC timestamp, event type, and structured event data.

The aggregated run summary is written to:

`output/summary.json`

The summary records payer-level status, discovered candidates, successful documents,
failed documents, and relevant crawler notes.

The crawler distinguishes successful discovery from conditions such as:

- documents discovered successfully
- no documents discovered from the accessible public surface
- discovery blocked by site behavior / robots restrictions
- crawler or transport failure

This distinction prevents an inaccessible site from being incorrectly reported as a
payer publishing no documents.

## Crawl Safety

The crawler operates only against publicly accessible resources.

It does not attempt to:

- bypass authentication
- solve or bypass CAPTCHAs
- bypass WAF/security controls
- use proxies to evade restrictions
- access authenticated provider portals

HTTP requests use bounded concurrency and connection pools. Transient failures such
as HTTP 429, 500, 502, 503, and 504 are retried using exponential backoff,
with Retry-After honored when provided.

### Confidence Scoring

Each document receives a deterministic `0.00–1.00` confidence score based on
signals such as HTTP success, URL resolution, discovery traceability, document
metadata, file identification, hashing, and authentication detection.

The detailed scoring methodology is documented in `NOTES.md`.

## Streamlit Dashboard

A lightweight dashboard is included for reviewing crawler execution and output.

Run:

```bash
streamlit run streamlit_app.py
```

The dashboard provides:

- overall crawler metrics
- payer-level crawl status
- candidate/success/failure counts
- checkpoint state
- discovered document browsing and filtering
- document-type and line-of-business filtering
- structured execution-log inspection

The dashboard reads the crawler artifacts directly and does not modify crawler state.


## Design Notes

The implementation intentionally favors deterministic and traceable extraction over
aggressive crawling.

Some payer websites may block automated access, return non-standard robots.txt
responses, redirect between domains, or expose documents through viewer applications.
These cases are recorded rather than bypassed.

Document metadata such as policy number, effective date, region, or line of business
is populated only when it can be extracted or deterministically identified with
reasonable confidence. Ambiguous fields are left empty/unknown rather than silently
fabricated.

Additional implementation decisions, limitations, and payer-specific observations are
documented in `NOTES.md`.