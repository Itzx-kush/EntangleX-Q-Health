from fastapi import APIRouter,Depends
from app.quantum.schemas import QuantumDiagnosticRequest,QuantumDiagnosticRun,QuantumDiagnosticRunList,QuantumRuntimeStatus
from app.quantum.service import QuantumRuntimeService
router=APIRouter(prefix='/api/quantum/runtime',tags=['quantum-runtime']);_service=None
def get_quantum_service():
 global _service
 if _service is None:_service=QuantumRuntimeService()
 return _service
@router.get('/status',response_model=QuantumRuntimeStatus)
def status(service=Depends(get_quantum_service)):return service.status()
@router.post('/diagnostics',response_model=QuantumDiagnosticRun,status_code=201)
def diagnostic(payload:QuantumDiagnosticRequest,service=Depends(get_quantum_service)):return service.run_diagnostic(payload)
@router.get('/diagnostics',response_model=QuantumDiagnosticRunList)
def list_diagnostics(service=Depends(get_quantum_service)):
 items=service.list();return{'items':items,'total':len(items)}
@router.get('/diagnostics/{run_id}',response_model=QuantumDiagnosticRun)
def get_diagnostic(run_id:str,service=Depends(get_quantum_service)):return service.get(run_id)
