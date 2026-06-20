"""Schedule C business identity helpers for extracted tax-return drafts."""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from app.schemas.extraction import ExtractedField

REVIEW_UNMATCHED_BUSINESS = "review_schedule_c_business_match"
SINGLE_BUSINESS_KEY = "schedule_c_single_business"


@dataclass(frozen=True)
class ScheduleCBusinessIdentity:
    index: int
    source_key: str
    label: str
    business_name: str | None
    normalized_name: str | None
    ein: str | None
    review_flags: list[str]


def build_identity(
    by_name: dict[str, ExtractedField],
    index: int,
    business_count: int,
) -> ScheduleCBusinessIdentity:
    business_name = _text_value(by_name, index, "business_name")
    normalized_name = normalize_business_name(business_name)
    ein = _normalize_ein(_text_value(by_name, index, "ein"))
    review_flags = []
    if ein:
        source_key = f"schedule_c_ein:{ein}"
    elif normalized_name:
        source_key = f"schedule_c_name:{normalized_name}"
    elif business_count == 1:
        source_key = SINGLE_BUSINESS_KEY
    else:
        source_key = f"schedule_c_unmatched_business_{index}"
        review_flags.append(REVIEW_UNMATCHED_BUSINESS)
    label = business_name or f"Schedule C business {index}"
    return ScheduleCBusinessIdentity(
        index=index,
        source_key=source_key,
        label=label,
        business_name=business_name,
        normalized_name=normalized_name,
        ein=ein,
        review_flags=review_flags,
    )


def normalize_business_name(value: str | None) -> str | None:
    if not value:
        return None
    clean = re.sub(r"[^\w\s]", " ", value.casefold())
    words = []
    for word in clean.split():
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]
        words.append(word)
    return " ".join(words) or None


def business_names_match(first: str | None, second: str | None) -> bool:
    first_normalized = normalize_business_name(first)
    second_normalized = normalize_business_name(second)
    if not first_normalized or not second_normalized:
        return False
    if first_normalized == second_normalized:
        return True
    ratio = SequenceMatcher(None, first_normalized, second_normalized).ratio()
    return ratio >= 0.82


def is_single_business_key(source_key: str | None) -> bool:
    return source_key in {SINGLE_BUSINESS_KEY, "business_1"}


def source_key_name(source_key: str | None) -> str | None:
    if source_key and source_key.startswith("schedule_c_name:"):
        return source_key.split(":", 1)[1]
    return None


def _text_value(
    by_name: dict[str, ExtractedField],
    index: int,
    suffix: str,
) -> str | None:
    field = by_name.get(f"schedule_c_business_{index}_{suffix}")
    if field is None and index == 1:
        field = by_name.get(f"schedule_c_{suffix}")
    if field is None:
        return None
    return field.raw_text.strip() if field.raw_text else None


def _normalize_ein(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) >= 6 else None
