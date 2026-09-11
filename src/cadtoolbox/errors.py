class CadToolboxError(RuntimeError):
    """Base error for cad-toolbox."""


class BackendUnavailable(CadToolboxError):
    """Raised when an optional CAD backend is not installed."""


class UnsupportedFormat(CadToolboxError):
    """Raised when an operation cannot handle the supplied format."""
