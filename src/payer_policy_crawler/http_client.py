import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx


USER_AGENT = "PayerPolicyCrawler/0.1"

MAX_CONNECTIONS = 10
MAX_KEEPALIVE_CONNECTIONS = 10

MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 8.0


@dataclass
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content: bytes
    redirect_chain: list[str]
    error: Optional[str] = None


class HttpClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": USER_AGENT,
            },
            limits=httpx.Limits(
                max_connections=MAX_CONNECTIONS,
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
            ),
        )

        # Additional application-level concurrency protection.
        self._semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

    async def fetch(self, url: str) -> FetchResult:
        async with self._semaphore:
            return await self._fetch_with_retry(url)

    async def _fetch_with_retry(self, url: str) -> FetchResult:
        last_error: Optional[str] = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self.client.get(url)

                if (
                    response.status_code not in RETRYABLE_STATUS_CODES
                    or attempt >= MAX_RETRIES
                ):
                    redirect_chain = [
                        str(redirect.url)
                        for redirect in response.history
                    ]

                    return FetchResult(
                        requested_url=url,
                        final_url=str(response.url),
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        content=response.content,
                        redirect_chain=redirect_chain,
                    )

                retry_after = self._get_retry_after(response)

                if retry_after is not None:
                    delay = min(
                        retry_after,
                        MAX_BACKOFF_SECONDS,
                    )
                else:
                    delay = min(
                        INITIAL_BACKOFF_SECONDS * (2**attempt),
                        MAX_BACKOFF_SECONDS,
                    )

                await asyncio.sleep(delay)

            except httpx.RequestError as exc:
                last_error = str(exc)

                if attempt >= MAX_RETRIES:
                    break

                delay = min(
                    INITIAL_BACKOFF_SECONDS * (2**attempt),
                    MAX_BACKOFF_SECONDS,
                )

                await asyncio.sleep(delay)

        return FetchResult(
            requested_url=url,
            final_url=url,
            status_code=0,
            headers={},
            content=b"",
            redirect_chain=[],
            error=last_error or "Request failed after retries",
        )

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> Optional[float]:
        value = response.headers.get("Retry-After")

        if not value:
            return None

        try:
            return float(value)
        except ValueError:
            return None

    async def close(self) -> None:
        await self.client.aclose()