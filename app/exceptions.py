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
