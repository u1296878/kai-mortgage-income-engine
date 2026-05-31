from enum import Enum


class BorrowerRole(str, Enum):
    primary = "primary"
    co_borrower = "co_borrower"
