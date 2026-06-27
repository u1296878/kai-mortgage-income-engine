from pathlib import Path
from types import SimpleNamespace

from app.parsers import pdf_parser


class FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_page_dimensions_returns_pdf_point_sizes(monkeypatch):
    pages = [
        SimpleNamespace(width=612, height=792),
        SimpleNamespace(width=595.2, height=841.8),
    ]
    monkeypatch.setattr(pdf_parser.pdfplumber, "open", lambda file_path: FakePdf(pages))

    sizes = pdf_parser.page_dimensions(Path("fake.pdf"), [1, 2])

    assert sizes == {1: (612.0, 792.0), 2: (595.2, 841.8)}
