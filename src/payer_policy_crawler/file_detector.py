from urllib.parse import urlparse


def detect_file_type(
    content: bytes,
    content_type: str | None,
    url: str,
) -> str:
    content_type = (content_type or "").lower().split(";")[0].strip()
    path = urlparse(url).path.lower()

    # Magic bytes first
    if content.startswith(b"%PDF-"):
        return "pdf"

    if content.startswith(b"PK\x03\x04"):
        if path.endswith(".docx"):
            return "docx"
        if path.endswith(".xlsx"):
            return "xlsx"

    if content.startswith(b"\xD0\xCF\x11\xE0"):
        if path.endswith(".doc"):
            return "doc"
        if path.endswith(".xls"):
            return "xls"

    # Content-Type fallback
    if content_type == "application/pdf":
        return "pdf"

    if content_type in {
        "application/msword",
    }:
        return "doc"

    if content_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        return "docx"

    if content_type in {
        "application/vnd.ms-excel",
    }:
        return "xls"

    if content_type in {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }:
        return "xlsx"

    if content_type in {
        "text/html",
        "application/xhtml+xml",
    }:
        return "html"

    return "other"