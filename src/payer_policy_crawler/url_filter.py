from urllib.parse import urlparse


DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
}


POLICY_KEYWORDS = {
    "medical-policy",
    "medical_policy",
    "medicalpolicy",
    "coverage-policy",
    "coverage_policy",
    "coverage",
    "prior-authorization",
    "prior_authorization",
    "priorauth",
    "precertification",
    "pre-certification",
    "formulary",
    "drug-list",
    "drug_list",
    "provider-manual",
    "provider_manual",
    "bulletin",
}


def get_hostname(url: str) -> str:
    hostname = urlparse(url).hostname

    if not hostname:
        return ""

    return hostname.lower().rstrip(".")


def is_same_domain(url: str, base_url: str) -> bool:
    """
    True when url belongs to the same domain or a subdomain
    of base_url.
    """
    hostname = get_hostname(url)
    base_hostname = get_hostname(base_url)

    if not hostname or not base_hostname:
        return False

    return (
        hostname == base_hostname
        or hostname.endswith(f".{base_hostname}")
    )


def is_document_url(url: str) -> bool:
    path = urlparse(url).path.lower()

    return any(
        path.endswith(extension)
        for extension in DOCUMENT_EXTENSIONS
    )


def looks_like_policy_url(url: str) -> bool:
    parsed = urlparse(url)

    text = f"{parsed.path} {parsed.query}".lower()

    if is_document_url(url):
        return True

    return any(
        keyword in text
        for keyword in POLICY_KEYWORDS
    )


def is_relevant_link(
    url: str,
    anchor_text: str = "",
) -> bool:
    """
    Determine whether a link looks like a policy/document
    candidate.

    Domain ownership is deliberately NOT checked here.
    Domain decisions belong to the discovery layer, where
    the source page and discovery chain are available.
    """
    parsed = urlparse(url)

    if parsed.fragment and not parsed.query:
        return False

    if is_document_url(url):
        return True

    text = (
        f"{parsed.path} "
        f"{parsed.query} "
        f"{anchor_text}"
    ).lower()

    return any(
        keyword in text
        for keyword in POLICY_KEYWORDS
    )