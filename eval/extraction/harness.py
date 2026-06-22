from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.schemas.extraction import ExtractedField
from app.services import extraction_service
from eval.extraction.reporting import markdown_report
from eval.extraction.subtotals import compute_subtotal

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LABELS = Path(__file__).with_name("labels.json")


@dataclass
class EvalConfig:
    provider: str
    runs: int = 1
    labels_path: Path = DEFAULT_LABELS
    model: str | None = None
    num_ctx: int = 2048
    num_gpu: int | None = 0
    results_dir: Path | None = Path(__file__).with_name("results")
    tolerance: float = 1.0


def run_eval(config: EvalConfig) -> tuple[str, dict]:
    original = _settings_snapshot()
    try:
        _configure_provider(config)
        result = _evaluate(config, _load_labels(config.labels_path))
        report = markdown_report(result)
        if config.results_dir:
            _write_result(config.results_dir, result)
        return report, result
    finally:
        _restore_settings(original)


def _load_labels(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    return payload["documents"] if isinstance(payload, dict) else payload


def _evaluate(config: EvalConfig, fixtures: list[dict]) -> dict:
    docs = [_score_fixture(fixture, config) for fixture in fixtures]
    tied = sum(1 for doc in docs if _doc_subtotal(doc).get("status") == "PASS")
    tieout_total = sum(1 for doc in docs if doc.get("subtotal") and doc["status"] != "SKIPPED")
    varied = sum(field["varied"] for doc in docs for field in doc.get("fields", []))
    return {
        "provider": config.provider,
        "model": _model_name(config),
        "runs": config.runs,
        "created_at": datetime.now(UTC).isoformat(),
        "documents": docs,
        "summary": {"tieouts": tied, "tieout_total": tieout_total, "varied_fields": varied},
    }


def _doc_subtotal(doc: dict) -> dict:
    return doc.get("subtotal") or {}


def _score_fixture(fixture: dict, config: EvalConfig) -> dict:
    path = _resolve_path(fixture["path"])
    if not path.exists():
        return {"id": fixture["id"], "path": fixture["path"], "status": "SKIPPED", "reason": "missing document"}
    try:
        runs = [_extract(path, fixture["doc_type"]) for _ in range(config.runs)]
    except Exception as error:
        return {"id": fixture["id"], "path": fixture["path"], "status": "FAILED", "reason": f"{type(error).__name__}: {error}"}
    by_run = [{field.field: field for field in fields} for fields in runs]
    field_rows = [_field_score(name, expected, by_run) for name, expected in fixture["expected_fields"].items()]
    subtotal = _subtotal_score(fixture, by_run, config.tolerance)
    return {
        "id": fixture["id"],
        "path": fixture["path"],
        "doc_type": fixture["doc_type"],
        "status": "DONE",
        "fields": field_rows,
        "subtotal": subtotal,
    }


def _field_score(name: str, expected, by_run: list[dict[str, ExtractedField]]) -> dict:
    got = [_actual_value(fields.get(name), expected) for fields in by_run]
    statuses = [_status(expected, value, 0.01) for value in got]
    return {
        "field": name,
        "expected": expected,
        "got": got,
        "accuracy": f"{statuses.count('PASS')}/{len(statuses)}",
        "status": "PASS" if all(status == "PASS" for status in statuses) else "FAIL",
        "varied": len({_stable(value) for value in got}) > 1,
    }


def _subtotal_score(fixture: dict, by_run: list[dict[str, ExtractedField]], tolerance: float) -> dict | None:
    subtotal = fixture.get("subtotal")
    if not subtotal:
        return None
    got = [compute_subtotal(subtotal["type"], fields) for fields in by_run]
    statuses = [_status(subtotal["expected"], value, tolerance) for value in got]
    return {
        "type": subtotal["type"],
        "expected": subtotal["expected"],
        "got": got,
        "accuracy": f"{statuses.count('PASS')}/{len(statuses)}",
        "status": "PASS" if all(status == "PASS" for status in statuses) else "FAIL",
        "varied": len({_stable(value) for value in got}) > 1,
    }


def _extract(path: Path, doc_type: str) -> list[ExtractedField]:
    return extraction_service.extract_fields(uuid4(), path, doc_type)


def _configure_provider(config: EvalConfig) -> None:
    settings.extraction_backend = "model"
    settings.extraction_provider = config.provider
    if config.provider == "anthropic" and config.model:
        settings.anthropic_model = config.model
    if config.provider == "ollama":
        settings.ollama_model = config.model or settings.ollama_model
        settings.ollama_num_ctx = config.num_ctx
        settings.ollama_num_gpu = config.num_gpu


def _settings_snapshot() -> dict:
    return {name: getattr(settings, name) for name in ("extraction_backend", "extraction_provider", "anthropic_model", "ollama_model", "ollama_num_ctx", "ollama_num_gpu")}


def _restore_settings(values: dict) -> None:
    for name, value in values.items():
        setattr(settings, name, value)


def _write_result(results_dir: Path, result: dict) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{result['provider']}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.json"
    (results_dir / filename).write_text(json.dumps(result, indent=2))


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _model_name(config: EvalConfig) -> str:
    return config.model or (settings.anthropic_model if config.provider == "anthropic" else settings.ollama_model)


def _actual_value(field: ExtractedField | None, expected):
    if field is None:
        return None
    return field.raw_text if isinstance(expected, str) else field.value


def _status(expected, got, tolerance: float) -> str:
    if expected is None:
        return "PASS" if got is None else "FAIL"
    if got is None:
        return "FAIL"
    if isinstance(expected, str):
        return "PASS" if str(got).strip().casefold() == expected.casefold() else "FAIL"
    return "PASS" if abs(float(got) - float(expected)) <= tolerance else "FAIL"


def _stable(value) -> str:
    return json.dumps(value, sort_keys=True)
