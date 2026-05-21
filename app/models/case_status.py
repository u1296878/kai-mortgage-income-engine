from enum import Enum


class CaseStatus(str, Enum):
    open = "open"
    in_review = "in_review"
    complete = "complete"
