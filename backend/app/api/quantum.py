from fastapi import APIRouter,Depends
from app.quantum.schemas import QuantumDiagnosticRequest,QuantumDiagnosticRun,QuantumDiagnosticRunList,QuantumRuntimeStatus
from app.quantum.service import QuantumRuntimeService
router=APIRouter(prefix='/api/quantum/runtime',tags=['quantum-runtime']);_service=None
def get_quantum_service():
 global _service
 if _service is None:_service=QuantumRuntimeService()
 return _service
@router.get('/status',response_model=QuantumRuntimeStatus)
def status(s=Depends(get_quantum_service)):return s.status()
@router.post('/diagnostics',response_model=QuantumDiagnosticRun,status_code=201)
def diagnostic(p:QuantumDiagnosticRequest,s=Depends(get_quantum_service)):return s.run_diagnostic(p)
@router.get('/diagnostics',response_model=QuantumDiagnosticRunList)
def runs(s=Depends(get_quantum_service)):
 x=s.list();return{'items':x,'total':len(x)}
@router.get('/diagnostics/{run_id}',response_model=QuantumDiagnosticRun)
def get_run(run_id:str,s=Depends(get_quantum_service)):return s.get(run_id)
