from dataclasses import dataclass

from payer_policy_crawler.html_parser import (
    extract_links,
    is_relevant_link,
)
from payer_policy_crawler.http_client import HttpClient
from payer_policy_crawler.models import CandidateURL
from payer_policy_crawler.robots import RobotsChecker
from payer_policy_crawler.sitemap import SitemapParser
from payer_policy_crawler.url_filter import (
    is_document_url,
    looks_like_policy_url,
)
from payer_policy_crawler.url_utils import normalize_url


@dataclass
class DiscoveryResult:
    payer_name: str
    seed_url: str
    candidates: list[CandidateURL]
    pages_checked: list[str]
    notes: list[str]
    status: str


def build_html_candidates(
    payer_name: str,
    page_url: str,
    links,
) -> list[CandidateURL]:

    candidates: list[CandidateURL] = []
    seen_urls: set[str] = set()

    normalized_page_url = normalize_url(
        page_url
    )

    for link in links:

        if not is_relevant_link(
            link.url,
            link.anchor_text,
        ):
            continue

        normalized_url = normalize_url(
            link.url
        )

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)

        candidates.append(
            CandidateURL(
                payer_name=payer_name,
                url=normalized_url,
                source_page_url=normalize_url(
                    link.source_page_url
                ),
                discovery_path=(
                    f"{normalized_page_url} > "
                    f"{normalized_url}"
                ),
                extraction_method=(
                    link.extraction_method
                ),
            )
        )

    return candidates


async def discover_from_page(
    client: HttpClient,
    payer_name: str,
    page_url: str,
) -> list[CandidateURL]:

    result = await client.fetch(page_url)

    if result.status_code != 200:
        return []

    content_type = result.headers.get(
        "content-type",
        "",
    ).lower()

    if "html" not in content_type:
        return []

    links = extract_links(
        html=result.content,
        source_page_url=result.final_url,
    )

    return build_html_candidates(
        payer_name=payer_name,
        page_url=result.final_url,
        links=links,
    )


async def discover_payer(
    client: HttpClient,
    payer_name: str,
    seed_url: str,
    start_pages: list[str],
    ignore_robots: bool = False,
) -> DiscoveryResult:

    candidates: list[CandidateURL] = []
    pages_checked: list[str] = []
    notes: list[str] = []

    seen_candidates: set[str] = set()
    seen_pages: set[str] = set()

    # ---------------------------------------------------------
    # 1. Robots
    # ---------------------------------------------------------

    # ---------------------------------------------------------
