from io import BytesIO
from pathlib import Path

from PIL import Image

from app.parsers import pdf_image_renderer


def test_render_pdf_pages_returns_png_bytes(monkeypatch):
    calls = []

    def fake_convert(file_path, dpi, first_page, last_page):
        calls.append((file_path, dpi, first_page, last_page))
        return [_image(80, 40)]

    monkeypatch.setattr(pdf_image_renderer.settings, "vision_dpi", 175)
    monkeypatch.setattr(pdf_image_renderer, "convert_from_path", fake_convert)

    images = pdf_image_renderer.render_pdf_pages(Path("tax.pdf"), [2, 4])

    assert [_png_size(image) for image in images] == [(80, 40), (80, 40)]
    assert calls[0][1] == 175
    assert calls[0][2:] == (2, 2)
    assert calls[1][2:] == (4, 4)


def test_render_pdf_pages_downscales_large_page(monkeypatch):
    monkeypatch.setattr(pdf_image_renderer.settings, "vision_image_max_px", 100)
    monkeypatch.setattr(
        pdf_image_renderer,
        "convert_from_path",
        lambda file_path, dpi, first_page, last_page: [_image(400, 200)],
    )

    rendered = pdf_image_renderer.render_pdf_pages(Path("large.pdf"), [1])

    assert _png_size(rendered[0]) == (100, 50)


def test_render_pdf_pages_leaves_small_page_unchanged(monkeypatch):
    monkeypatch.setattr(pdf_image_renderer.settings, "vision_image_max_px", 100)
    monkeypatch.setattr(
        pdf_image_renderer,
        "convert_from_path",
        lambda file_path, dpi, first_page, last_page: [_image(60, 40)],
    )

    rendered = pdf_image_renderer.render_pdf_pages(Path("small.pdf"), [1])

    assert _png_size(rendered[0]) == (60, 40)


def _image(width: int, height: int) -> Image.Image:
    return Image.new("RGB", (width, height), "white")


def _png_size(payload: bytes) -> tuple[int, int]:
    with Image.open(BytesIO(payload)) as image:
        return image.size
