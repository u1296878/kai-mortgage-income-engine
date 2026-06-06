import pytest

from app.exceptions import InvalidNonTaxableInput
from app.income.nontaxable import compute_nontaxable_income, compute_social_security
from app.schemas.nontaxable_inputs import (
    NonTaxableMethod,
    NonTaxableSource,
    SocialSecurityMethod,
    SocialSecuritySource,
)


def test_gross_100_divides_annual_by_twelve():
    source = NonTaxableSource(method=NonTaxableMethod.gross_100, annual_gross=24000)

    result = compute_nontaxable_income(source)

    assert result.monthly == 2000.00


def test_total_adjusted_grosses_up_only_the_nontaxable_slice():
    source = NonTaxableSource(
        method=NonTaxableMethod.total_adjusted,
        annual_gross=24000,
        annual_taxable=18000,
    )

    result = compute_nontaxable_income(source)

    # taxable 18000/12 = 1500 (not grossed up);
    # eligible (24000-18000)*1.25/12 = 625 (grossed up 25%); total 2125
    assert result.monthly == 2125.00
    assert result.taxable_monthly == 1500.00
    assert result.eligible_monthly == 625.00


def test_current_monthly_applies_return_taxable_ratio_to_current_amount():
    source = NonTaxableSource(
        method=NonTaxableMethod.current_monthly,
        current_monthly=2200,
        annual_gross=24000,
        annual_taxable=18000,
    )

    result = compute_nontaxable_income(source)

    # ratio 18000/24000 = 0.75; taxable_mo 2200*0.75 = 1650; eligible_mo 550;
    # monthly 1650 + 550*1.25 = 2337.50
    assert result.monthly == 2337.50
    assert result.taxable_monthly == 1650.00
    assert result.eligible_monthly == 687.50


def test_current_monthly_with_custom_gross_up_rate():
    source = NonTaxableSource(
        method=NonTaxableMethod.current_monthly,
        current_monthly=2000,
        annual_gross=24000,
        annual_taxable=18000,
        gross_up_rate=0.15,
    )

    result = compute_nontaxable_income(source)

    # taxable_mo 1500; eligible_mo 500; monthly 1500 + 500*1.15 = 2075.00
    assert result.monthly == 2075.00


def test_current_monthly_zero_gross_guards_divide_by_zero():
    source = NonTaxableSource(
        method=NonTaxableMethod.current_monthly,
        current_monthly=1000,
        annual_gross=0,
        annual_taxable=0,
    )

    result = compute_nontaxable_income(source)

    # ratio guards to 0, so the full current amount is treated non-taxable:
    # 0 + 1000*1.25 = 1250.00 (no crash)
    assert result.monthly == 1250.00


def test_social_security_gross_100_divides_by_twelve():
    ss = SocialSecuritySource(method=SocialSecurityMethod.gross_100, annual_gross=24000)

    result = compute_social_security(ss)

    assert result.monthly == 2000.00


def test_social_security_adjusted_grosses_up_fifteen_percent_at_twenty_five():
    ss = SocialSecuritySource(method=SocialSecurityMethod.adjusted, annual_gross=24000)

    result = compute_social_security(ss)

    # (24000 + 24000*0.15*0.25)/12 = (24000 + 900)/12 = 2075.00
    assert result.monthly == 2075.00
    assert result.eligible_monthly == 75.00


def test_gross_100_without_annual_gross_raises_invalid_input():
    source = NonTaxableSource(method=NonTaxableMethod.gross_100)

    with pytest.raises(InvalidNonTaxableInput):
        compute_nontaxable_income(source)


def test_total_adjusted_without_taxable_raises_invalid_input():
    source = NonTaxableSource(
        method=NonTaxableMethod.total_adjusted, annual_gross=24000
    )

    with pytest.raises(InvalidNonTaxableInput):
        compute_nontaxable_income(source)


def test_current_monthly_without_current_amount_raises_invalid_input():
    source = NonTaxableSource(
        method=NonTaxableMethod.current_monthly,
        annual_gross=24000,
        annual_taxable=18000,
    )

    with pytest.raises(InvalidNonTaxableInput):
        compute_nontaxable_income(source)


def test_social_security_without_gross_raises_invalid_input():
    ss = SocialSecuritySource(method=SocialSecurityMethod.adjusted)

    with pytest.raises(InvalidNonTaxableInput):
        compute_social_security(ss)
