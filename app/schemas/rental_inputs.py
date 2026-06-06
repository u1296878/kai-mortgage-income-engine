"""Pydantic input models for the rental calc engine (spec section 4)."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class PropertyClass(str, Enum):
    primary_2_4_unit = "primary_2_4_unit"
    investment = "investment"


class RentalMethod(str, Enum):
    schedule_e = "schedule_e"
    lease = "lease"


class ScheduleEYear(BaseModel):
    """One tax year of Schedule E line items (spec 4.1)."""

    months_in_service: float = 12.0  # capped at 12 in the engine
    rents_received: float = 0.0
    total_expenses: float = 0.0
    insurance: float = 0.0
    mortgage_interest: float = 0.0
    taxes: float = 0.0
    depreciation_depletion: float = 0.0
    hoa_addback: float = 0.0
    casualty_one_time: float = 0.0


class RentalProperty(BaseModel):
    property_class: PropertyClass
    method: RentalMethod
    schedule_e_years: list[ScheduleEYear] = []  # up to two (current + prior)
    monthly_pitia: float | None = None  # required for investment net
    gross_monthly_rent: float | None = None  # lease: lesser of lease vs market rent
    vacancy_factor: float = 0.25  # lease


class RentalCalculationCreate(RentalProperty):
    """Save request: a full RentalProperty plus optional case-binding metadata."""

    borrower_id: UUID | None = None
    label: str | None = None
