class EvaluationError(Exception):
 def __init__(self,code,message,details=None,status_code=400):super().__init__(message);self.code=code;self.message=message;self.details=details;self.status_code=status_code
