from uuid import uuid4

from app.extractors.schedule_c_extractor import extract_schedule_c_fields
from app.income.self_employment import compute_schedule_c
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from tests.unit.tax_return_test_helpers import block


def fields_for(blocks, page=2):
    fields = extract_schedule_c_fields(blocks, uuid4(), {page})
    return {field.field: field for field in fields}


def value(fields, name):
    field = fields.get(f"schedule_c_business_1_{name}")
    return field.value if field else 0.0


def values(fields):
    names = ("net_profit", "nonrecurring_income", "depreciation", "business_use_of_home", "amortization_casualty")
    return {name: value(fields, name) for name in names}


def schedule_c_subtotal(fields, tax_year):
    year = ScheduleCYear(
        tax_year=tax_year,
        net_profit=value(fields, "net_profit"),
        nonrecurring_income=value(fields, "nonrecurring_income"),
        depletion=value(fields, "depletion"),
        depreciation=value(fields, "depreciation"),
        meals_entertainment_exclusion=value(fields, "meals_entertainment_exclusion"),
        business_use_of_home=value(fields, "business_use_of_home"),
        business_miles=value(fields, "business_miles"),
        amortization_casualty=value(fields, "amortization_casualty"),
    )
    return compute_schedule_c(ScheduleCInput(years=[year])).years[0].annual_subtotal


def ocr_style(blocks):
    return [_scale_jitter(block) for block in blocks]


def schedule_c_page(
    net="94,380.00",
    depreciation="3,633.00",
    home="4,628.00",
    other_expenses="7,557.00",
    taxes="10,959.00",
    ordinary_part_v=True,
    part_v_amortization=False,
):
    blocks = _header() + _income_trap() + _wrapped_depreciation(depreciation, taxes)
    blocks += _home_and_net(home, net, other_expenses)
    if ordinary_part_v or part_v_amortization:
        blocks += _part_v_header()
    if ordinary_part_v:
        blocks += [block("Supplies", 80, 500, 132, 512, page=2), block(other_expenses, 620, 500, 680, 512, page=2)]
    if part_v_amortization:
        blocks += [block("Amortization", 80, 520, 170, 532, page=2), block("1,200.00", 620, 520, 680, 532, page=2)]
    return blocks


def _header():
    return [
        block("Schedule", 50, 50, 110, 62, page=2), block("C", 114, 50, 124, 62, page=2),
        block("Profit", 128, 50, 166, 62, page=2), block("or", 170, 50, 184, 62, page=2),
        block("Loss", 188, 50, 220, 62, page=2), block("From", 224, 50, 256, 62, page=2),
        block("Business", 260, 50, 320, 62, page=2),
    ]


def _income_trap():
    return [
        block("1", 50, 120, 58, 132, page=2), block("Gross", 80, 120, 126, 132, page=2),
        block("receipts", 130, 120, 184, 132, page=2), block("145,721.00", 620, 120, 690, 132, page=2),
        block("6", 50, 150, 58, 162, page=2), block("Other", 80, 150, 118, 162, page=2),
        block("income", 122, 150, 168, 162, page=2),
    ]


def _wrapped_depreciation(depreciation, taxes):
    return [
        block("13", 50, 180, 66, 192, page=2), block("Deduction", 80, 180, 148, 192, page=2),
        block(depreciation, 620, 180, 680, 192, page=2), block("Depreciation", 80, 188, 158, 200, page=2),
        block("23", 50, 191, 66, 203, page=2), block("Taxes", 80, 191, 122, 203, page=2),
        block("and", 126, 191, 148, 203, page=2), block("licenses", 152, 191, 210, 203, page=2),
        block(taxes, 620, 191, 680, 203, page=2),
    ]


def _home_and_net(home, net, other_expenses):
    return [
        block("27a", 50, 260, 74, 272, page=2), block("Other", 80, 260, 118, 272, page=2),
        block("expenses", 122, 260, 180, 272, page=2), block(other_expenses, 620, 260, 680, 272, page=2),
        block("30", 50, 300, 66, 312, page=2), block("Business", 80, 300, 138, 312, page=2),
        block("use", 142, 300, 166, 312, page=2), block("of", 170, 300, 184, 312, page=2),
        block("home", 188, 300, 224, 312, page=2), block("Form", 260, 300, 298, 312, page=2),
        block("8829", 302, 300, 342, 312, page=2), block(home, 620, 300, 680, 312, page=2),
        block("31", 50, 340, 66, 352, page=2), block("Net", 80, 340, 104, 352, page=2),
        block("profit", 108, 340, 146, 352, page=2), block(net, 620, 340, 680, 352, page=2),
    ]


def _part_v_header():
    return [
        block("Part", 50, 460, 82, 472, page=2), block("V", 86, 460, 96, 472, page=2),
        block("Other", 110, 460, 148, 472, page=2), block("Expenses", 152, 460, 214, 472, page=2),
    ]


def _scale_jitter(item):
    copied = item.copy()
    copied.update({key: value * 2 for key, value in item.items() if key in {"x1", "x2", "y1", "y2"}})
    if item["x1"] >= 600:
        copied["y1"] += 4
        copied["y2"] += 4
    return copied
