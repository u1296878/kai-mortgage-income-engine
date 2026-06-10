class DocumentNotFound(Exception):
    pass


class UnsupportedDocumentType(Exception):
    pass


class ExtractionFailed(Exception):
    pass


class PageOcrTimeout(Exception):
    pass


class JobAlreadyProcessed(Exception):
    pass


class CaseNotFound(Exception):
    pass


class JobNotFound(Exception):
    pass


class ResultNotFound(Exception):
    pass


class Unauthorized(Exception):
    pass


class IncomeStreamNotFound(Exception):
    pass


class InvalidIncomeStreamAssignment(Exception):
    pass


class BorrowerNotFound(Exception):
    pass


class InvalidBorrowerAssignment(Exception):
    pass


class InvalidEmploymentInput(Exception):
    pass


class EmploymentCalculationNotFound(Exception):
    pass


class InvalidRentalInput(Exception):
    pass


class RentalCalculationNotFound(Exception):
    pass


class InvalidNonTaxableInput(Exception):
    pass


class NonTaxableCalculationNotFound(Exception):
    pass


class InvalidSelfEmploymentInput(Exception):
    pass


class SelfEmploymentCalculationNotFound(Exception):
    pass
