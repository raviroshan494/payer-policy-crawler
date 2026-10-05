from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


DOWNLOAD_PARAMETERS = {
    "t.download",
    "download",
}


WIDEN_TEMPORARY_PARAMETERS = {
    "u",
}


def normalize_url(url: str) -> str:
    parts = urlsplit(url)

    hostname = parts.hostname.lower() if parts.hostname else ""

    ignored_parameters = set(TRACKING_PARAMETERS)
    ignored_parameters.update(DOWNLOAD_PARAMETERS)

    # Widen document/view URLs use "u" as a delivery/view parameter.
    if hostname.endswith(("widen.net", "widencdn.net")):
        ignored_parameters.update(WIDEN_TEMPORARY_PARAMETERS)

    query = [
        (key, value)
        for key, value in parse_qsl(
            parts.query,
            keep_blank_values=True,
        )
        if key.lower() not in ignored_parameters
    ]

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path or "/",
            urlencode(query),
            "",
        )
    )