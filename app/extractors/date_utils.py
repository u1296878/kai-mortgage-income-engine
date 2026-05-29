from datetime import datetime


DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y")


def parse_date(text: str) -> datetime | None:
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return None


def iso_date(text: str) -> str | None:
    parsed = parse_date(text)
    return parsed.strftime("%Y-%m-%d") if parsed else None


def inclusive_month_count(start_text: str, end_text: str) -> int | None:
    start = parse_date(start_text)
    end = parse_date(end_text)
    if not start or not end or end < start:
        return None
    return (end.year - start.year) * 12 + end.month - start.month + 1
