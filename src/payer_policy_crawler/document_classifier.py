def classify_document(title: str, text: str) -> str:
    title_lower = title.lower()
    combined = f"{title}\n{text[:10000]}".lower()

    # Strong signals from title first.
    if "formulary" in title_lower:
        return "formulary"

    if "drug list" in title_lower or "drug-list" in title_lower:
        return "drug_list"

    if (
        "prior authorization" in title_lower
        or "prior auth" in title_lower
        or "preauthorization" in title_lower
    ):
        return "pa_list"

    if "medical policy" in title_lower:
        return "medical_policy"

    if "coverage guideline" in title_lower:
        return "coverage_guideline"

    if "provider manual" in title_lower:
        return "provider_manual"

    if "bulletin" in title_lower:
        return "bulletin"

    # Fall back to document body.
    if "prior authorization" in combined:
        return "pa_list"

    if "medical policy" in combined:
        return "medical_policy"

    if "coverage guideline" in combined:
        return "coverage_guideline"

    if "provider manual" in combined:
        return "provider_manual"

    if "formulary" in combined:
        return "formulary"

    if "drug list" in combined:
        return "drug_list"

    if "bulletin" in combined:
        return "bulletin"

    return "other"