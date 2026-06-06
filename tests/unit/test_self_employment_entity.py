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


def components_by_name(result):
    return {component.component: component for component in result.components}


def test_partnership_combines_k1_w2_and_owned_1065_share():
    source = PartnershipInput(
        k1_years=[
            PartnershipK1Year(
                ordinary_income=50000,
                net_rental_income=5000,
                guaranteed_payments=10000,
            )
        ],
        w2_years=[W2WagesYear(wages=24000)],
        form_1065_years=[
            Form1065Year(
                passthrough_other_partnerships=100000,
                nonrecurring_income=5000,
                depreciation=12000,
                depreciation_8825=3000,
                depletion=1000,
                amortization_casualty_nonrecurring_loss=2000,
                mortgages_notes_payable_lt_1yr=10000,
                travel_entertainment_exclusion=1500,
                ownership_pct=0.4,
            )
        ],
    )

    result = compute_partnership(source)

    components = components_by_name(result)
    assert components["partnership_k1"].qualifying_monthly == 5416.67
    assert components["w2_wages"].qualifying_monthly == 2000.00
    assert components["form_1065_share"].years[0].annual_subtotal == 40600.00
    assert result.qualifying_monthly == 10800.00


def test_s_corporation_combines_k1_w2_and_owned_1120s_share():
    source = SCorpInput(
        k1_years=[
            SCorpK1Year(ordinary_income=36000, net_rental_income=6000)
        ],
        w2_years=[W2WagesYear(wages=30000)],
        form_1120s_years=[
            Form1120SYear(
                nonrecurring_income=4000,
                depreciation=15000,
                depreciation_8825=1000,
                depletion=500,
                amortization_casualty_nonrecurring_loss=2500,
                mortgages_notes_payable_lt_1yr=3000,
                travel_entertainment_exclusion=700,
                ownership_pct=0.5,
            )
        ],
    )

    result = compute_s_corporation(source)

    components = components_by_name(result)
    assert components["s_corp_k1"].qualifying_monthly == 3500.00
    assert components["w2_wages"].qualifying_monthly == 2500.00
    assert components["form_1120s_share"].years[0].annual_subtotal == 5650.00
    assert result.qualifying_monthly == 6470.83


def test_corporation_combines_w2_and_owned_1120_share_minus_dividends():
    source = CorporationInput(
        w2_years=[W2WagesYear(wages=48000)],
        form_1120_years=[
            Form1120Year(
                taxable_income=200000,
                total_tax=40000,
                nonrecurring_gains_losses=3000,
                nonrecurring_income=10000,
                depreciation=20000,
                depletion=2000,
                amortization_casualty_nonrecurring_loss=1000,
                nol_and_special_deductions=5000,
                mortgages_notes_payable_lt_1yr=20000,
                travel_entertainment_exclusion=1000,
                ownership_pct=0.25,
                dividends_paid_to_borrower=10000,
            )
        ],
    )

    result = compute_corporation(source)

    components = components_by_name(result)
    assert components["w2_wages"].qualifying_monthly == 4000.00
    assert components["form_1120_share"].years[0].annual_subtotal == 30000.00
    assert result.qualifying_monthly == 6500.00


def test_ownership_pct_applies_only_to_business_return_component():
    source = PartnershipInput(
        k1_years=[
            PartnershipK1Year(
                ordinary_income=100000,
                net_rental_income=10000,
                guaranteed_payments=10000,
            )
        ],
        w2_years=[W2WagesYear(wages=60000)],
        form_1065_years=[
            Form1065Year(
                passthrough_other_partnerships=120000,
                nonrecurring_income=0,
                depreciation=0,
                depreciation_8825=0,
                depletion=0,
                amortization_casualty_nonrecurring_loss=0,
                mortgages_notes_payable_lt_1yr=0,
                travel_entertainment_exclusion=0,
                ownership_pct=0.1,
            )
        ],
    )

    result = compute_partnership(source)

    components = components_by_name(result)
    assert components["partnership_k1"].qualifying_monthly == 10000.00
    assert components["w2_wages"].qualifying_monthly == 5000.00
    assert components["form_1065_share"].qualifying_monthly == 1000.00
    assert result.qualifying_monthly == 16000.00
