"""Pydantic inputs for self-employment personal schedules (spec section 5.2)."""

from pydantic import BaseModel, Field


class SelfEmploymentYear(BaseModel):
    months: float = 12.0
    included: bool = True


class ScheduleBYear(SelfEmploymentYear):
    recurring_interest: float | None = None
    recurring_dividends: float | None = None


class ScheduleCYear(SelfEmploymentYear):
    tax_year: int | None = None
    net_profit: float | None = None
    nonrecurring_income: float | None = None
    depletion: float | None = None
    depreciation: float | None = None
    meals_entertainment_exclusion: float | None = None
    business_use_of_home: float | None = None
    business_miles: float | None = None
    amortization_casualty: float | None = None
    w2_self_employment_income: float | None = None


class ScheduleDYear(SelfEmploymentYear):
    recurring_capital_gains: float | None = None


class ScheduleERoyaltyYear(SelfEmploymentYear):
    royalty_income: float | None = None
    total_expenses: float | None = None
    depreciation_depletion: float | None = None


class ScheduleFYear(SelfEmploymentYear):
    net_profit: float | None = None
    nontax_coop_ccc_payments: float | None = None
    nonrecurring_loss: float | None = None
    nonrecurring_income: float | None = None
    depreciation: float | None = None
    amortization_casualty_depletion: float | None = None
    business_use_of_home: float | None = None


class ScheduleBInput(BaseModel):
    years: list[ScheduleBYear] = Field(default_factory=list, max_length=2)


class ScheduleCInput(BaseModel):
    years: list[ScheduleCYear] = Field(default_factory=list, max_length=2)


class ScheduleDInput(BaseModel):
    years: list[ScheduleDYear] = Field(default_factory=list, max_length=2)


class ScheduleERoyaltyInput(BaseModel):
    years: list[ScheduleERoyaltyYear] = Field(default_factory=list, max_length=2)


class ScheduleFInput(BaseModel):
    years: list[ScheduleFYear] = Field(default_factory=list, max_length=2)