# 1. Robots
# ---------------------------------------------------------

    robots_checker = RobotsChecker(client)

    robots_result = await robots_checker.fetch_robots(
        seed_url
    )

    if not robots_result.robots_valid:

        notes.append(
            "robots.txt unavailable or invalid: "
            f"{robots_result.error}"
        )

        if not ignore_robots:
            notes.append(
                "Skipped sitemap and HTML discovery because "
                "robots.txt could not be validated"
            )

            return DiscoveryResult(
                payer_name=payer_name,
                seed_url=seed_url,
                candidates=candidates,
                pages_checked=pages_checked,
                notes=notes,
                status="blocked",
            )

        notes.append(
            "Ignoring robots.txt validation failure "
            "for this run"
        )

    else:

        notes.append(
            "robots.txt fetched successfully"
        )

        if robots_result.robots_blocked and not ignore_robots:

            notes.append(
                "robots.txt indicates crawling is blocked "
                "for the crawler user-agent"
            )

            notes.append(
                "Skipped sitemap and HTML discovery because "
                "crawling is blocked"
            )

            return DiscoveryResult(
                payer_name=payer_name,
                seed_url=seed_url,
                candidates=candidates,
                pages_checked=pages_checked,
                notes=notes,
                status="blocked",
            )

        if robots_result.robots_blocked:

            notes.append(
                "robots.txt crawling restriction ignored "
                "for this run"
            )

        else:

            notes.append(
                "robots.txt allows crawling of the seed URL"
            )    # ---------------------------------------------------------
    # 2. Sitemap discovery
    # ---------------------------------------------------------

    if robots_result.sitemaps:

        notes.append(
            f"Discovered {len(robots_result.sitemaps)} "
            "sitemap(s)"
        )

        sitemap_parser = SitemapParser(client)

        sitemap_documents, failed_sitemaps = (
            await sitemap_parser.collect_urls(
                robots_result.sitemaps
            )
        )

        notes.append(
            f"Sitemap produced "
            f"{len(sitemap_documents)} URL(s)"
        )

        if failed_sitemaps:

            notes.append(
                f"Failed to fetch "
                f"{len(failed_sitemaps)} sitemap(s)"
            )

        for sitemap_url, path in (
            sitemap_documents.items()
        ):

            normalized_sitemap_url = normalize_url(
                sitemap_url
            )

            discovery_path = " > ".join(
                normalize_url(item)
                for item in path
            )

            # Direct document from sitemap
            if is_document_url(
                normalized_sitemap_url
            ):

                if (
                    normalized_sitemap_url
                    in seen_candidates
                ):
                    continue

                seen_candidates.add(
                    normalized_sitemap_url
                )

                candidates.append(
                    CandidateURL(
                        payer_name=payer_name,
                        url=normalized_sitemap_url,
                        source_page_url="",
                        discovery_path=discovery_path,
                        extraction_method="sitemap",
                    )
                )

                continue

            # Relevant HTML page from sitemap
            if not looks_like_policy_url(
                normalized_sitemap_url
            ):
                continue

            if normalized_sitemap_url in seen_pages:
                continue

            seen_pages.add(
                normalized_sitemap_url
            )

            pages_checked.append(
                normalized_sitemap_url
            )

            page_candidates = (
                await discover_from_page(
                    client=client,
                    payer_name=payer_name,
                    page_url=normalized_sitemap_url,
                )
            )

            for candidate in page_candidates:

                if candidate.url in seen_candidates:
                    continue

                seen_candidates.add(
                    candidate.url
                )

                candidates.append(
                    CandidateURL(
                        payer_name=candidate.payer_name,
                        url=candidate.url,
                        source_page_url=(
                            candidate.source_page_url
                        ),
                        discovery_path=(
                            f"{discovery_path} > "
                            f"{candidate.url}"
                        ),
                        extraction_method=(
                            f"sitemap|"
                            f"{candidate.extraction_method}"
                        ),
                    )
                )

    else:

        notes.append(
            "robots.txt did not provide sitemap URLs"
        )

    # ---------------------------------------------------------
    # 3. Start-page discovery
    # ---------------------------------------------------------

    for page_url in start_pages:

        normalized_page_url = normalize_url(
            page_url
        )

        if normalized_page_url in seen_pages:
            continue

        seen_pages.add(
            normalized_page_url
        )

        pages_checked.append(
            normalized_page_url
        )

        page_candidates = (
            await discover_from_page(
                client=client,
                payer_name=payer_name,
                page_url=normalized_page_url,
            )
        )

        for candidate in page_candidates:

            if candidate.url in seen_candidates:
                continue

            seen_candidates.add(
                candidate.url
            )

            candidates.append(candidate)

    # ---------------------------------------------------------
    # 4. One-level recursive HTML discovery
    # ---------------------------------------------------------

    initial_candidates = list(candidates)

    for candidate in initial_candidates:

        if is_document_url(candidate.url):
            continue

        if not looks_like_policy_url(
            candidate.url
        ):
            continue

        if candidate.url in seen_pages:
            continue

        seen_pages.add(candidate.url)

        pages_checked.append(
            candidate.url
        )

        page_candidates = (
            await discover_from_page(
                client=client,
                payer_name=payer_name,
                page_url=candidate.url,
            )
        )

        for nested_candidate in page_candidates:

            if nested_candidate.url in seen_candidates:
                continue

            seen_candidates.add(
                nested_candidate.url
            )

            candidates.append(
                CandidateURL(
                    payer_name=(
                        nested_candidate.payer_name
                    ),
                    url=nested_candidate.url,
                    source_page_url=(
                        nested_candidate.source_page_url
                    ),
                    discovery_path=(
                        f"{candidate.discovery_path} > "
                        f"{nested_candidate.url}"
                    ),
                    extraction_method=(
                        f"{candidate.extraction_method}|"
                        f"{nested_candidate.extraction_method}"
                    ),
                )
            )

    # ---------------------------------------------------------
    # 5. Keep only document candidates
    # ---------------------------------------------------------

    candidates = [
        candidate
        for candidate in candidates
        if is_document_url(candidate.url)
    ]

    notes.append(
        f"Checked {len(pages_checked)} HTML page(s)"
    )

    notes.append(
        f"Discovered {len(candidates)} "
        "candidate document URL(s)"
    )


    if candidates:
        discovery_status = "completed"
    else:
        discovery_status = "no_documents_found"

    return DiscoveryResult(
        payer_name=payer_name,
        seed_url=seed_url,
        candidates=candidates,
        pages_checked=pages_checked,
        notes=notes,
        status=discovery_status,
    )
