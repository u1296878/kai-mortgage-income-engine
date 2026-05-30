from app.models.income_stream import IncomeStream
from app.models.income_stream_type import IncomeStreamType
from app.models.result import Result

CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def suggest_result_match(
    result: Result,
    streams: list[IncomeStream],
) -> dict:
    meta = _result_metadata(result)
    typed_streams = [stream for stream in streams if stream.stream_type == meta["stream_type"].value]
    if typed_streams:
        best = max(
            (_candidate(meta, stream) for stream in typed_streams),
            key=lambda item: (CONFIDENCE_RANK[item["confidence"]], item["stream"].created_at, item["stream"].id),
        )
        stream = best["stream"]
        return {
            "result_id": result.id,
            "stream_id": stream.id,
            "stream_type": meta["stream_type"],
            "suggested_stream_name": stream.name,
            "confidence": best["confidence"],
            "reason": best["reason"],
            "can_auto_apply": best["confidence"] == "high",
            "action": "assign_existing_stream",
        }
    confidence, reason = _new_stream_confidence(meta)
    return {
        "result_id": result.id,
        "stream_id": None,
        "stream_type": meta["stream_type"],
        "suggested_stream_name": _suggested_stream_name(meta),
        "confidence": confidence,
        "reason": reason,
        "can_auto_apply": confidence == "high",
        "action": "create_stream",
    }


def _candidate(meta: dict, stream: IncomeStream) -> dict:
    key = _stream_key(stream)
    if meta["stream_type"] == IncomeStreamType.employment:
        if meta["employer"] and key == meta["employer"]:
            return {"stream": stream, "confidence": "high", "reason": "Shared employer name"}
        if meta["tax_year"] is not None:
            return {"stream": stream, "confidence": "medium", "reason": "Same employment stream type and tax year"}
    if meta["stream_type"] == IncomeStreamType.rental:
        if meta["property_address"] and key == meta["property_address"]:
            return {"stream": stream, "confidence": "high", "reason": "Shared property address"}
        if meta["tax_year"] is not None:
            return {"stream": stream, "confidence": "medium", "reason": "Same rental stream type and tax year"}
    if meta["stream_type"] == IncomeStreamType.self_employment and meta["has_schedule_c"]:
        return {"stream": stream, "confidence": "high", "reason": "Schedule C result matches self-employment stream"}
    if meta["stream_type"] == IncomeStreamType.bank_statement and meta["statement_period"]:
        if key == meta["statement_period"]:
            return {"stream": stream, "confidence": "high", "reason": "Matching bank statement period"}
        return {"stream": stream, "confidence": "medium", "reason": "Same bank statement stream type in case"}
    return {"stream": stream, "confidence": "low", "reason": "Same stream type in case"}


def _new_stream_confidence(meta: dict) -> tuple[str, str]:
    if meta["stream_type"] == IncomeStreamType.employment and meta["employer"]:
        return "high", "Employer name supports a new employment stream"
    if meta["stream_type"] == IncomeStreamType.rental and meta["property_address"]:
        return "high", "Property address supports a new rental stream"
    if meta["stream_type"] == IncomeStreamType.self_employment and meta["has_schedule_c"]:
        return "high", "Schedule C result supports a self-employment stream"
    if meta["stream_type"] == IncomeStreamType.bank_statement and meta["statement_period"]:
        return "high", "Statement period supports a bank statement stream"
    return "medium", "No strong identifier found; stream type is a compatible match"


def _suggested_stream_name(meta: dict) -> str:
    if meta["stream_type"] == IncomeStreamType.employment and meta["employer"]:
        return f"Employment: {meta['employer_raw']}"
    if meta["stream_type"] == IncomeStreamType.rental and meta["property_address"]:
        return f"Rental: {meta['property_address_raw']}"
    if meta["stream_type"] == IncomeStreamType.self_employment and meta["tax_year"] is not None:
        return f"Self-employment: {meta['tax_year']}"
    if meta["stream_type"] == IncomeStreamType.bank_statement and meta["statement_period_raw"]:
        return f"Bank statement: {meta['statement_period_raw']}"
    return f"{meta['stream_type'].value.replace('_', ' ').title()} stream"


def _result_metadata(result: Result) -> dict:
    by_name = {field["field"]: field for field in result.extracted_fields}
    employer_raw = (by_name.get("w2_employer_name") or {}).get("raw_text")
    property_raw = (by_name.get("property_address") or {}).get("raw_text")
    start = (by_name.get("statement_start_date") or {}).get("raw_text")
    end = (by_name.get("statement_end_date") or {}).get("raw_text")
    tax_year_value = (by_name.get("tax_year") or {}).get("value")
    period_raw = f"{start} to {end}" if start and end else None
    return {
        "stream_type": _infer_stream_type(result, by_name),
        "employer": _normalize_key(employer_raw),
        "employer_raw": employer_raw,
        "property_address": _normalize_key(property_raw),
        "property_address_raw": property_raw,
        "statement_period": _normalize_key(period_raw),
        "statement_period_raw": period_raw,
        "tax_year": int(tax_year_value) if tax_year_value is not None else None,
        "has_schedule_c": "schedule_c_net" in by_name,
    }


def _infer_stream_type(result: Result, by_name: dict) -> IncomeStreamType:
    if result.doc_type in {"w2", "pay_stub"}:
        return IncomeStreamType.employment
    if result.doc_type == "bank_statement":
        return IncomeStreamType.bank_statement
    if result.doc_type == "tax_return":
        return IncomeStreamType.self_employment if "schedule_c_net" in by_name else IncomeStreamType.employment
    if result.doc_type == "other" and {"rental_net_income", "property_address"} & set(by_name):
        return IncomeStreamType.rental
    return IncomeStreamType.other


def _stream_key(stream: IncomeStream) -> str | None:
    if stream.notes and "auto_key=" in stream.notes:
        return _normalize_key(stream.notes.split("auto_key=", 1)[1].split(";", 1)[0])
    if ":" in stream.name:
        return _normalize_key(stream.name.split(":", 1)[1])
    return None


def _normalize_key(text: str | None) -> str | None:
    if not text:
        return None
    return " ".join(text.lower().split())
