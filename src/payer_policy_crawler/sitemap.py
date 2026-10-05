from dataclasses import dataclass
from xml.etree import ElementTree

from payer_policy_crawler.http_client import HttpClient


MAX_SITEMAPS = 100


@dataclass
class SitemapResult:
    url: str
    status_code: int
    final_url: str
    sitemap_urls: list[str]
    document_urls: list[str]
    error: str | None = None


class SitemapParser:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    async def fetch(self, url: str) -> SitemapResult:
        result = await self.client.fetch(url)

        if result.error:
            return SitemapResult(
                url=url,
                status_code=0,
                final_url=result.final_url,
                sitemap_urls=[],
                document_urls=[],
                error=result.error,
            )

        if result.status_code != 200:
            return SitemapResult(
                url=url,
                status_code=result.status_code,
                final_url=result.final_url,
                sitemap_urls=[],
                document_urls=[],
                error=f"HTTP {result.status_code}",
            )

        try:
            root = ElementTree.fromstring(result.content)
        except ElementTree.ParseError as exc:
            return SitemapResult(
                url=url,
                status_code=result.status_code,
                final_url=result.final_url,
                sitemap_urls=[],
                document_urls=[],
                error=f"Invalid XML: {exc}",
            )

        namespace = ""

        if root.tag.startswith("{"):
            namespace = root.tag.split("}", 1)[0] + "}"

        sitemap_urls: list[str] = []
        document_urls: list[str] = []

        if root.tag.endswith("sitemapindex"):
            for element in root.findall(f"{namespace}sitemap"):
                loc = element.find(f"{namespace}loc")

                if loc is not None and loc.text:
                    sitemap_urls.append(loc.text.strip())

        elif root.tag.endswith("urlset"):
            for element in root.findall(f"{namespace}url"):
                loc = element.find(f"{namespace}loc")

                if loc is not None and loc.text:
                    document_urls.append(loc.text.strip())

        return SitemapResult(
            url=url,
            status_code=result.status_code,
            final_url=result.final_url,
            sitemap_urls=sitemap_urls,
            document_urls=document_urls,
        )

    async def collect_urls(
        self,
        sitemap_urls: list[str],
        ) -> tuple[dict[str, list[str]], list[str]]:
        visited: set[str] = set()
        document_paths: dict[str, list[str]] = {}
        failed_sitemaps: list[str] = []

        queue = [
            (sitemap_url, [sitemap_url])
            for sitemap_url in sitemap_urls
        ]

        while queue and len(visited) < MAX_SITEMAPS:
            sitemap_url, discovery_path = queue.pop(0)

            if sitemap_url in visited:
                continue

            visited.add(sitemap_url)

            result = await self.fetch(sitemap_url)

            if result.error:
                failed_sitemaps.append(sitemap_url)
                continue

            for document_url in result.document_urls:
                document_paths.setdefault(
                    document_url,
                    discovery_path + [document_url],
                )

            for child_url in result.sitemap_urls:
                if child_url not in visited:
                    queue.append(
                        (
                            child_url,
                            discovery_path + [child_url],
                        )
                    )

        return document_paths, failed_sitemaps