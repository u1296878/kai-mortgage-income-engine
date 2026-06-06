class DocumentNotFound(Exception):
    pass


class UnsupportedDocumentType(Exception):
    pass


class ExtractionFailed(Exception):
    pass


class JobAlreadyProcessed(Exception):
    pass


class CaseNotFound(Exception):
    pass


class JobNotFound(Exception):
    pass


class ResultNotFound(Exception):
    pass


class UserAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class AccountDeactivated(Exception):
    pass


class Unauthorized(Exception):
    pass


class InvalidCaseRequest(Exception):
    pass


class IncomeStreamNotFound(Exception):
    pass


class InvalidIncomeStreamAssignment(Exception):
    pass


class BorrowerNotFound(Exception):
    pass


class InvalidBorrowerAssignment(Exception):
    pass


class UserNotFound(Exception):
    pass


class InvalidEmploymentInput(Exception):
    pass


class EmploymentCalculationNotFound(Exception):
    pass
