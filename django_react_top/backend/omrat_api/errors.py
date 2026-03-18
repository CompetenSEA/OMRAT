"""Error types for the OMRAT Django refactor backend."""


class OmratAPIError(Exception):
    """Base error for API/service boundary failures."""


class ValidationError(OmratAPIError):
    """Raised when incoming payloads fail contract requirements."""


class ImportMergeError(OmratAPIError):
    """Raised when project import operations cannot be completed."""


class TaskExecutionError(OmratAPIError):
    """Raised when a background run cannot be prepared or finalized."""
