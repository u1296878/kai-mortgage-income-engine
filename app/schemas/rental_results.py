"""API response models mirroring the rental engine dataclasses (spec section 4).

The engine stays pure (returns dataclasses); these give the API a typed contract.
"""

from pydantic import BaseModel


class RentalYearResult(BaseModel):
    months: float
    annual_net: float
    monthly_gross: float


class RentalResult(BaseModel):
    qualifying_monthly: float
    property_class: str
    method: str
    years: list[RentalYearResult]
