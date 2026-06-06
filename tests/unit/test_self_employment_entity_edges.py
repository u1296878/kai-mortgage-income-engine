import pytest

from app.exceptions import InvalidSelfEmploymentInput
from app.income.self_employment_entity import (
    compute_corporation,
    compute_partnership,
    compute_s_corporation,
)
from app.schemas.self_employment_entity_inputs import (
    CorporationInput,
    Form1065Year,
    Form1120SYear,
    Form1120Year,
    PartnershipInput,
    PartnershipK1Year,
    SCorpInput,
    SCorpK1Year,
    W2WagesYear,
)


def form_1120s_year(**overrides):
    values = {
        "nonrecurring_income": 0,
        "depreciation": 0,
        "depreciation_8825": 0,
        "depletion": 0,
        "amortization_casualty_nonrecurring_loss": 0,
        "mortgages_notes_payable_lt_1yr": 0,
        "travel_entertainment_exclusion": 0,
        "ownership_pct": 1,
    }
    values.update(overrides)
    return Form1120SYear(**values)


def test_component_or_year_toggled_off_drops_out():
    source = PartnershipInput(
        k1_years=[
            PartnershipK1Year(
                ordinary_income=24000,
                net_rental_income=0,
                guaranteed_payments=0,
                included=False,
            )
        ],
        w2_years=[W2WagesYear(wages=12000)],
        form_1065_years=[Form1065Year(included=False)],
    )

    result = compute_partnership(source)

    assert result.components[0].qualifying_monthly == 0.00
    assert result.components[1].qualifying_monthly == 1000.00
    assert result.components[2].qualifying_monthly == 0.00
    assert result.qualifying_monthly == 1000.00


def test_component_average_is_months_weighted_across_included_years():
    source = CorporationInput(
        w2_years=[
            W2WagesYear(months=12, wages=24000),
            W2WagesYear(months=6, wages=18000),
        ]
    )

    result = compute_corporation(source)

    assert result.components[0].qualifying_monthly == 2333.33
    assert result.qualifying_monthly == 2333.33


def test_entity_loss_passes_through_negative():
    source = SCorpInput(
        form_1120s_years=[
            form_1120s_year(nonrecurring_income=12000)
        ]
    )

    result = compute_s_corporation(source)

    assert result.components[2].years[0].annual_subtotal == -12000.00
    assert result.qualifying_monthly == -1000.00


def test_zero_included_months_guards_divide_by_zero():
    source = CorporationInput(
        w2_years=[W2WagesYear(months=0, wages=12000)]
    )

    result = compute_corporation(source)

    assert result.components[0].qualifying_monthly == 0.00
    assert result.qualifying_monthly == 0.00


@pytest.mark.parametrize(
    ("source", "compute"),
    [
        (
            PartnershipInput(k1_years=[PartnershipK1Year(ordinary_income=1)]),
            compute_partnership,
        ),
        (
            SCorpInput(k1_years=[SCorpK1Year(ordinary_income=1)]),
            compute_s_corporation,
        ),
        (PartnershipInput(w2_years=[W2WagesYear()]), compute_partnership),
        (
            PartnershipInput(
                form_1065_years=[
                    Form1065Year(passthrough_other_partnerships=1)
                ]
            ),
            compute_partnership,
        ),
        (
            SCorpInput(form_1120s_years=[Form1120SYear(nonrecurring_income=0)]),
            compute_s_corporation,
        ),
        (
            CorporationInput(form_1120_years=[Form1120Year(taxable_income=0)]),
            compute_corporation,
        ),
    ],
)
def test_missing_required_line_items_raise_invalid_input(source, compute):
    with pytest.raises(InvalidSelfEmploymentInput):
        compute(source)
