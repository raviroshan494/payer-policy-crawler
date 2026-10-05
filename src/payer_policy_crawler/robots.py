from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from payer_policy_crawler.http_client import HttpClient


USER_AGENT = "PayerPolicyCrawler/0.1"


@dataclass
class RobotsResult:
    base_url: str
    robots_url: str
    status_code: int
    final_url: str
    robots_available: bool
    robots_valid: bool
    robots_blocked: bool
    sitemaps: list[str]
    redirect_chain: list[str]
    error: str | None = None


class RobotsChecker:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    async def fetch_robots(self, base_url: str) -> RobotsResult:
        parsed = urlparse(base_url)

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        result = await self.client.fetch(robots_url)

        if result.error:
            return RobotsResult(
                base_url=base_url,
                robots_url=robots_url,
                status_code=0,
                final_url=result.final_url,
                robots_available=False,
                robots_valid=False,
                robots_blocked=False,
                sitemaps=[],
                redirect_chain=result.redirect_chain,
                error=result.error,
            )

        if result.status_code != 200:
            return RobotsResult(
                base_url=base_url,
                robots_url=robots_url,
                status_code=result.status_code,
                final_url=result.final_url,
                robots_available=False,
                robots_valid=False,
                robots_blocked=False,
                sitemaps=[],
                redirect_chain=result.redirect_chain,
                error=f"robots.txt returned HTTP {result.status_code}",
            )

        # A 200 response isn't necessarily a robots.txt response.
        # Geisinger currently redirects /robots.txt to a maintenance page.
        final_path = urlparse(result.final_url).path.lower()

        if not final_path.endswith("/robots.txt"):
            return RobotsResult(
                base_url=base_url,
                robots_url=robots_url,
                status_code=result.status_code,
                final_url=result.final_url,
                robots_available=False,
                robots_valid=False,
                robots_blocked=False,
                sitemaps=[],
                redirect_chain=result.redirect_chain,
                error="robots.txt redirected to a non-robots resource",
            )

        text = result.content.decode("utf-8", errors="replace")

        parser = RobotFileParser()
        parser.set_url(result.final_url)
        parser.parse(text.splitlines())

        sitemaps = [
            urljoin(result.final_url, sitemap)
            for sitemap in parser.site_maps() or []
        ]

        robots_blocked = not parser.can_fetch(
            USER_AGENT,
            base_url,
        )

        return RobotsResult(
            base_url=base_url,
            robots_url=robots_url,
            status_code=result.status_code,
            final_url=result.final_url,
            robots_available=True,
            robots_valid=True,
            robots_blocked=robots_blocked,
            sitemaps=sitemaps,
            redirect_chain=result.redirect_chain,
        )