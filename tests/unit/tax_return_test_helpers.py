from uuid import uuid4

from app.extractors.tax_return_extractor import extract_tax_return_fields


def block(text, x1, y1, x2, y2, page=1):
    return {"text": text, "page": page, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def tax_return_blocks():
    return [
        block("Form", 50, 50, 80, 62),
        block("1040", 84, 50, 116, 62),
        block("U.S.", 120, 50, 145, 62),
        block("Individual", 150, 50, 210, 62),
        block("Income", 214, 50, 260, 62),
        block("Tax", 264, 50, 288, 62),
        block("Return", 292, 50, 338, 62),
        block("2023", 450, 50, 482, 62),
        block("Filing", 50, 80, 90, 92),
        block("Status:", 94, 80, 140, 92),
        block("Single", 144, 80, 186, 92),
        block("1a", 50, 140, 66, 152),
        block("Total", 72, 140, 106, 152),
        block("amount", 110, 140, 160, 152),
        block("from", 164, 140, 194, 152),
        block("Form(s)", 198, 140, 246, 152),
        block("W-2,", 250, 140, 282, 152),
        block("box", 286, 140, 310, 152),
        block("1", 314, 140, 320, 152),
        block("85000.00", 500, 140, 556, 152),
        block("9", 50, 180, 58, 192),
        block("Total", 72, 180, 106, 192),
        block("income", 110, 180, 156, 192),
        block("90000.00", 500, 180, 556, 192),
        block("11", 50, 220, 66, 232),
        block("Adjusted", 72, 220, 130, 232),
        block("gross", 134, 220, 174, 232),
        block("income", 178, 220, 224, 232),
        block("79000.00", 500, 220, 556, 232),
    ]


def schedule_c_blocks(value="5000.00"):
    return [
        block("Schedule", 50, 300, 110, 312),
        block("C", 114, 300, 124, 312),
        block("Profit", 128, 300, 166, 312),
        block("or", 170, 300, 184, 312),
        block("Loss", 188, 300, 220, 312),
        block("From", 224, 300, 256, 312),
        block("Business", 260, 300, 320, 312),
        block("31", 50, 340, 66, 352),
        block("Net", 72, 340, 96, 352),
        block("profit", 100, 340, 136, 352),
        block("or", 140, 340, 154, 352),
        block("loss", 158, 340, 188, 352),
        block(value, 500, 340, 556, 352),
    ]


def schedule_e_blocks(
    property_a="22,480.00",
    property_b="13,500.00",
    total_gross="35,980.00",
    net="3,440.00",
    page=2,
):
    return [
        block("SCHEDULE", 50, 50, 120, 62, page=page),
        block("E", 124, 50, 132, 62, page=page),
        block("Supplemental", 136, 50, 220, 62, page=page),
        block("Income", 224, 50, 270, 62, page=page),
        block("and", 274, 50, 296, 62, page=page),
        block("Loss", 300, 50, 330, 62, page=page),
        block("1a", 50, 100, 66, 112, page=page),
        block("Physical", 72, 100, 126, 112, page=page),
        block("address", 130, 100, 180, 112, page=page),
        block("of", 184, 100, 198, 112, page=page),
        block("each", 202, 100, 232, 112, page=page),
        block("property", 236, 100, 292, 112, page=page),
        block("A", 50, 120, 58, 132, page=page),
        block("131", 72, 120, 92, 132, page=page),
        block("E", 96, 120, 104, 132, page=page),
        block("500", 108, 120, 132, 132, page=page),
        block("S", 136, 120, 144, 132, page=page),
        block("Provo", 148, 120, 184, 132, page=page),
        block("UT", 188, 120, 204, 132, page=page),
        block("84606", 208, 120, 244, 132, page=page),
        block("B", 50, 140, 58, 152, page=page),
        block("2221", 72, 140, 104, 152, page=page),
        block("Corby", 108, 140, 146, 152, page=page),
        block("Blvd", 150, 140, 180, 152, page=page),
        block("South", 184, 140, 222, 152, page=page),
        block("Bend", 226, 140, 258, 152, page=page),
        block("IN", 262, 140, 276, 152, page=page),
        block("46615", 280, 140, 316, 152, page=page),
        block("Income", 50, 200, 90, 212, page=page),
        block(":", 94, 200, 98, 212, page=page),
        block("A", 420, 200, 428, 212, page=page),
        block("B", 500, 200, 508, 212, page=page),
        block("C", 580, 200, 588, 212, page=page),
        block("3", 50, 220, 58, 232, page=page),
        block("Rents", 72, 220, 110, 232, page=page),
        block("received", 114, 220, 174, 232, page=page),
        block(property_a, 420, 220, 486, 232, page=page),
        block(property_b, 500, 220, 566, 232, page=page),
        block("23a", 50, 340, 74, 352, page=page),
        block("Total", 78, 340, 112, 352, page=page),
        block("amounts", 116, 340, 170, 352, page=page),
        block("reported", 174, 340, 232, 352, page=page),
        block("on", 236, 340, 252, 352, page=page),
        block("line", 256, 340, 284, 352, page=page),
        block("3", 288, 340, 296, 352, page=page),
        block("for", 300, 340, 320, 352, page=page),
        block("all", 324, 340, 342, 352, page=page),
        block("rental", 346, 340, 390, 352, page=page),
        block("properties", 394, 340, 466, 352, page=page),
        block(total_gross, 500, 340, 566, 352, page=page),
        block("26", 50, 400, 66, 412, page=page),
        block("Total", 72, 400, 106, 412, page=page),
        block("rental", 110, 400, 154, 412, page=page),
        block("real", 158, 400, 184, 412, page=page),
        block("estate", 188, 400, 230, 412, page=page),
        block("income", 234, 400, 280, 412, page=page),
        block("or", 284, 400, 298, 412, page=page),
        block("loss", 302, 400, 332, 412, page=page),
        block("26", 500, 440, 516, 452, page=page),
        block(net, 540, 440, 606, 452, page=page),
    ]


def field_map(blocks):
    return {field.field: field for field in extract_tax_return_fields(blocks, uuid4())}
