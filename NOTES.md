# Engineering Notes

## 1. Approach

The crawler was designed as a configurable, asynchronous discovery pipeline rather
than a collection of payer-specific scrapers.

Each payer is defined in `config/payer_seed_list.csv` using only its name and hint
host. The crawler then discovers the publicly accessible surface dynamically through
`robots.txt`, XML sitemaps, sitemap indexes, HTML pages, document links, and supported
document/viewer URLs.

The main stages are:

1. Load payer seed configuration.
2. Check and parse `robots.txt`.
3. Discover sitemap URLs and crawl sitemap indexes.
4. Discover relevant policy/provider pages.
5. Extract document candidates from accessible pages.
6. Resolve redirects and supported document viewers.
7. Fetch the final document bytes.
8. Extract metadata and classify the document.
9. Calculate SHA-256 and file size.
10. Validate the resulting 22-column record.
11. Persist payer-level results and update the checkpoint.
12. Globally deduplicate document URLs and write the final output.

The implementation deliberately avoids hard-coding payer domains or relying on
payer-specific scraping logic wherever possible.

---

## 2. Discovery and Traceability

A key design goal was to make every document reproducible.

Each document record contains:

- `source_page_url`
- `discovery_path`
- `document_url`
- `extraction_method`

`discovery_path` records the route from the original discovery source to the final
document. Redirects are also preserved where available.

This makes it possible for a reviewer to manually trace how a document was discovered
instead of receiving only a list of URLs with no provenance.

For sitemap- or pattern-based discoveries where there is no conventional source page,
the discovery path records the relevant discovery mechanism.

---

## 3. Redirects and Document Resolution

Payer websites frequently redirect between provider portals, corporate domains,
regional sites, CDN/document-hosting domains, or document viewers.

The crawler therefore follows redirects and uses the final resolved URL as the
`document_url`.

The redirect/resolution chain is retained in `discovery_path` so that the original
candidate and final document location remain traceable.

For viewer-style pages, the crawler attempts to identify an underlying supported
document URL rather than treating the viewer page itself as the document.

---

## 4. Metadata and Confidence

Metadata extraction is intentionally conservative.

The crawler extracts information such as:

- document title
- document type
- policy number
- effective date
- last updated date
- state/region
- line of business
- file type

Dates are intended to represent dates printed in the document. HTTP metadata may be
used as a fallback for `last_updated_date` where appropriate.

The crawler does not attempt to manufacture missing metadata. Fields that cannot be
reliably determined are left empty or marked as `Unknown` where the schema requires a
value.

A deterministic confidence score is generated from signals such as HTTP success,
document availability, metadata quality, document classification, and discovery
traceability. Lower-confidence records are retained rather than discarded so that
the output remains auditable.

---

## 5. Duplicate Handling

The final dataset requires globally unique `document_url` values.

Deduplication is therefore performed across all payers after payer-level crawling,
rather than only within an individual payer.

This is important because the same document can be exposed through multiple payer
pages, regional pages, redirects, or discovery paths.

The final output retains one canonical record for a duplicated document URL.

SHA-256 is calculated from the exact raw bytes returned by the document request. This
provides a deterministic content identifier independent of the document filename or
URL.

---

## 6. Resumability and Failure Handling

Crawler state is maintained in:

`data/checkpoint.json`

Payer-level results are persisted under:

`data/payer_results/`

The checkpoint distinguishes between:

- `pending`
- `running`
- `completed`
- `blocked`
- `no_documents_found`
- `failed`

This allows an interrupted run to resume without unnecessarily repeating completed
payer crawls.

The crawler also writes structured JSONL events to:

`output/run_log.jsonl`

and an aggregated run summary to:

`output/summary.json`

---

## 7. Blocked vs. No Documents Found

These states are intentionally different.

### `no_documents_found`

The crawler was able to access the relevant public discovery surface but did not find
qualifying policy/provider documents through the implemented discovery methods.

### `blocked`

The crawler could not reliably perform discovery because access was prevented or
restricted, for example by robots restrictions or other site-level access behavior.

