from uuid import uuid4

from app.extractors.schedule_c_extractor import extract_schedule_c_fields
from app.income.self_employment import compute_schedule_c
from app.schemas.self_employment_inputs import ScheduleCInput, ScheduleCYear
from tests.unit.tax_return_test_helpers import block


def test_wrapped_line_13_uses_line_number_row_value():
    fields = _fields(_schedule_c_page(depreciation="3,633.00", wrapped_depreciation=True))

    assert fields["schedule_c_business_1_depreciation"].value == 3633.0
    assert fields["schedule_c_business_1_depreciation"].bounding_box.x1 == 620.0


def test_other_expenses_total_is_not_added_back_without_part_v_amortization():
    fields = _fields(_schedule_c_page(other_expenses="7,557.00", ordinary_part_v=True))

    assert _value(fields, "amortization_casualty") == 0.0


def test_part_v_amortization_and_casualty_details_are_added_back():
    fields = _fields(_schedule_c_page(part_v_amortization=True))

    assert _value(fields, "amortization_casualty") == 1500.0


def test_digital_and_ocr_style_blocks_extract_same_values():
    digital = _schedule_c_page(net="85,247.00", depreciation="659.00", home="3,173.00")
    ocr = [_scaled_jittered(block) for block in digital]

    assert _values(_fields(digital)) == _values(_fields(ocr))


def test_2023_schedule_c_ties_out_without_27a_over_add():
    fields = _fields(
        _schedule_c_page(
            net="94,380.00",
            depreciation="3,633.00",
            home="4,628.00",
            other_expenses="7,557.00",
            ordinary_part_v=True,
        )
    )

    assert _schedule_c_subtotal(fields, tax_year=2023) == 102641.0


def test_2024_schedule_c_ties_out_without_27a_over_add():
    fields = _fields(
        _schedule_c_page(
            net="85,247.00",
            depreciation="659.00",
            home="3,173.00",
            other_expenses="5,046.00",
            ordinary_part_v=True,
        )
    )

    assert _schedule_c_subtotal(fields, tax_year=2024) == 89079.0


def _fields(blocks):
    fields = extract_schedule_c_fields(blocks, uuid4(), {2})
    return {field.field: field for field in fields}


def _value(fields, name):
    field = fields.get(f"schedule_c_business_1_{name}")
    return field.value if field else 0.0


def _values(fields):
    names = ("net_profit", "depreciation", "business_use_of_home", "amortization_casualty")
    return {name: _value(fields, name) for name in names}


def _schedule_c_subtotal(fields, tax_year):
    year = ScheduleCYear(
        tax_year=tax_year,
        net_profit=_value(fields, "net_profit"),
        nonrecurring_income=_value(fields, "nonrecurring_income"),
        depletion=_value(fields, "depletion"),
        depreciation=_value(fields, "depreciation"),
        meals_entertainment_exclusion=_value(fields, "meals_entertainment_exclusion"),
        business_use_of_home=_value(fields, "business_use_of_home"),
        business_miles=_value(fields, "business_miles"),
        amortization_casualty=_value(fields, "amortization_casualty"),
    )
    return compute_schedule_c(ScheduleCInput(years=[year])).years[0].annual_subtotal


def _schedule_c_page(
    net="50,000.00",
    depreciation="8,000.00",
    home="3,000.00",
    other_expenses="700.00",
    wrapped_depreciation=False,
    ordinary_part_v=False,
    part_v_amortization=False,
):
    blocks = _base_schedule_c(net, home, other_expenses)
    blocks.extend(_wrapped_depreciation(depreciation) if wrapped_depreciation else _simple_depreciation(depreciation))
    if ordinary_part_v or part_v_amortization:
        blocks.extend(_part_v_header())
    if ordinary_part_v:
        blocks.append(block("Supplies", 80, 500, 132, 512, page=2))
        blocks.append(block(other_expenses, 620, 500, 680, 512, page=2))
    if part_v_amortization:
        blocks.extend(
            [
                block("Amortization", 80, 500, 170, 512, page=2),
                block("1,200.00", 620, 500, 680, 512, page=2),
                block("Casualty", 80, 520, 138, 532, page=2),
                block("300.00", 620, 520, 668, 532, page=2),
            ]
        )
    return blocks


def _base_schedule_c(net, home, other_expenses):
    return [
        block("Schedule", 50, 50, 110, 62, page=2),
        block("C", 114, 50, 124, 62, page=2),
        block("Profit", 128, 50, 166, 62, page=2),
        block("or", 170, 50, 184, 62, page=2),
        block("Loss", 188, 50, 220, 62, page=2),
        block("From", 224, 50, 256, 62, page=2),
        block("Business", 260, 50, 320, 62, page=2),
        block("27a", 50, 260, 74, 272, page=2),
        block("Other", 80, 260, 118, 272, page=2),
        block("expenses", 122, 260, 180, 272, page=2),
        block(other_expenses, 620, 260, 680, 272, page=2),
        block("30", 50, 300, 66, 312, page=2),
        block("Business", 80, 300, 138, 312, page=2),
        block("use", 142, 300, 166, 312, page=2),
        block("of", 170, 300, 184, 312, page=2),
        block("home", 188, 300, 224, 312, page=2),
        block(home, 620, 300, 680, 312, page=2),
        block("31", 50, 340, 66, 352, page=2),
        block("Net", 80, 340, 104, 352, page=2),
        block("profit", 108, 340, 146, 352, page=2),
        block(net, 620, 340, 680, 352, page=2),
    ]


def _simple_depreciation(value):
    return [block("13", 50, 180, 66, 192, page=2), block("Depreciation", 80, 180, 158, 192, page=2), block(value, 620, 180, 680, 192, page=2)]


def _wrapped_depreciation(value):
    return [
        block("13", 50, 180, 66, 192, page=2),
        block("Deduction", 80, 180, 148, 192, page=2),
        block(value, 620, 180, 680, 192, page=2),
        block("Depreciation", 80, 188, 158, 200, page=2),
        block("9,999.00", 620, 191, 680, 203, page=2),
        block("14", 50, 206, 66, 218, page=2),
        block("Other", 80, 206, 118, 218, page=2),
    ]


def _part_v_header():
    return [block("Part", 50, 460, 82, 472, page=2), block("V", 86, 460, 96, 472, page=2), block("Other", 110, 460, 148, 472, page=2), block("Expenses", 152, 460, 214, 472, page=2)]


def _scaled_jittered(item):
    copied = item.copy()
    copied.update({key: value * 2 for key, value in item.items() if key in {"x1", "x2", "y1", "y2"}})
    if item["x1"] >= 600:
        copied["y1"] += 4
        copied["y2"] += 4
    return copied
