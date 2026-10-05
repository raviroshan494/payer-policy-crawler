import pymupdf


def extract_pdf_text(content: bytes) -> str:
    document = pymupdf.open(
        stream=content,
        filetype="pdf",
    )

    try:
        pages = []

        for page in document:
            pages.append(page.get_text())

        return "\n".join(pages)

    finally:
        document.close()