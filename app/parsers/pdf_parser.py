from pathlib import Path

import pdfplumber

from app.exceptions import ExtractionFailed


def parse_pdf(file_path: Path) -> list[dict]:
    try:
        with pdfplumber.open(file_path) as pdf:
            blocks = []
            for page_number, page in enumerate(pdf.pages, start=1):
                words = page.extract_words() or []
                blocks.extend(_word_to_block(word, page_number) for word in words)
            return blocks
    except Exception as error:
        raise ExtractionFailed(f"Could not parse PDF: {file_path}") from error


def _word_to_block(word: dict, page_number: int) -> dict:
    return {
        "text": word.get("text", ""),
        "page": page_number,
        "x1": float(word.get("x0", 0.0)),
        "y1": float(word.get("top", 0.0)),
        "x2": float(word.get("x1", 0.0)),
        "y2": float(word.get("bottom", 0.0)),
    }
