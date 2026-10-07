from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse


@dataclass
class PageLink:
    url: str
    source_page_url: str
    anchor_text: str
    extraction_method: str = "css_selector"


def extract_links(
    html: bytes,
    source_page_url: str,
) -> list[PageLink]:
    soup = BeautifulSoup(html, "lxml")

    links: list[PageLink] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()

        if not href:
            continue

        absolute_url = urljoin(source_page_url, href)

        anchor_text = anchor.get_text(
            " ",
            strip=True,
        )

        links.append(
            PageLink(
                url=absolute_url,
                source_page_url=source_page_url,
                anchor_text=anchor_text,
            )
        )

    return links



POLICY_KEYWORDS = {
    "medical policy",
    "medical-policy",
    "coverage policy",
    "coverage-policy",
    "prior authorization",
    "prior-authorization",
    "precertification",
    "formulary",
    "drug list",
    "drug-list",
    "provider manual",
    "provider-manual",
    "policy",
}



DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
}


def is_document_link(url: str) -> bool:
    path = urlparse(url).path.lower()

    return any(
        path.endswith(extension)
        for extension in DOCUMENT_EXTENSIONS
    )


def is_relevant_link(url: str, anchor_text: str) -> bool:
    parsed = urlparse(url)

    # Ignore same-page fragment navigation.
    if parsed.fragment and not parsed.query:
        return False

    if is_document_link(url):
        return True

    text = f"{parsed.path} {parsed.query} {anchor_text}".lower()

    return any(
        keyword in text
        for keyword in POLICY_KEYWORDS
    )





def extract_viewer_pdf_url(html: bytes) -> str | None:
    text = html.decode("utf-8", errors="replace")

    match = re.search(
        r"window\.viewerPdfUrl\s*=\s*['\"]([^'\"]+)",
        text,
    )

    if not match:
        return None

    return match.group(1)