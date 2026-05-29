FIELD_PATTERNS = {
    "rental_gross_income": (
        ("3", ("rents", "received")),
        ("", ("gross", "rents")),
        ("", ("gross", "rental", "income")),
        ("", ("rental", "income")),
        ("", ("total", "rents")),
    ),
    "rental_expenses": (
        ("20", ("total", "expenses")),
        ("", ("rental", "expenses")),
        ("", ("expenses",)),
    ),
    "rental_net_income": (
        ("21", ("income", "or", "loss")),
        ("26", ("total", "rental", "real", "estate", "income", "or", "loss")),
        ("", ("net", "rental", "income")),
        ("", ("net", "income")),
        ("", ("net", "loss")),
    ),
}

ADDRESS_LABELS = (
    "property address",
    "address of property",
    "rental property",
)
