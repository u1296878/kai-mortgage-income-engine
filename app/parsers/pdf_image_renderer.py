from io import BytesIO
from pathlib import Path

from app.config import settings
from app.exceptions import ExtractionFailed

convert_from_path = None


def render_pdf_pages(file_path: Path, pages: list[int]) -> list[bytes]:
    if not pages:
        return []
    try:
        converter = _load_converter()
        return [_render_page(converter, file_path, page) for page in pages]
    except ExtractionFailed:
        raise
    except Exception as error:
        raise ExtractionFailed(f"Could not render document images: {file_path}") from error


def _render_page(converter, file_path: Path, page_number: int) -> bytes:
    images = _convert_page(converter, file_path, page_number)
    if not images:
        raise ExtractionFailed(f"Could not render page {page_number}")
    output = BytesIO()
    images[0].save(output, format="PNG")
    return output.getvalue()


def _convert_page(converter, file_path: Path, page_number: int):
    try:
        return converter(
            file_path,
            dpi=settings.ocr_dpi,
            first_page=page_number,
            last_page=page_number,
        )
    except TypeError:
        return converter(file_path)


def _load_converter():
    if callable(convert_from_path):
        return convert_from_path
    from pdf2image import convert_from_path as imported_convert_from_path

    return imported_convert_from_path
