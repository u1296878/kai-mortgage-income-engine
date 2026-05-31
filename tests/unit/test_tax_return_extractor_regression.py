from tests.unit.tax_return_test_helpers import block, field_map


def federal_1040_blocks(
    page=1,
    wages="94,380.00",
    total_income="94,380.00",
    agi="87,638.00",
    include_state_name_in_address=False,
):
    address = [block("6370 Hawaii Kai Drive", 50, 110, 220, 122, page=page)] if include_state_name_in_address else []
    return address + [
        block("Form", 50, 50, 80, 62, page=page),
        block("1040", 84, 50, 116, 62, page=page),
        block("U.S.", 120, 50, 145, 62, page=page),
        block("Individual", 150, 50, 210, 62, page=page),
        block("Income", 214, 50, 260, 62, page=page),
        block("Tax", 264, 50, 288, 62, page=page),
        block("Return", 292, 50, 338, 62, page=page),
        block("2023", 450, 50, 482, 62, page=page),
        block("Filing", 50, 80, 90, 92, page=page),
        block("Status:", 94, 80, 140, 92, page=page),
        block("Head", 144, 80, 176, 92, page=page),
        block("of", 180, 80, 194, 92, page=page),
        block("household", 198, 80, 264, 92, page=page),
        block("1a", 50, 140, 66, 152, page=page),
        block("Total", 72, 140, 106, 152, page=page),
        block("amount", 110, 140, 160, 152, page=page),
        block("from", 164, 140, 194, 152, page=page),
        block("Form(s)", 198, 140, 246, 152, page=page),
        block("W-2,", 250, 140, 282, 152, page=page),
        block("box", 286, 140, 310, 152, page=page),
        block("1", 314, 140, 320, 152, page=page),
        block(wages, 500, 140, 566, 152, page=page),
        block("9", 50, 180, 58, 192, page=page),
        block("Total", 72, 180, 106, 192, page=page),
        block("income", 110, 180, 156, 192, page=page),
        block(total_income, 500, 180, 566, 192, page=page),
        block("11", 50, 220, 66, 232, page=page),
        block("Adjusted", 72, 220, 130, 232, page=page),
        block("gross", 134, 220, 174, 232, page=page),
        block("income", 178, 220, 224, 232, page=page),
        block(agi, 500, 220, 566, 232, page=page),
    ]


def state_return_noise_blocks(page=2, amount="8,919.00"):
    return [
        block("STATE", 50, 50, 90, 62, page=page),
        block("RETURN", 94, 50, 144, 62, page=page),
        block("1a", 50, 140, 66, 152, page=page),
        block("Wages", 72, 140, 108, 152, page=page),
        block(amount, 500, 140, 556, 152, page=page),
        block("9", 50, 180, 58, 192, page=page),
        block("Total", 72, 180, 106, 192, page=page),
        block("income", 110, 180, 156, 192, page=page),
        block(amount, 500, 180, 556, 192, page=page),
        block("11", 50, 220, 66, 232, page=page),
        block("Adjusted", 72, 220, 130, 232, page=page),
        block("gross", 134, 220, 174, 232, page=page),
        block("income", 178, 220, 224, 232, page=page),
        block(amount, 500, 220, 556, 232, page=page),
    ]


def test_federal_form_1040_with_state_name_in_address_extracts_correct_values():
    fields = field_map(federal_1040_blocks(include_state_name_in_address=True))

    assert fields["wages"].value == 94380.0
    assert fields["agi"].value == 87638.0


def test_attached_state_pages_are_ignored_for_federal_field_extraction():
    blocks = state_return_noise_blocks(page=1) + federal_1040_blocks(page=3)
    fields = field_map(blocks)

    assert fields["wages"].value == 94380.0
    assert fields["total_income"].value == 94380.0
    assert fields["agi"].value == 87638.0
    assert fields["tax_year"].value == 2023.0
    assert fields["filing_status"].raw_text == "head of household"


def test_schedule_c_net_profit_is_extracted_only_from_schedule_c_line_31():
    blocks = federal_1040_blocks()
    blocks += [
        block("31", 50, 340, 66, 352, page=2),
        block("Net", 72, 340, 96, 352, page=2),
        block("profit", 100, 340, 136, 352, page=2),
        block("29.", 160, 340, 176, 352, page=2),
        block("Schedule", 50, 300, 110, 312, page=4),
        block("C", 114, 300, 124, 312, page=4),
        block("Profit", 128, 300, 166, 312, page=4),
        block("or", 170, 300, 184, 312, page=4),
        block("Loss", 188, 300, 220, 312, page=4),
        block("From", 224, 300, 256, 312, page=4),
        block("Business", 260, 300, 320, 312, page=4),
        block("31", 50, 340, 66, 352, page=4),
        block("Net", 72, 340, 96, 352, page=4),
        block("profit", 100, 340, 136, 352, page=4),
        block("94,380.00", 500, 340, 566, 352, page=4),
    ]
    fields = field_map(blocks)

    assert fields["schedule_c_net"].value == 94380.0


def test_unrelated_numeric_text_is_not_used_when_line_anchor_value_exists():
    blocks = federal_1040_blocks(wages="94,380.00")
    blocks += [
        block("8,919.", 180, 170, 220, 182, page=1),
        block("29.", 240, 170, 260, 182, page=1),
    ]
    fields = field_map(blocks)

    assert fields["wages"].value == 94380.0
