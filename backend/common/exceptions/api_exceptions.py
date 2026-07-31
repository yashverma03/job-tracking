class ApiError(Exception):
    """Single error type for API-facing failures raised from service layers."""

    def __init__(self, message: str, status_code: int, details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
