from pathlib import Path
from types import SimpleNamespace

import pytest
import pytesseract

from app.exceptions import ExtractionFailed
from app.parsers import ocr_parser, pdf_parser


class FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_parse_pdf_returns_text_blocks(monkeypatch):
    page = SimpleNamespace(extract_words=lambda: [{"text": "85000.00", "x0": 1, "top": 2, "x1": 3, "bottom": 4}])
    monkeypatch.setattr(pdf_parser.pdfplumber, "open", lambda file_path: FakePdf([page]))

    blocks = pdf_parser.parse_pdf(Path("fake.pdf"))

    assert blocks == [{"text": "85000.00", "page": 1, "x1": 1.0, "y1": 2.0, "x2": 3.0, "y2": 4.0}]


def test_parse_pdf_returns_empty_list_for_no_text(monkeypatch):
    page = SimpleNamespace(extract_words=lambda: [])
    monkeypatch.setattr(pdf_parser.pdfplumber, "open", lambda file_path: FakePdf([page]))

    blocks = pdf_parser.parse_pdf(Path("empty.pdf"))

    assert blocks == []


def test_parse_pdf_raises_on_corrupt_file(monkeypatch):
    def raise_parse_error(file_path):
        raise RuntimeError("corrupt")

    monkeypatch.setattr(pdf_parser.pdfplumber, "open", raise_parse_error)

    with pytest.raises(ExtractionFailed):
        pdf_parser.parse_pdf(Path("corrupt.pdf"))


def test_parse_with_ocr_returns_text_blocks(monkeypatch):
    data = {"text": ["", "85000.00"], "left": [0, 10], "top": [0, 20], "width": [0, 30], "height": [0, 40]}
    monkeypatch.setattr(ocr_parser, "convert_from_path", lambda file_path: ["image"])
    monkeypatch.setattr(ocr_parser.pytesseract, "image_to_data", lambda image, output_type: data)

    blocks = ocr_parser.parse_with_ocr(Path("scan.pdf"))

    assert blocks == [{"text": "85000.00", "page": 1, "x1": 4.8, "y1": 9.6, "x2": 19.2, "y2": 28.8}]


def test_parse_with_ocr_raises_when_tesseract_missing(monkeypatch):
    def raise_missing_tesseract(image, output_type):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(ocr_parser, "convert_from_path", lambda file_path: ["image"])
    monkeypatch.setattr(ocr_parser.pytesseract, "image_to_data", raise_missing_tesseract)

    with pytest.raises(ExtractionFailed):
        ocr_parser.parse_with_ocr(Path("scan.pdf"))
