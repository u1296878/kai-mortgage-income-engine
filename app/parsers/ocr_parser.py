from pathlib import Path
from types import SimpleNamespace

from app.exceptions import ExtractionFailed

# Test hooks for monkeypatching without importing OCR dependencies on startup.
convert_from_path = None
pytesseract = SimpleNamespace(
    Output=SimpleNamespace(DICT="dict"),
    image_to_data=None,
)

DPI = 150
POINTS_PER_PIXEL = 72 / DPI


def parse_with_ocr(file_path: Path) -> list[dict]:
    try:
        ocr_convert_from_path, ocr_pytesseract = _load_ocr_dependencies()
        page_count = _count_pdf_pages(file_path)
        blocks = []
        for page_number in range(1, page_count + 1):
            pages = _convert_single_page(ocr_convert_from_path, file_path, page_number)
            if not pages:
                continue
            image = pages[0]
            data = ocr_pytesseract.image_to_data(
                image,
                output_type=ocr_pytesseract.Output.DICT,
            )
            blocks.extend(_ocr_data_to_blocks(data, page_number))
        return blocks
    except Exception as error:
        raise ExtractionFailed(f"Could not OCR document: {file_path}") from error


def _ocr_data_to_blocks(data: dict, page_number: int) -> list[dict]:
    blocks = []
    for index, text in enumerate(data.get("text", [])):
        clean_text = text.strip()
        if not clean_text:
            continue
        left = _to_pdf_points(data["left"][index])
        top = _to_pdf_points(data["top"][index])
        width = _to_pdf_points(data["width"][index])
        height = _to_pdf_points(data["height"][index])
        blocks.append(
            {
                "text": clean_text,
                "page": page_number,
                "x1": left,
                "y1": top,
                "x2": round(left + width, 2),
                "y2": round(top + height, 2),
            }
        )
    return blocks


def _to_pdf_points(value) -> float:
    return round(float(value) * POINTS_PER_PIXEL, 2)


def _load_ocr_dependencies():
    if callable(convert_from_path) and getattr(pytesseract, "image_to_data", None):
        return convert_from_path, pytesseract
    from pdf2image import convert_from_path as imported_convert_from_path
    import pytesseract as imported_pytesseract

    return imported_convert_from_path, imported_pytesseract


def _count_pdf_pages(file_path: Path) -> int:
    if not file_path.exists():
        return 1
    import pdfplumber

    with pdfplumber.open(file_path) as pdf:
        return len(pdf.pages)


def _convert_single_page(ocr_convert_from_path, file_path: Path, page_number: int):
    try:
        return ocr_convert_from_path(
            file_path,
            dpi=DPI,
            first_page=page_number,
            last_page=page_number,
        )
    except TypeError:
        # Keep test monkeypatch compatibility for simple one-argument stubs.
        return ocr_convert_from_path(file_path)
