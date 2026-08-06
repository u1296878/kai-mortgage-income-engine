from datetime import datetime

from app.models.result import Result


def stream_income_snapshot(results: list[Result]) -> tuple[float | None, str | None]:
    selected = select_stream_result(results)
    if selected is None:
        return None, None
    return selected.annual_income, selected.confidence


def select_stream_result(results: list[Result]) -> Result | None:
    candidates = [result for result in results if result.annual_income is not None]
    if not candidates:
        return None
    return max(candidates, key=_stream_sort_key)


def _stream_sort_key(result: Result) -> tuple[int, datetime, str]:
    return (
        _confidence_rank(result.confidence),
        result.created_at,
        result.id,
    )


def _confidence_rank(confidence: str | None) -> int:
    ranks = {"high": 3, "medium": 2, "low": 1}
    return ranks.get(confidence or "", 0)
