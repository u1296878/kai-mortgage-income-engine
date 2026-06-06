"""Pydantic inputs for self-employment business entities (spec sections 5.3-5.5)."""

from pydantic import BaseModel, Field

from app.schemas.self_employment_inputs import SelfEmploymentYear


class PartnershipK1Year(SelfEmploymentYear):
    ordinary_income: float | None = None
    net_rental_income: float | None = None
    guaranteed_payments: float | None = None


class SCorpK1Year(SelfEmploymentYear):
    ordinary_income: float | None = None
    net_rental_income: float | None = None


class W2WagesYear(SelfEmploymentYear):
    wages: float | None = None


class Form1065Year(SelfEmploymentYear):
    passthrough_other_partnerships: float | None = None
    nonrecurring_income: float | None = None
    depreciation: float | None = None
    depreciation_8825: float | None = None
    depletion: float | None = None
    amortization_casualty_nonrecurring_loss: float | None = None
    mortgages_notes_payable_lt_1yr: float | None = None
    travel_entertainment_exclusion: float | None = None
    ownership_pct: float | None = None


class Form1120SYear(SelfEmploymentYear):
    nonrecurring_income: float | None = None
    depreciation: float | None = None
    depreciation_8825: float | None = None
    depletion: float | None = None
    amortization_casualty_nonrecurring_loss: float | None = None
    mortgages_notes_payable_lt_1yr: float | None = None
    travel_entertainment_exclusion: float | None = None
    ownership_pct: float | None = None


class Form1120Year(SelfEmploymentYear):
    taxable_income: float | None = None
    total_tax: float | None = None
    nonrecurring_gains_losses: float | None = None
    nonrecurring_income: float | None = None
    depreciation: float | None = None
    depletion: float | None = None
    amortization_casualty_nonrecurring_loss: float | None = None
    nol_and_special_deductions: float | None = None
    mortgages_notes_payable_lt_1yr: float | None = None
    travel_entertainment_exclusion: float | None = None
    ownership_pct: float | None = None
    dividends_paid_to_borrower: float | None = None


class PartnershipInput(BaseModel):
    k1_years: list[PartnershipK1Year] = Field(default_factory=list, max_length=2)
    w2_years: list[W2WagesYear] = Field(default_factory=list, max_length=2)
    form_1065_years: list[Form1065Year] = Field(default_factory=list, max_length=2)


class SCorpInput(BaseModel):
    k1_years: list[SCorpK1Year] = Field(default_factory=list, max_length=2)
    w2_years: list[W2WagesYear] = Field(default_factory=list, max_length=2)
    form_1120s_years: list[Form1120SYear] = Field(default_factory=list, max_length=2)


class CorporationInput(BaseModel):
    w2_years: list[W2WagesYear] = Field(default_factory=list, max_length=2)
    form_1120_years: list[Form1120Year] = Field(default_factory=list, max_length=2)
