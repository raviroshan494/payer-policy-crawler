from payer_policy_crawler.document_classifier import classify_document
from payer_policy_crawler.models import DocumentMetadata
from payer_policy_crawler.pdf_metadata import (
    extract_document_title,
    extract_effective_date,
    extract_last_updated_date,
)


import re


def infer_state_or_region(
    title: str,
    text: str,
) -> str:
    combined = f"{title}\n{text[:5000]}"

    states = {
        "Alabama": r"\bAlabama\b|\bAL\b",
        "Arizona": r"\bArizona\b|\bAZ\b",
        "California": r"\bCalifornia\b|\bCA\b",
        "Colorado": r"\bColorado\b|\bCO\b",
        "Florida": r"\bFlorida\b|\bFL\b",
        "Georgia": r"\bGeorgia\b|\bGA\b",
        "Illinois": r"\bIllinois\b|\bIL\b",
        "Maryland": r"\bMaryland\b|\bMD\b",
        "Michigan": r"\bMichigan\b|\bMI\b",
        "New Jersey": r"\bNew Jersey\b|\bNJ\b",
        "New York": r"\bNew York\b|\bNY\b",
        "North Carolina": r"\bNorth Carolina\b|\bNC\b",
        "Ohio": r"\bOhio\b|\bOH\b",
        "Pennsylvania": r"\bPennsylvania\b|\bPA\b",
        "Tennessee": r"\bTennessee\b|\bTN\b",
        "Texas": r"\bTexas\b|\bTX\b",
        "Virginia": r"\bVirginia\b|\bVA\b",
        "Washington": r"\bWashington\b|\bWA\b",
    }

    for state, pattern in states.items():
        if re.search(pattern, combined, re.IGNORECASE):
            return state

    return "Unknown"


def infer_line_of_business(
    title: str,
    text: str,
) -> str:
    combined = f"{title}\n{text[:5000]}".lower()

    if "medicare advantage" in combined:
        return "Medicare Advantage"

    if "medicaid" in combined:
        return "Medicaid"

    if "commercial" in combined:
        return "Commercial"

    if "exchange" in combined:
        return "Exchange"

    if "marketplace" in combined:
        return "Marketplace"

    if "medicare part d" in combined:
        return "Medicare Part D"

    if "medicare" in combined:
        return "Medicare"

    return "Unknown"



def extract_metadata(
    text: str,
    file_type: str,
    last_modified_header: str | None = None,
) -> DocumentMetadata:
    title = extract_document_title(text)

    return DocumentMetadata(
        document_title=title,
        document_type=classify_document(
            title=title,
            text=text,
        ),
        file_type=file_type,
        policy_number="",
        effective_date=extract_effective_date(text),
        last_updated_date=extract_last_updated_date(
            text=text,
            last_modified_header=last_modified_header,
        ),
        state_or_region=infer_state_or_region(
            title,
            text,
        ),
        line_of_business=infer_line_of_business(
            title,
            text,
        ),
    )