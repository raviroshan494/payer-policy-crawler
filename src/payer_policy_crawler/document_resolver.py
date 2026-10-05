from dataclasses import dataclass

from payer_policy_crawler.html_parser import extract_viewer_pdf_url
from payer_policy_crawler.http_client import FetchResult, HttpClient


@dataclass
class ResolvedDocument:
    requested_url: str
    document_url: str
    fetch_result: FetchResult
    render_mode: str
    extraction_method: str
    resolution_path: list[str]


def _append_unique(path: list[str], url: str) -> None:
    """Append a URL only if it is different from the previous URL."""
    if not path or path[-1] != url:
        path.append(url)


async def resolve_document(client, url):
    result = await client.fetch(url)

    resolution_path = []
    _append_unique(resolution_path, url)
    _append_unique(resolution_path, result.final_url)

    if result.content.startswith(b"%PDF-"):
        return ResolvedDocument(
            requested_url=url,
            document_url=result.final_url,
            fetch_result=result,
            render_mode="static",
            extraction_method="url_pattern",
            resolution_path=resolution_path,
        )

    viewer_pdf_url = extract_viewer_pdf_url(result.content)

    if viewer_pdf_url:
        # The viewer URL is a temporary signed URL.
        # Use it internally to fetch the PDF, but don't expose it
        # in the reproducible discovery path.
        pdf_result = await client.fetch(viewer_pdf_url)

        if pdf_result.content.startswith(b"%PDF-"):
            return ResolvedDocument(
                requested_url=url,
                document_url=result.final_url,
                fetch_result=pdf_result,
                render_mode="static",
                extraction_method="regex",
                resolution_path=resolution_path,
            )

    return ResolvedDocument(
        requested_url=url,
        document_url=result.final_url,
        fetch_result=result,
        render_mode="static",
        extraction_method="css_selector",
        resolution_path=resolution_path,
    )