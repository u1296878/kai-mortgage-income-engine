from dataclasses import dataclass


@dataclass(frozen=True)
class ResultIncome:
    annual_income: float | None
    confidence: str
    notes: str | None


def compute_result_income(values: dict[str, float | None], doc_type: str) -> ResultIncome:
    if doc_type == "w2":
        return _reference("Income derived from employment draft; W-2 boxes shown for reference only.")
    if doc_type == "pay_stub":
        return _reference("Income derived from employment draft; pay-stub fields shown for reference only.")
    if doc_type == "tax_return":
        return _reference("Income derived from per-schedule drafts; AGI shown for reference only.")
    if doc_type == "bank_statement":
        return ResultIncome(_annualize(values.get("average_monthly_deposit")), "low", None)
    if values.get("rental_net_income") is not None:
        return ResultIncome(values["rental_net_income"], "low", None)
    return ResultIncome(values.get("reported_income"), "low", None)


def _reference(notes: str) -> ResultIncome:
    return ResultIncome(None, "medium", notes)


def _annualize(monthly: float | None) -> float | None:
    return monthly * 12 if monthly is not None else None
