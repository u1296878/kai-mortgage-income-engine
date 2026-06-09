import os
from concurrent.futures import ProcessPoolExecutor, TimeoutError
from pathlib import Path
from types import SimpleNamespace

from app.config import settings
from app.exceptions import ExtractionFailed, PageOcrTimeout

# Test hooks for monkeypatching without importing OCR dependencies on startup.
convert_from_path = None
pytesseract = SimpleNamespace(
    Output=SimpleNamespace(DICT="dict"),
    image_to_data=None,
)


def parse_with_ocr(file_path: Path) -> list[dict]:
    try:
        page_count = _count_pdf_pages(file_path)
        return _parse_pages(file_path, page_count)
    except PageOcrTimeout:
        raise
    except Exception as error:
        raise ExtractionFailed(f"Could not OCR document: {file_path}") from error


def _parse_pages(file_path: Path, page_count: int) -> list[dict]:
    dpi = settings.ocr_dpi
    timeout = settings.ocr_page_timeout_seconds
    thread_limit = settings.ocr_thread_limit
    max_workers = _worker_count(page_count)
    if page_count <= 1 or _using_test_hooks():
        return _parse_pages_serial(file_path, page_count, dpi, thread_limit)
    return _parse_pages_with_pool(file_path, page_count, dpi, max_workers, timeout, thread_limit)


def _parse_pages_serial(file_path: Path, page_count: int, dpi: int, thread_limit: int) -> list[dict]:
    blocks = []
    for page_number in range(1, page_count + 1):
        blocks.extend(_ocr_single_page(file_path, page_number, dpi, thread_limit))
    return blocks


def _parse_pages_with_pool(
    file_path: Path,
    page_count: int,
    dpi: int,
    max_workers: int,
    timeout: int,
    thread_limit: int,
) -> list[dict]:
    executor = ProcessPoolExecutor(max_workers=max_workers)
    try:
        futures = {
            page: executor.submit(_ocr_page_worker, str(file_path), page, dpi, thread_limit)
            for page in range(1, page_count + 1)
        }
        blocks = []
        for page, future in futures.items():
            try:
                blocks.extend(future.result(timeout=timeout))
            except TimeoutError as error:
                raise PageOcrTimeout(f"OCR timed out on page {page}") from error
        return blocks
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _ocr_page_worker(file_path: str, page_number: int, dpi: int, thread_limit: int) -> list[dict]:
    return _ocr_single_page(Path(file_path), page_number, dpi, thread_limit)


def _ocr_single_page(file_path: Path, page_number: int, dpi: int, thread_limit: int) -> list[dict]:
    os.environ["OMP_THREAD_LIMIT"] = str(thread_limit)
    ocr_convert_from_path, ocr_pytesseract = _load_ocr_dependencies()
    pages = _convert_single_page(ocr_convert_from_path, file_path, page_number, dpi)
    if not pages:
        return []
    data = ocr_pytesseract.image_to_data(
        pages[0],
        output_type=ocr_pytesseract.Output.DICT,
    )
    return _ocr_data_to_blocks(data, page_number, dpi)


def _ocr_data_to_blocks(data: dict, page_number: int, dpi: int) -> list[dict]:
    blocks = []
    for index, text in enumerate(data.get("text", [])):
        clean_text = text.strip()
        if not clean_text:
            continue
        left = _to_pdf_points(data["left"][index], dpi)
        top = _to_pdf_points(data["top"][index], dpi)
        width = _to_pdf_points(data["width"][index], dpi)
        height = _to_pdf_points(data["height"][index], dpi)
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


def _to_pdf_points(value, dpi: int) -> float:
    return round(float(value) * (72 / dpi), 2)


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


def _convert_single_page(ocr_convert_from_path, file_path: Path, page_number: int, dpi: int):
    try:
        return ocr_convert_from_path(
            file_path,
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
        )
    except TypeError:
        # Keep test monkeypatch compatibility for simple one-argument stubs.
        return ocr_convert_from_path(file_path)


def _using_test_hooks() -> bool:
    return callable(convert_from_path) and getattr(pytesseract, "image_to_data", None) is not None


def _worker_count(page_count: int) -> int:
    cpu_count = os.cpu_count() or 1
    configured = max(1, settings.ocr_max_workers)
    return min(page_count, cpu_count, configured)