This distinction avoids incorrectly reporting an inaccessible payer as a payer that
publishes no documents.

---

## 8. Rate Limiting and Crawl Safety

The crawler is designed for public resources and does not attempt to bypass access
controls.

It does not:

- bypass authentication
- solve CAPTCHAs
- bypass WAF/security controls
- use paid proxies to evade restrictions
- access private provider portals

HTTP access uses bounded concurrency and connection pooling. Transient failures
including `429`, `500`, `502`, `503`, and `504` are retried using exponential backoff.
`Retry-After` is honored when supplied by the server.

A descriptive crawler user agent is used for requests.

---

## 9. Known Limitations

Public payer websites are heterogeneous and can change independently of the crawler.

Potential limitations include:

- JavaScript-only document discovery.
- Documents exposed through proprietary viewer applications.
- Site-specific access restrictions.
- Non-standard or unusable `robots.txt` responses.
- Documents requiring authentication.
- Metadata embedded in formats that are difficult to extract reliably.
- Duplicate documents exposed through multiple URLs.
- Websites whose public navigation does not expose all available documents.

The crawler records these situations rather than attempting to circumvent the site's
controls.

The goal is therefore a reproducible and auditable public-document discovery process,
not an attempt to guarantee discovery of every document hosted by every payer.

---

## 10. Output Quality Checks

Before producing the final dataset, records are validated for:

- exact required column set and order
- valid document type and file type values
- valid HTTP status
- valid `Y/N` boolean fields
- valid confidence range
- valid SHA-256 format
- valid file size
- non-empty document URL
- non-empty discovery path
- globally unique document URLs

The final CSV is written as UTF-8 CSV using the required 22-column schema.

---
## 11. Confidence Score Logic

Each document record receives a deterministic `confidence_score` between `0.00`
and `1.00`.

The score is intended to indicate the reliability and completeness of the discovered
record, rather than the probability that the underlying payer document is correct.

The score is calculated from independent signals available during crawling:

| Signal | Score contribution |
|---|---:|
| Successful document HTTP response | +0.20 |
| SHA-256 content hash available | +0.15 |
| Complete discovery path available | +0.15 |
| Document title successfully identified | +0.10 |
| Document type successfully classified | +0.10 |
| File type successfully identified | +0.10 |
| Effective date identified | +0.05 |
| Last-updated date identified | +0.05 |
| Authentication status determined | +0.05 |
| Valid resolved document URL | +0.05 |

The resulting score is capped at `1.00` and written with two decimal places.

For example, a successfully downloaded PDF with a resolved URL, complete discovery
path, title, classification, file type, hash, and authentication status will receive
a substantially higher confidence score than a record where only the URL and HTTP
status are known.

Scores below `0.70` are considered lower-confidence records and should include an
explanation in the `notes` field when the available information is incomplete or
ambiguous.

The confidence score does not cause a document to be discarded. Lower-confidence
records are retained so that the final dataset remains auditable and reviewers can
inspect the underlying discovery information.


---

## 12. Operational UI

A lightweight Streamlit application is included for reviewing crawler results.

It provides:

- overall run metrics
- payer-level status and counts
- document filtering and inspection
- checkpoint state
- structured run-log inspection

The UI reads the generated crawler artifacts and is intentionally separate from the
crawler execution path.

Run it with:

```bash
streamlit run streamlit_app.py
```

## 13. Trade-offs

The implementation favors traceability, safety, and deterministic behavior over
aggressive crawling.

In particular:

Sitemap and public HTML discovery are preferred over uncontrolled site-wide
crawling.
Access restrictions are recorded rather than bypassed.
Missing metadata is preferred over unreliable inference.
Intermediate payer results are persisted to support recovery.
Global URL deduplication prevents duplicate documents in the final dataset.
Structured logs and discovery paths make crawler behavior auditable.

This approach provides a practical foundation that can be extended with additional
payer-specific discovery adapters, headless-browser handling, or other extraction
methods as future requirements.