from __future__ import annotations


class BenchmarkError(Exception):
    def __init__(self, code: str, message: str, details: object | None = None, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
