import asyncio
from dataclasses import dataclass

from payer_policy_crawler.discovery import discover_payer
from payer_policy_crawler.document_resolver import resolve_document
from payer_policy_crawler.file_detector import detect_file_type
from payer_policy_crawler.http_client import HttpClient
from payer_policy_crawler.metadata_extractor import extract_metadata
from payer_policy_crawler.models import CandidateURL, DocumentRecord
from payer_policy_crawler.pdf_parser import extract_pdf_text
from payer_policy_crawler.record_builder import build_document_record


DOCUMENT_CONCURRENCY = 10


@dataclass
class CrawlResult:
    payer_name: str
    records: list[DocumentRecord]
    candidates: int
    successful_documents: int
    failed_documents: int
    status: str
    notes: list[str]



async def process_candidate(
    client: HttpClient,
    candidate: CandidateURL,
    semaphore: asyncio.Semaphore,
) -> DocumentRecord | None:

    async with semaphore:

        try:
            resolved = await resolve_document(
                client=client,
                url=candidate.url,
            )

            result = resolved.fetch_result

            if result.status_code != 200:
                print(
                    f"SKIPPED: {candidate.url} "
                    f"| HTTP {result.status_code}"
                )
                return None

            if not result.content:
                print(
                    f"SKIPPED: {candidate.url} "
                    f"| Empty response"
                )
                return None

            file_type = detect_file_type(
                content=result.content,
                content_type=result.headers.get(
                    "content-type"
                ),
                url=resolved.document_url,
            )

            if file_type != "pdf":
                print(
                    f"SKIPPED: {candidate.url} "
                    f"| Detected file type: {file_type}"
                )
                return None

            text = extract_pdf_text(
                result.content
            )

            metadata = extract_metadata(
                text=text,
                file_type=file_type,
                last_modified_header=result.headers.get(
                    "last-modified"
                ),
            )

            return build_document_record(
                candidate=candidate,
                resolved=resolved,
                metadata=metadata,
            )

        except Exception as exc:
            print(
                f"FAILED: {candidate.url}\n"
                f"Error: {exc}"
            )
            return None


async def crawl_payer(
    client: HttpClient,
    payer_name: str,
    seed_url: str,
    start_pages: list[str],
    ignore_robots: bool = False,
) -> CrawlResult:

    discovery = await discover_payer(
        client=client,
        payer_name=payer_name,
        seed_url=seed_url,
        start_pages=start_pages,
        ignore_robots=ignore_robots,
    )

    candidates = discovery.candidates


    semaphore = asyncio.Semaphore(
        DOCUMENT_CONCURRENCY
    )

    tasks = [
        asyncio.create_task(
            process_candidate(
                client=client,
                candidate=candidate,
                semaphore=semaphore,
            )
        )
        for candidate in candidates
    ]

    records: list[DocumentRecord] = []

    for index, task in enumerate(
        asyncio.as_completed(tasks),
        start=1,
    ):
        record = await task

        print(
            f"[{payer_name}] "
            f"Completed candidate "
            f"{index}/{len(candidates)}"
        )

        if record is not None:
            records.append(record)

    successful_documents = len(records)

    failed_documents = (
        len(candidates)
        - successful_documents
    )

    notes = list(discovery.notes)

    notes.append(
        f"Successfully processed "
        f"{successful_documents} document(s)"
    )

    notes.append(
        f"Failed/skipped "
        f"{failed_documents} candidate(s)"
    )

    notes.append(
        f"Document concurrency: "
        f"{DOCUMENT_CONCURRENCY}"
    )

    return CrawlResult(
        payer_name=discovery.payer_name,
        records=records,
        candidates=len(candidates),
        successful_documents=successful_documents,
        failed_documents=failed_documents,
        status=discovery.status,
        notes=notes,
    )

