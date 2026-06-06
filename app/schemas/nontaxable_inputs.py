"""Pydantic input models for the non-taxable income engine (spec section 3)."""

from enum import Enum

from pydantic import BaseModel


class NonTaxableMethod(str, Enum):
    gross_100 = "gross_100"  # gross amount, 100%, no gross-up
    total_adjusted = "total_adjusted"  # gross-up the non-taxable portion of a return
    current_monthly = "current_monthly"  # current monthly prorated by taxable ratio


class SocialSecurityMethod(str, Enum):
    gross_100 = "gross_100"  # 100% gross
    adjusted = "adjusted"  # 15% of gross grossed up at 25%


class NonTaxableSource(BaseModel):
    method: NonTaxableMethod
    annual_gross: float | None = None
    annual_taxable: float | None = None
    current_monthly: float | None = None
    gross_up_rate: float = 0.25  # spec 1.3


class SocialSecuritySource(BaseModel):
    method: SocialSecurityMethod
    annual_gross: float | None = None
