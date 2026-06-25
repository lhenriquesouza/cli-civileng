"""Extract clean text from PDF documents using pymupdf (fitz)."""
import fitz  # pymupdf


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF file, preserving page order."""
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            texts.append(text.strip())
    doc.close()
    return "\n\n".join(texts)


def extract_text_by_page(pdf_path: str) -> list[str]:
    """Extract text page by page."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text("text").strip() for page in doc]
    doc.close()
    return pages
