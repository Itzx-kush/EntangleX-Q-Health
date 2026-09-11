class OrchestrationError(Exception):
    def __init__(self, code: str, message: str, details=None, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
