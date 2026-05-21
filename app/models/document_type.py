from enum import Enum


class DocumentType(str, Enum):
    pay_stub = "pay_stub"
    w2 = "w2"
    tax_return = "tax_return"
    bank_statement = "bank_statement"
    other = "other"
