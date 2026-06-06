"""Annual subtotals for self-employment entities (spec sections 5.3-5.5)."""

from app.exceptions import InvalidSelfEmploymentInput
from app.schemas.self_employment_entity_inputs import (
    Form1065Year,
    Form1120SYear,
    Form1120Year,
    PartnershipK1Year,
    SCorpK1Year,
    W2WagesYear,
)


def k1_partnership_subtotal(year: PartnershipK1Year) -> float:
    return round(
        _required(year.ordinary_income, "ordinary_income")
        + _required(year.net_rental_income, "net_rental_income")
        + _required(year.guaranteed_payments, "guaranteed_payments"),
        2,
    )


def k1_s_corp_subtotal(year: SCorpK1Year) -> float:
    return round(
        _required(year.ordinary_income, "ordinary_income")
        + _required(year.net_rental_income, "net_rental_income"),
        2,
    )


def w2_wages_subtotal(year: W2WagesYear) -> float:
    return round(_required(year.wages, "wages"), 2)


def form_1065_subtotal(year: Form1065Year) -> float:
    return round(
        _required(year.passthrough_other_partnerships, "passthrough_other_partnerships")
        - _required(year.nonrecurring_income, "nonrecurring_income")
        + _required(year.depreciation, "depreciation")
        + _required(year.depreciation_8825, "depreciation_8825")
        + _required(year.depletion, "depletion")
        + _required(
            year.amortization_casualty_nonrecurring_loss,
            "amortization_casualty_nonrecurring_loss",
        )
        - _required(
            year.mortgages_notes_payable_lt_1yr,
            "mortgages_notes_payable_lt_1yr",
        )
        - _required(
            year.travel_entertainment_exclusion,
            "travel_entertainment_exclusion",
        ),
        2,
    )


def form_1065_share(year: Form1065Year) -> float:
    return round(form_1065_subtotal(year) * _ownership_pct(year.ownership_pct), 2)


def form_1120s_subtotal(year: Form1120SYear) -> float:
    return round(
        -_required(year.nonrecurring_income, "nonrecurring_income")
        + _required(year.depreciation, "depreciation")
        + _required(year.depreciation_8825, "depreciation_8825")
        + _required(year.depletion, "depletion")
        + _required(
            year.amortization_casualty_nonrecurring_loss,
            "amortization_casualty_nonrecurring_loss",
        )
        - _required(
            year.mortgages_notes_payable_lt_1yr,
            "mortgages_notes_payable_lt_1yr",
        )
        - _required(
            year.travel_entertainment_exclusion,
            "travel_entertainment_exclusion",
        ),
        2,
    )


def form_1120s_share(year: Form1120SYear) -> float:
    return round(form_1120s_subtotal(year) * _ownership_pct(year.ownership_pct), 2)


def form_1120_subtotal(year: Form1120Year) -> float:
    return round(
        _required(year.taxable_income, "taxable_income")
        - _required(year.total_tax, "total_tax")
        + _required(year.nonrecurring_gains_losses, "nonrecurring_gains_losses")
        - _required(year.nonrecurring_income, "nonrecurring_income")
        + _required(year.depreciation, "depreciation")
        + _required(year.depletion, "depletion")
        + _required(
            year.amortization_casualty_nonrecurring_loss,
            "amortization_casualty_nonrecurring_loss",
        )
        + _required(year.nol_and_special_deductions, "nol_and_special_deductions")
        - _required(
            year.mortgages_notes_payable_lt_1yr,
            "mortgages_notes_payable_lt_1yr",
        )
        - _required(
            year.travel_entertainment_exclusion,
            "travel_entertainment_exclusion",
        ),
        2,
    )


def form_1120_share(year: Form1120Year) -> float:
    ownership_share = form_1120_subtotal(year) * _ownership_pct(year.ownership_pct)
    return round(
        ownership_share
        - _required(year.dividends_paid_to_borrower, "dividends_paid_to_borrower"),
        2,
    )


def _ownership_pct(value: float | None) -> float:
    return _required(value, "ownership_pct")


def _required(value: float | None, name: str) -> float:
    if value is None:
        raise InvalidSelfEmploymentInput(f"{name} is required")
    return value
