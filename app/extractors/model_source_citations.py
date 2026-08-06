import re
from dataclasses import dataclass

from app.extractors.extracted_field_factory import parse_float
from app.extractors.model_source_locator import locate_source
from app.extractors.source_lines import SourceLine, resolve_source_lines
from app.extractors.tax_return_text import normalize

LOW_CONFIDENCE = 0.2


@dataclass(frozen=True)
class CitationResult:
    source: dict | None
    confidence: float
    review_flags: list[dict]


def resolve_model_source(
    field_name: str,
    entry,
    lines: list[SourceLine],
    blocks: list[dict],
    value: float | None,
    source_text: str | None,
    confidence: float,
) -> CitationResult:
    ids = _source_line_ids(entry)
    needs_source = value is not None or source_text is not None
    if not needs_source:
        return CitationResult(None, confidence, [])
    if ids is None:
        return _fallback(field_name, blocks, value, source_text, confidence, needs_source)
    if not ids:
        return _missing(field_name, blocks, value, source_text, confidence, needs_source)

    resolution = resolve_source_lines(lines, ids)
    flags = _resolution_flags(field_name, resolution.invalid_ids, resolution.cross_page_ids)
    source = _source_from_resolution(resolution)
    if source is not None:
        flags.extend(_support_flags(field_name, resolution.raw_text or "", value, source_text))
    if flags:
        confidence = min(confidence, LOW_CONFIDENCE)
    return CitationResult(source, confidence, flags)


def _source_line_ids(entry) -> list[str] | None:
    if not isinstance(entry, dict) or "source_line_ids" not in entry:
        return None
    ids = entry.get("source_line_ids")
    if not isinstance(ids, list) or any(not isinstance(source_id, str) for source_id in ids):
        return None
    return ids


def _missing(
    field_name: str,
    blocks: list[dict],
    value: float | None,
    source_text: str | None,
    confidence: float,
    needs_source: bool,
) -> CitationResult:
    if not needs_source:
        return CitationResult(None, confidence, [])
    source = locate_source(blocks, value, source_text)
    flags = [_issue(field_name, "source_line_ids missing for model value")]
    if source is not None:
        flags.append(_issue(field_name, "source located by fallback; verify"))
    return CitationResult(source, min(confidence, LOW_CONFIDENCE), flags)


def _fallback(
    field_name: str,
    blocks: list[dict],
    value: float | None,
    source_text: str | None,
    confidence: float,
    needs_source: bool,
) -> CitationResult:
    if not needs_source:
        return CitationResult(None, confidence, [])
    source = locate_source(blocks, value, source_text)
    flags = [_issue(field_name, "source_line_ids missing for model value")]
    if source is not None:
        flags.append(_issue(field_name, "source located by fallback; verify"))
    return CitationResult(source, min(confidence, LOW_CONFIDENCE), flags)


def _resolution_flags(field_name: str, invalid_ids: list[str], cross_page_ids: list[str]) -> list[dict]:
    flags = []
    if invalid_ids:
        flags.append(_issue(field_name, f"source_line_ids invalid: {', '.join(invalid_ids)}"))
    if cross_page_ids:
        flags.append(_issue(field_name, f"source_line_ids cross pages: {', '.join(cross_page_ids)}"))
    return flags


def _source_from_resolution(resolution) -> dict | None:
    if resolution.page is None or resolution.bounding_box is None:
        return None
    return {"page": resolution.page, "raw_text": resolution.raw_text or "", **resolution.bounding_box}


def _support_flags(field_name: str, raw_text: str, value: float | None, source_text: str | None) -> list[dict]:
    flags = []
    if source_text and normalize(source_text) not in normalize(raw_text):
        flags.append(_issue(field_name, "source_text not found in cited source"))
    if value is not None and not _has_numeric_value(raw_text, value):
        flags.append(_issue(field_name, "value not found in cited source"))
    return flags


def _has_numeric_value(raw_text: str, value: float) -> bool:
    for candidate in re.findall(r"\(?-?\$?\d[\d,]*(?:\.\d+)?\)?", raw_text):
        parsed = parse_float(candidate)
        if parsed is not None and abs(parsed - value) < 0.01:
            return True
    return False


def _issue(field_name: str, message: str) -> dict:
    return {"fields": [field_name], "message": message, "severity": "low"}
