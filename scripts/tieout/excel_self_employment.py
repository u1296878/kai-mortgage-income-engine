"""Self-employment adapter for the Excel tie-out generator."""

SCHED_C = {
    "net_profit": 19,
    "nonrecurring_income": 20,
    "depletion": 21,
    "depreciation": 22,
    "meals_entertainment_exclusion": 23,
    "business_use_of_home": 24,
    "business_miles": 25,
    "amortization_casualty": 28,
}
K1_PTR = {"ordinary_income": 117, "net_rental_income": 118, "guaranteed_payments": 119}
F1065 = {
    "passthrough_other_partnerships": 129,
    "nonrecurring_income": 130,
    "depreciation": 131,
    "depreciation_8825": 132,
    "depletion": 133,
    "amortization_casualty_nonrecurring_loss": 134,
    "mortgages_notes_payable_lt_1yr": 135,
    "travel_entertainment_exclusion": 136,
}
F1120 = {
    "taxable_income": 373,
    "total_tax": 374,
    "nonrecurring_gains_losses": 375,
    "nonrecurring_income": 376,
    "depreciation": 377,
    "depletion": 378,
    "amortization_casualty_nonrecurring_loss": 379,
    "nol_and_special_deductions": 380,
    "mortgages_notes_payable_lt_1yr": 381,
    "travel_entertainment_exclusion": 382,
}


def apply_self_employment(wb, engine_input):
    kind, payload = engine_input["kind"], engine_input["payload"]
    sam, summary = wb["SAM"], wb["Summary"]
    sam["I5"] = 2025
    sam["L5"] = 2024
    if kind == "schedule_c":
        return _apply_schedule_c(sam, summary, payload)
    if kind == "partnership":
        return _apply_partnership(sam, summary, payload)
    if kind == "corporation":
        return _apply_corporation(sam, summary, payload)
    raise NotImplementedError(f"Self-employment kind not mapped: {kind}")


def _apply_schedule_c(sam, summary, payload):
    years = payload["years"]
    if any(year.get("w2_self_employment_income") for year in years):
        raise NotImplementedError("Single-member-LLC Schedule C block not mapped yet")
    for col, year in zip(("I", "L"), years):
        sam[f"{col}5"] = year.get("tax_year", 2025 if col == "I" else 2024)
        _fill(sam, col, year, SCHED_C)
    if len(years) == 1:
        _exclude_year2(summary, [8])
    return "Summary", "K8"


def _apply_partnership(sam, summary, payload):
    years = zip(("I", "L"), payload["k1_years"], payload["w2_years"], payload["form_1065_years"])
    for col, k1, w2, form in years:
        _fill(sam, col, k1, K1_PTR)
        sam[f"{col}125"] = w2.get("wages", 0)
        _fill(sam, col, form, F1065)
        sam[f"{col}140"] = form.get("ownership_pct", 0)
    if len(payload["w2_years"]) == 1:
        _exclude_year2(summary, [16, 17, 18])
    return "Summary", "K19"


def _apply_corporation(sam, summary, payload):
    years = zip(("I", "L"), payload["w2_years"], payload["form_1120_years"])
    for col, w2, form in years:
        sam[f"{col}369"] = w2.get("wages", 0)
        _fill(sam, col, form, F1120)
        sam[f"{col}386"] = form.get("ownership_pct", 0)
        sam[f"{col}387"] = form.get("dividends_paid_to_borrower", 0)
    if len(payload["w2_years"]) == 1:
        _exclude_year2(summary, [49, 50])
    return "Summary", "K51"


def _fill(ws, col, year, rowmap):
    for field, row in rowmap.items():
        ws[f"{col}{row}"] = year.get(field, 0)


def _exclude_year2(summary, rows):
    for row in rows:
        summary[f"Q{row}"] = True
