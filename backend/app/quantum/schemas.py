from datetime import datetime
from typing import Literal
from pydantic import BaseModel,Field
class QuantumDiagnosticRequest(BaseModel):
 backend:Literal['aer_simulator','ibm_quantum']='aer_simulator';qubits:int=Field(default=4,ge=1,le=8);shots:int=Field(default=1024,ge=1,le=8192);seed:int=42
class QuantumRuntimeStatus(BaseModel):
 simulator_available:bool;qiskit_available:bool;ibm_runtime_available:bool;ibm_token_configured:bool;real_quantum_enabled:bool;provider_ready:bool;default_backend:str;default_qubits:int;max_qubits:int;max_shots:int
class QuantumDiagnosticRun(BaseModel):
 id:str;backend:str;execution_mode:str;qubits:int;shots:int;seed:int;circuit_name:str;circuit_depth:int;circuit_size:int;operation_counts:dict[str,int];measurement_counts:dict[str,int];execution_duration_seconds:float;artifact_path:str;created_at:datetime
class QuantumDiagnosticRunList(BaseModel):items:list[QuantumDiagnosticRun];total:int
