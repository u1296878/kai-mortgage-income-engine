from pathlib import Path

from app.parsers import pdf_image_renderer


class FakeImage:
    def __init__(self, label: str) -> None:
        self.label = label

    def save(self, output, format: str) -> None:
        output.write(f"{format}:{self.label}".encode("ascii"))


def test_render_pdf_pages_returns_png_bytes(monkeypatch):
    calls = []

    def fake_convert(file_path, dpi, first_page, last_page):
        calls.append((file_path, dpi, first_page, last_page))
        return [FakeImage(f"page-{first_page}")]

    monkeypatch.setattr(pdf_image_renderer, "convert_from_path", fake_convert)

    images = pdf_image_renderer.render_pdf_pages(Path("tax.pdf"), [2, 4])

    assert images == [b"PNG:page-2", b"PNG:page-4"]
    assert calls[0][2:] == (2, 2)
    assert calls[1][2:] == (4, 4)
