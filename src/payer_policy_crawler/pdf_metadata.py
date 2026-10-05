import re
from datetime import date
from email.utils import parsedate_to_datetime


def month_to_number(month: str) -> int:
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    return months[month.lower()]

import re


import re


def extract_document_title(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    meaningful_lines = []

    for line in lines:
        # Ignore standalone page numbers.
        if re.fullmatch(r"\d+", line):
            continue

        # Ignore standalone years.
        if re.fullmatch(r"\d{4}", line):
            continue

        # Stop before the table of contents.
        if line.lower() == "table of contents":
            break

        meaningful_lines.append(line)

    if not meaningful_lines:
        return ""

    # The first one or two meaningful lines are usually
    # the document title when the heading wraps.
    title_lines = meaningful_lines[:2]

    return " ".join(title_lines)



def extract_effective_date(text: str) -> str:
    match = re.search(
        r"Effective\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+(\d{1,2}),\s+(\d{4})",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    month, day, year = match.groups()

    parsed_date = date(
        int(year),
        month_to_number(month),
        int(day),
    )

    return parsed_date.isoformat()


def extract_last_updated_date(
    text: str,
    last_modified_header: str | None = None,
) -> str:
    """
    Prefer a printed revision/review/update date from the document.

    Fall back to HTTP Last-Modified when no reliable printed
    date can be extracted.
    """

    patterns = [
        r"(?:Last\s+Updated|Last\s+Update|Updated)"
        r"\s*[:\-]?\s*"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+(\d{1,2}),\s+(\d{4})",

        r"(?:Last\s+Reviewed|Last\s+Review|Reviewed)"
        r"\s*[:\-]?\s*"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+(\d{1,2}),\s+(\d{4})",

        r"(?:Revision\s+Date|Revision)"
        r"\s*[:\-]?\s*"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)"
        r"\s+(\d{1,2}),\s+(\d{4})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            month, day, year = match.groups()

            parsed_date = date(
                int(year),
                month_to_number(month),
                int(day),
            )

            return parsed_date.isoformat()

    # Fall back to HTTP Last-Modified.
    if last_modified_header:
        try:
            parsed = parsedate_to_datetime(last_modified_header)
            return parsed.date().isoformat()
        except (TypeError, ValueError, OverflowError):
            pass

    return ""