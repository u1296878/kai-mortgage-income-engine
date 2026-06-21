from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.schemas.extraction import ExtractedField
from app.services import extraction_service, extraction_validation
from app.services.self_employment_income_service import run_self_employment_engine
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from app.schemas.self_employment_results import SelfEmploymentCalculationRequest

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = Path(__file__).with_name("extraction_fixtures.json")


@dataclass
class EvalConfig:
    fixtures_path: Path = DEFAULT_FIXTURES
    runs: int = 1
    model: str = "llama3.2:latest"
    num_ctx: int = 2048
    num_gpu: int | None = 0
    markdown_path: Path | None = None


def run_eval(config: EvalConfig) -> str:
    original_settings = _settings_snapshot()
    try:
        _configure_model(config)
        fixtures = json.loads(config.fixtures_path.read_text())
        lines: list[str] = []
        aggregate: dict[str, list[bool]] = defaultdict(list)
        variance: dict[str, list[str]] = defaultdict(list)
        lines.append("# Extraction accuracy report")
        lines.append("")
        for fixture in fixtures:
            lines.extend(_score_fixture(fixture, config.runs, aggregate, variance))
        lines.extend(_aggregate_lines(aggregate, variance))
        report = "\n".join(lines)
        if config.markdown_path:
            config.markdown_path.parent.mkdir(parents=True, exist_ok=True)
            config.markdown_path.write_text(report)
        return report
    finally:
        _restore_settings(original_settings)


def _configure_model(config: EvalConfig) -> None:
    settings.extraction_backend = "model"
    settings.ollama_model = config.model
    settings.ollama_num_ctx = config.num_ctx
    settings.ollama_num_gpu = config.num_gpu


def _settings_snapshot() -> dict:
    return {
        "extraction_backend": settings.extraction_backend,
        "ollama_model": settings.ollama_model,
        "ollama_num_ctx": settings.ollama_num_ctx,
        "ollama_num_gpu": settings.ollama_num_gpu,
    }


def _restore_settings(values: dict) -> None:
    for name, value in values.items():
        setattr(settings, name, value)


def _score_fixture(fixture: dict, runs: int, aggregate: dict, variance: dict) -> list[str]:
    fixture_path = Path(fixture["path"])
    path = fixture_path if fixture_path.is_absolute() else ROOT / fixture_path
    lines = [f"## {fixture['id']}", ""]
    if not path.exists():
        lines.append(f"SKIPPED: missing fixture `{fixture['path']}`")
        lines.append("")
        return lines
    try:
        run_fields = [_extract(path, fixture["doc_type"]) for _ in range(runs)]
    except Exception as error:
        return [*lines, f"FAILED: {type(error).__name__}: {error}", ""]
    fields = run_fields[0]
    by_name = {field.field: field for field in fields}
    lines.extend(_field_score_lines(fixture, by_name, aggregate))
    lines.extend(_income_lines(fixture, by_name))
    lines.extend(_validation_lines(fixture, fields))
    _record_variance(fixture, run_fields, variance)
    lines.append("")
    return lines


def _extract(path: Path, doc_type: str) -> list[ExtractedField]:
    return extraction_service.extract_fields(uuid4(), path, doc_type)


def _field_score_lines(fixture: dict, by_name: dict, aggregate: dict) -> list[str]:
    lines = ["| field | expected | got | status |", "|---|---:|---:|---|"]
    for field, expected in fixture["expected_fields"].items():
        got = _actual_value(by_name.get(field), expected)
        status = _status(expected, got)
        aggregate[field].append(status == "PASS")
        lines.append(f"| `{field}` | {_fmt(expected)} | {_fmt(got)} | {status} |")
    return lines


def _income_lines(fixture: dict, by_name: dict) -> list[str]:
    if "expected_monthly_income" not in fixture:
        return []
    got = _schedule_c_monthly(by_name)
    status = _status(fixture["expected_monthly_income"], got)
    return [
        "",
        f"Schedule C monthly income: expected {_fmt(fixture['expected_monthly_income'])}, got {_fmt(got)} ({status})",
    ]


def _validation_lines(fixture: dict, fields: list[ExtractedField]) -> list[str]:
    issues = extraction_validation.validate_extraction(fixture["doc_type"], fields)
    high = extraction_validation.has_high_issue(issues)
    expected = bool(fixture.get("expect_high_review"))
    status = "PASS" if high == expected else "MISMATCH"
    messages = "; ".join(issue["message"] for issue in issues) or "none"
    return ["", f"Validation high-review flag: expected {expected}, got {high} ({status})", f"Issues: {messages}"]


def _record_variance(fixture: dict, run_fields: list[list[ExtractedField]], variance: dict) -> None:
    if len(run_fields) < 2:
        return
    for field in fixture["expected_fields"]:
        values = [_actual_value({item.field: item for item in fields}.get(field), fixture["expected_fields"][field]) for fields in run_fields]
        if len({json.dumps(value, sort_keys=True) for value in values}) > 1:
            variance[fixture["id"]].append(f"{field}: {values}")


def _aggregate_lines(aggregate: dict, variance: dict) -> list[str]:
    lines = ["## Aggregate accuracy", "", "| field | correct |", "|---|---:|"]
    for field in sorted(aggregate):
        values = aggregate[field]
        lines.append(f"| `{field}` | {sum(values)}/{len(values)} |")
    lines.append("")
    lines.append("## Variance")
    if not variance:
        lines.append("No variance checked or no changed values.")
    for document, changes in variance.items():
        lines.append(f"- {document}: {'; '.join(changes)}")
    return lines


def _actual_value(field: ExtractedField | None, expected):
    if field is None:
        return None
    return field.raw_text if isinstance(expected, str) else field.value


def _status(expected, got) -> str:
    if expected is None:
        return "PASS" if got is None else "MISMATCH"
    if got is None:
        return "MISSING"
    if isinstance(expected, str):
        return "PASS" if str(got).strip().casefold() == expected.casefold() else "MISMATCH"
    return "PASS" if abs(float(got) - float(expected)) < 0.01 else "MISMATCH"


def _schedule_c_monthly(by_name: dict[str, ExtractedField]) -> float | None:
    net = _num(by_name, "schedule_c_net_profit")
    if net is None:
        return None
    year = ScheduleCYear(
        tax_year=int(_num(by_name, "tax_year") or 0) or None,
        net_profit=net,
        depreciation=_num(by_name, "schedule_c_depreciation") or 0,
        business_use_of_home=_num(by_name, "schedule_c_business_use_of_home") or 0,
        business_miles=_num(by_name, "schedule_c_business_miles") or 0,
    )
    request = SelfEmploymentCalculationRequest(kind="schedule_c", payload=ScheduleCInput(years=[year]).model_dump(mode="json"))
    return run_self_employment_engine(request).qualifying_monthly


def _num(by_name: dict[str, ExtractedField], field: str) -> float | None:
    item = by_name.get(field)
    return item.value if item else None


def _fmt(value) -> str:
    if value is None:
        return "null"
    return str(value)
