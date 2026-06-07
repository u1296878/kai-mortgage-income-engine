"""Workbook-specific cell adapters for the Excel tie-out generator."""

from __future__ import annotations

import datetime

from excel_self_employment import apply_self_employment

PAY_FREQ = {
    "hourly": "Hourly (H)",
    "weekly": "Weekly (52)",
    "biweekly": "Bi-Weekly (26)",
    "semimonthly": "Semi-Monthly (24)",
    "monthly": "Monthly (12)",
    "quarterly": "Quarterly (4)",
    "semiannually": "Semi-Annually (2)",
    "annually": "Annually (1)",
    "varies": "Varies",
}
EMP_ROWS = {
    "base_pay": (14, 15, 16),
    "overtime": (23, 24, 25),
    "bonus": (32, 33, 34),
    "commission": (41, 42, 43),
    "other": (52, 53, 54),
}
EMP_AY = {"overtime": 22, "bonus": 31, "commission": 40, "other": 51}
RENT_SCHE = {
    "months_in_service": 13,
    "rents_received": 14,
    "total_expenses": 15,
    "insurance": 16,
    "mortgage_interest": 17,
    "taxes": 18,
    "depreciation_depletion": 19,
    "hoa_addback": 20,
    "casualty_one_time": 21,
}
def apply_employment(wb, engine_input):
    ws = wb["Primary Employment"]
    base = engine_input["base_pay"]
    _periods(ws, "base_pay", base.get("periods", []))
    if base.get("rate_line_included"):
        ws["R12"] = True
        ws["G12"] = base["rate"]
        ws["H12"] = PAY_FREQ[base["pay_frequency"]]
        if base.get("hours_weekly") is not None:
            ws["I12"] = base["hours_weekly"]
    else:
        ws["R12"] = False
    for bucket in ("overtime", "bonus", "commission", "other"):
        spec = engine_input.get(bucket)
        if spec is None:
            for row in EMP_ROWS[bucket]:
                ws[f"R{row}"] = False
            continue
        _periods(ws, bucket, spec.get("periods", []))
        ay = EMP_AY[bucket]
        annualize = bool(spec.get("annualize")) and not bool(spec.get("use_ytd"))
        ws[f"R{ay}"] = annualize
        ws[f"S{ay}"] = not annualize
    return "Primary Employment", "K59"


def apply_rental(wb, engine_input):
    cls, method = engine_input["property_class"], engine_input["method"]
    if method == "lease":
        if cls != "primary_2_4_unit":
            raise NotImplementedError("Investment lease block not mapped yet")
        ws = wb["Principal Residence (2-4 Unit)"]
        ws["J64"] = engine_input["gross_monthly_rent"]
        ws["H65"] = engine_input.get("vacancy_factor", 0.25)
        return "Principal Residence (2-4 Unit)", "J66"
    sheet = "Investment Property" if cls == "investment" else "Principal Residence (2-4 Unit)"
    ws = wb[sheet]
    ws["I4"] = 2025
    ws["L4"] = 2024
    for col, year in zip(("I", "L"), engine_input.get("schedule_e_years", [])):
        _fill(ws, col, year, RENT_SCHE)
        if cls == "investment":
            ws[f"{col}24"] = engine_input.get("monthly_pitia", 0)
    return (sheet, "J26") if cls == "investment" else (sheet, "J24")


ADAPTERS = {
    "employment": {
        "workbook": "Income-Worksheet-Macro-Free.xlsx",
        "apply": apply_employment,
    },
    "rental": {"workbook": "Rental-Worksheet-Macro-Free.xlsx", "apply": apply_rental},
    "self_employment": {
        "workbook": "All-In-One-Worksheet-Macro-Free.xlsx",
        "apply": apply_self_employment,
    },
}


def _periods(ws, name, periods):
    for idx, row in enumerate(EMP_ROWS[name]):
        if idx < len(periods) and periods[idx] is not None:
            period = periods[idx]
            ws[f"F{row}"] = datetime.datetime.strptime(period["date_from"], "%Y-%m-%d")
            ws[f"G{row}"] = datetime.datetime.strptime(period["date_through"], "%Y-%m-%d")
            ws[f"H{row}"] = period["total_earnings"]
            ws[f"R{row}"] = bool(period.get("included", True))
        else:
            ws[f"R{row}"] = False


def _fill(ws, col, year, rowmap):
    for field, row in rowmap.items():
        ws[f"{col}{row}"] = year.get(field, 0)

