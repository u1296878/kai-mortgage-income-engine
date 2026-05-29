from enum import Enum


class IncomeStreamType(str, Enum):
    employment = "employment"
    rental = "rental"
    self_employment = "self_employment"
    bank_statement = "bank_statement"
    other = "other"
