"""Pure self-employment entity engine (spec sections 5.3-5.6)."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.income.self_employment_common import (
    SelfEmploymentYearLike,
    SelfEmploymentYearResult,
    build_year_results,
    qualifying_monthly,
)
from app.income.self_employment_entity_subtotals import (
    form_1065_share,
    form_1120_share,
    form_1120s_share,
    k1_partnership_subtotal,
    k1_s_corp_subtotal,
    w2_wages_subtotal,
)
from app.schemas.self_employment_entity_inputs import (
    CorporationInput,
    PartnershipInput,
    SCorpInput,
)


@dataclass
class SelfEmploymentComponentResult:
    component: str
    qualifying_monthly: float
    years: list[SelfEmploymentYearResult]


@dataclass
class SelfEmploymentEntityResult:
    qualifying_monthly: float
    entity_type: str
    components: list[SelfEmploymentComponentResult]


@dataclass
class _ComponentMonthly:
    result: SelfEmploymentComponentResult
    exact_monthly: float


def compute_partnership(source: PartnershipInput) -> SelfEmploymentEntityResult:
    components = [
        _component("partnership_k1", source.k1_years, k1_partnership_subtotal),
        _component("w2_wages", source.w2_years, w2_wages_subtotal),
        _component("form_1065_share", source.form_1065_years, form_1065_share),
    ]
    return _entity("partnership", components)


def compute_s_corporation(source: SCorpInput) -> SelfEmploymentEntityResult:
    components = [
        _component("s_corp_k1", source.k1_years, k1_s_corp_subtotal),
        _component("w2_wages", source.w2_years, w2_wages_subtotal),
        _component("form_1120s_share", source.form_1120s_years, form_1120s_share),
    ]
    return _entity("s_corporation", components)


def compute_corporation(source: CorporationInput) -> SelfEmploymentEntityResult:
    components = [
        _component("w2_wages", source.w2_years, w2_wages_subtotal),
        _component("form_1120_share", source.form_1120_years, form_1120_share),
    ]
    return _entity("corporation", components)


def _component(
    name: str,
    years: Sequence[SelfEmploymentYearLike],
    subtotal_fn: Callable[[SelfEmploymentYearLike], float],
) -> _ComponentMonthly:
    year_results = build_year_results(years, subtotal_fn)
    monthly = qualifying_monthly(year_results)
    result = SelfEmploymentComponentResult(
        component=name,
        qualifying_monthly=round(monthly, 2),
        years=year_results,
    )
    return _ComponentMonthly(result=result, exact_monthly=monthly)


def _entity(
    entity_type: str,
    components: list[_ComponentMonthly],
) -> SelfEmploymentEntityResult:
    return SelfEmploymentEntityResult(
        qualifying_monthly=round(
            sum(component.exact_monthly for component in components),
            2,
        ),
        entity_type=entity_type,
        components=[component.result for component in components],
    )
