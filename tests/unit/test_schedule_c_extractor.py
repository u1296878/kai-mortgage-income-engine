from tests.unit.tax_return_test_helpers import block, field_map, tax_return_blocks


def test_extract_schedule_c_business_fields_from_each_schedule_c_page():
    fields = field_map(
        tax_return_blocks()
        + _schedule_c_page(page=2, net="50,000.00", depreciation="8,000.00", miles="1000")
        + _schedule_c_page(page=3, net="25,000.00", depreciation="4,000.00", miles="0")
    )

    assert fields["schedule_c_business_1_net_profit"].value == 50000.0
    assert fields["schedule_c_business_1_depreciation"].value == 8000.0
    assert fields["schedule_c_business_1_business_miles"].value == 1000.0
    assert fields["schedule_c_business_2_net_profit"].value == 25000.0
    assert fields["schedule_c_business_2_depreciation"].value == 4000.0


def test_extract_schedule_c_addback_source_boxes_use_values():
    fields = field_map(tax_return_blocks() + _schedule_c_page(page=2, net="50,000.00"))

    assert fields["schedule_c_business_1_business_use_of_home"].value == 3000.0
    assert fields["schedule_c_business_1_business_use_of_home"].bounding_box.x1 == 500.0


def _schedule_c_page(page: int, net: str, depreciation: str = "8,000.00", miles: str = "0"):
    return [
        block("Schedule", 50, 50, 110, 62, page=page),
        block("C", 114, 50, 124, 62, page=page),
        block("Profit", 128, 50, 166, 62, page=page),
        block("or", 170, 50, 184, 62, page=page),
        block("Loss", 188, 50, 220, 62, page=page),
        block("From", 224, 50, 256, 62, page=page),
        block("Business", 260, 50, 320, 62, page=page),
        block("6", 50, 120, 58, 132, page=page),
        block("Other", 72, 120, 110, 132, page=page),
        block("income", 114, 120, 160, 132, page=page),
        block("5,000.00", 500, 120, 556, 132, page=page),
        block("12", 50, 160, 66, 172, page=page),
        block("Depletion", 72, 160, 132, 172, page=page),
        block("500.00", 500, 160, 548, 172, page=page),
        block("13", 50, 180, 66, 192, page=page),
        block("Depreciation", 72, 180, 150, 192, page=page),
        block(depreciation, 500, 180, 556, 192, page=page),
        block("24b", 50, 220, 74, 232, page=page),
        block("Meals", 72, 220, 110, 232, page=page),
        block("2,000.00", 500, 220, 556, 232, page=page),
        block("27a", 50, 260, 74, 272, page=page),
        block("Other", 72, 260, 110, 272, page=page),
        block("expenses", 114, 260, 170, 272, page=page),
        block("700.00", 500, 260, 548, 272, page=page),
        block("30", 50, 300, 66, 312, page=page),
        block("Business", 72, 300, 130, 312, page=page),
        block("use", 134, 300, 158, 312, page=page),
        block("of", 162, 300, 176, 312, page=page),
        block("home", 180, 300, 214, 312, page=page),
        block("3,000.00", 500, 300, 556, 312, page=page),
        block("31", 50, 340, 66, 352, page=page),
        block("Net", 72, 340, 96, 352, page=page),
        block("profit", 100, 340, 136, 352, page=page),
        block(net, 500, 340, 570, 352, page=page),
        block("44a", 50, 420, 74, 432, page=page),
        block("Business", 72, 420, 130, 432, page=page),
        block("miles", 134, 420, 170, 432, page=page),
        block(miles, 500, 420, 540, 432, page=page),
    ]
