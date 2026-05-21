from pathlib import Path

from pdf2image import convert_from_path
import pytesseract

from app.exceptions import ExtractionFailed


def parse_with_ocr(file_path: Path) -> list[dict]:
    try:
        pages = convert_from_path(file_path)
        blocks = []
        for page_number, image in enumerate(pages, start=1):
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
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
        left = float(data["left"][index])
        top = float(data["top"][index])
        width = float(data["width"][index])
        height = float(data["height"][index])
        blocks.append(
            {
                "text": clean_text,
                "page": page_number,
                "x1": left,
                "y1": top,
                "x2": left + width,
                "y2": top + height,
            }
        )
    return blocks
