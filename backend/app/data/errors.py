from __future__ import annotations

class DatasetError(Exception):
    def __init__(self, code: str, message: str, details: str | None = None, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
